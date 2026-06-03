"use client";

import type { ReactNode } from "react";
import {
  ArtifactLinkBlock,
  ComparisonBlock,
  DecisionBlock,
  EditableBlock,
  EvidenceBlock,
  FallbackBlock,
  FormBlock,
  HeadingBlock,
  LinkBlock,
  ListBlock,
  ProgressBlock,
  TextBlock,
} from "./blocks";
import type { BlockOverrides, BlockProps, TiloAction } from "./types";
import type { SurfaceBlock, SurfaceBlockType, SurfaceSpec } from "../../lib/surface";
import { NOOP_ACTION_ID } from "../../lib/surface";

const DEFAULTS: { [K in SurfaceBlockType]: (props: BlockProps<K>) => JSX.Element } = {
  heading: HeadingBlock,
  text: TextBlock,
  evidence: EvidenceBlock,
  comparison: ComparisonBlock,
  decision: DecisionBlock,
  form: FormBlock,
  progress: ProgressBlock,
  list: ListBlock,
  link: LinkBlock,
  editable: EditableBlock,
  artifact_link: ArtifactLinkBlock,
  fallback: FallbackBlock,
} as const;

export interface TiloRendererProps {
  surface: SurfaceSpec;
  /**
   * Per-block visual override. Pass any subset of block types to replace
   * the default visual. Unspecified types render with the built-in defaults.
   *
   * Example:
   *   <TiloRenderer surface={...} components={{ decision: MyDecision }} />
   */
  components?: BlockOverrides;
  /**
   * Called whenever the user fires a block-level action (decision option,
   * form submit, editable submit, artifact open, link click). The action's
   * `id` is the same as on `block.actions[].id`.
   *
   * The component does NOT itself talk to the backend — composition with
   * `useTiloAction` (or your own state mgmt) is the renderer's
   * responsibility, exactly per ADR ("frontend renders intent, backend owns
   * action semantics").
   */
  onAction?: (event: TiloAction) => void | Promise<void>;
  /**
   * Optional wrapper around each block. Useful for spacing/dividers without
   * having to override every block component. The default wrapper is
   * `<div className="surface-block">`.
   */
  blockWrapper?: (block: SurfaceBlock, child: ReactNode) => ReactNode;
}

const defaultWrapper = (_block: SurfaceBlock, child: ReactNode): ReactNode => (
  <div className="surface-block">{child}</div>
);

export function TiloRenderer({
  surface,
  components,
  onAction,
  blockWrapper = defaultWrapper,
}: TiloRendererProps): JSX.Element {
  return (
    <article
      className="tilo-surface"
      data-intent={surface.intent}
      data-budget={surface.budget_hint}
      data-surface-id={surface.surface_id}
    >
      {surface.blocks.map((block) => {
        const child = renderBlock(surface, block, components, onAction);
        return (
          <div key={block.id} data-block-id={block.id} data-block-type={block.type}>
            {blockWrapper(block, child)}
          </div>
        );
      })}
    </article>
  );
}

function renderBlock(
  surface: SurfaceSpec,
  block: SurfaceBlock,
  components: BlockOverrides | undefined,
  onAction: TiloRendererProps["onAction"],
): JSX.Element {
  const fire = makeFire(surface, block, onAction);
  const userOverride = components?.[block.type];
  if (userOverride) {
    // We can't statically prove the user-supplied component matches the
    // discriminant payload at compile time once it's generic, so cast at
    // the boundary and trust the default shape is preserved.
    const Cmp = userOverride as (props: BlockProps<SurfaceBlockType>) => JSX.Element;
    return <Cmp block={block as never} surface={surface} fire={fire} />;
  }
  // Graceful fallback: if the runtime emitted a block type we don't
  // recognise, render its fallback_text instead of crashing the page.
  // This implements `block_compat: graceful` (see SURFACE_PROTOCOL §6.2).
  const Default = DEFAULTS[block.type];
  if (!Default) {
    return <FallbackBlock block={{ ...block, type: "fallback", data: { content: block.fallback_text } } as never} surface={surface} fire={fire} />;
  }
  return <Default block={block as never} surface={surface} fire={fire} />;
}

function makeFire(
  surface: SurfaceSpec,
  block: SurfaceBlock,
  onAction: TiloRendererProps["onAction"],
): BlockProps<SurfaceBlockType>["fire"] {
  return (actionId, optionPayload) => {
    if (actionId === NOOP_ACTION_ID) return;
    const action = (block.actions || []).find((a) => a.id === actionId);
    if (!action) return;
    if (!onAction) return;
    return onAction({
      action,
      block,
      surface,
      payload: optionPayload,
    });
  };
}
