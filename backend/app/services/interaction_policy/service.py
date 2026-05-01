from pathlib import Path

import yaml

from app.services.apps.loader import get_app_loader
from app.services.interaction_policy.schemas import (
    InteractionContext,
    InteractionDecision,
    InteractionDecisionType,
    InteractionPolicy,
    InteractionRule,
)


class InteractionPolicyService:
    def load_for_app(self, app_id: str) -> InteractionPolicy:
        policy_path = get_app_loader().load_policy_path(app_id)
        return self.load_file(policy_path)

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

    def _with_budget(self, policy: InteractionPolicy, context: InteractionContext, rule: InteractionRule) -> InteractionDecision:
        if rule.decision == InteractionDecisionType.mini_surface:
            if context.mini_surfaces_used >= policy.budget.max_mini_surfaces_per_run:
                return InteractionDecision(decision=InteractionDecisionType.no_ui, reason="mini_surface_budget_exceeded", rule_id=rule.id)
            if rule.surface == "MiniMemoryCard" and context.memory_cards_used >= policy.budget.max_memory_cards_per_run:
                return InteractionDecision(decision=InteractionDecisionType.no_ui, reason="memory_card_budget_exceeded", rule_id=rule.id)
            if context.confirmations_used >= policy.budget.max_confirmations_per_run and rule.surface in {"MiniIssueCard", "MiniApprovalCard", "MiniToolPreview"}:
                return InteractionDecision(decision=InteractionDecisionType.ask_text, reason="confirmation_budget_exceeded", rule_id=rule.id)
        return InteractionDecision(decision=rule.decision, surface=rule.surface, reason=rule.reason, rule_id=rule.id)
