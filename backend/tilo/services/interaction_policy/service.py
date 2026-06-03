"""Interaction policy service.

Phase 1: emits both `intent` (preferred) and `surface` (legacy passthrough)
on every UI decision. Validation against `app.yaml` happens at the *intent*
level when policies declare intents directly; the legacy surface-name
validation still runs for rules that only specified `surface:`.
"""

from pathlib import Path

import yaml

from tilo.schemas.surface import SurfaceIntent
from tilo.services.apps.loader import get_app_loader
from tilo.services.apps.schemas import AgentAppManifest
from tilo.services.interaction_policy.schemas import (
    InteractionContext,
    InteractionDecision,
    InteractionDecisionType,
    InteractionPolicy,
    InteractionRule,
    LEGACY_SURFACE_TO_INTENT,
)


# Intents that produce inline mini surfaces. Used for budget accounting.
_MINI_INTENTS: set[SurfaceIntent] = {
    SurfaceIntent.request_approval,
    SurfaceIntent.collect_input,
    SurfaceIntent.present_result,
    SurfaceIntent.offer_choices,
    SurfaceIntent.confirm_memory,
    SurfaceIntent.show_progress,
    SurfaceIntent.ask_clarification,
}

# Intents that produce confirmation-gated UI. Used for budget accounting.
_CONFIRMATION_INTENTS: set[SurfaceIntent] = {
    SurfaceIntent.request_approval,
}

_MEMORY_INTENTS: set[SurfaceIntent] = {
    SurfaceIntent.confirm_memory,
}


class InteractionPolicyService:
    def load_for_app(self, app_id: str) -> InteractionPolicy:
        loader = get_app_loader()
        app = loader.load_manifest(app_id)
        policy = self.load_file(loader.load_policy_path(app_id))
        self.validate_for_app(app, policy)
        return policy

    def load_file(self, path: Path) -> InteractionPolicy:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return InteractionPolicy.model_validate(data)

    def evaluate(self, policy: InteractionPolicy, context: InteractionContext) -> InteractionDecision:
        for rule in policy.rules:
            if self._matches(rule, context):
                return self._with_budget(policy, context, rule)
        return InteractionDecision(decision=InteractionDecisionType.no_ui, reason="no_policy_match")

    def evaluate_for_app(self, app_id: str, context: InteractionContext) -> InteractionDecision:
        return self.evaluate(self.load_for_app(app_id), context)

    def validate_for_app(self, app: AgentAppManifest, policy: InteractionPolicy) -> None:
        """Validate that every rule's target is declared in app.yaml.

        Validation order, per rule:
          1. If the rule used `intent:` directly and the manifest declares
             intents, the intent must be in `app.surfaces.intents`.
          2. If the rule used legacy `surface:`, the surface name must be in
             `app.surfaces.mini` or `app.surfaces.rich`.

        Apps that have not migrated their manifest still validate via the
        legacy surface check. New apps SHOULD declare `surfaces.intents`.
        """
        mini_surfaces = set(app.surfaces.mini)
        rich_surfaces = set(app.surfaces.rich)
        declared_intents = set(app.surfaces.intents) if app.surfaces.intents else None

        for rule in policy.rules:
            if rule.decision not in {InteractionDecisionType.mini_surface, InteractionDecisionType.rich_surface}:
                continue

            # Legacy form: validate against named surfaces.
            if rule.surface:
                if rule.decision == InteractionDecisionType.mini_surface and rule.surface not in mini_surfaces:
                    raise ValueError(f"Policy rule {rule.id!r} references undeclared mini surface {rule.surface!r}")
                if rule.decision == InteractionDecisionType.rich_surface and rule.surface not in rich_surfaces:
                    raise ValueError(f"Policy rule {rule.id!r} references undeclared rich surface {rule.surface!r}")
                continue

            # Modern form: validate against declared intents (if the manifest declares them).
            if rule.intent is None:
                # Should have been caught by InteractionRule validator already.
                raise ValueError(f"Policy rule {rule.id!r}: missing both intent and surface")
            if declared_intents is not None and rule.intent.value not in declared_intents:
                raise ValueError(
                    f"Policy rule {rule.id!r} references undeclared intent {rule.intent.value!r}; "
                    f"add it to {app.id}.yaml > surfaces.intents."
                )

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    def _matches(self, rule: InteractionRule, context: InteractionContext) -> bool:
        values = context.model_dump()
        values.update(context.extra)
        for key, expected in rule.when.items():
            actual = values.get(key)
            if actual is None:
                return False
            if str(actual).lower() != str(expected).lower():
                return False
        return True

    def _with_budget(
        self, policy: InteractionPolicy, context: InteractionContext, rule: InteractionRule
    ) -> InteractionDecision:
        intent = rule.intent  # always populated for UI decisions after schema normalisation
        if rule.decision == InteractionDecisionType.mini_surface:
            if context.mini_surfaces_used >= policy.budget.max_mini_surfaces_per_run:
                return InteractionDecision(
                    decision=InteractionDecisionType.no_ui,
                    reason="mini_surface_budget_exceeded",
                    rule_id=rule.id,
                )
            if intent in _MEMORY_INTENTS and context.memory_cards_used >= policy.budget.max_memory_cards_per_run:
                return InteractionDecision(
                    decision=InteractionDecisionType.no_ui,
                    reason="memory_card_budget_exceeded",
                    rule_id=rule.id,
                )
            if (
                intent in _CONFIRMATION_INTENTS
                and context.confirmations_used >= policy.budget.max_confirmations_per_run
            ):
                return InteractionDecision(
                    decision=InteractionDecisionType.ask_text,
                    reason="confirmation_budget_exceeded",
                    rule_id=rule.id,
                )

        return InteractionDecision(
            decision=rule.decision,
            intent=intent,
            surface=rule.surface,
            reason=rule.reason,
            rule_id=rule.id,
        )


__all__ = [
    "InteractionPolicyService",
    "LEGACY_SURFACE_TO_INTENT",
]
