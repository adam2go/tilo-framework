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
import type { BlockOverrides, BlockProps, TiloAction } from "./block-types";
import type { SurfaceBlock, SurfaceBlockType, SurfaceSpec } from "./surface";
import { NOOP_ACTION_ID } from "./surface";

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
   * the default renderer. Unspecified types use the built-in defaults.
   *
   * @example
   * <TiloRenderer surface={spec} components={{ decision: MyDecision }} />
   */
  components?: BlockOverrides;
  /**
   * Called whenever the user fires a block-level action (decision, form
   * submit, editable save, artifact open, link click).
   *
   * The renderer does NOT call the backend — compose with `useTiloSurface`
   * or your own state management per the AIP design: "frontend renders
   * intent, backend owns action semantics."
   */
  onAction?: (event: TiloAction) => void | Promise<void>;
  /**
   * Optional wrapper rendered around each block. Useful for spacing or
   * dividers without overriding every block component individually.
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
    const Cmp = userOverride as (props: BlockProps<SurfaceBlockType>) => JSX.Element;
    return <Cmp block={block as never} surface={surface} fire={fire} />;
  }
  const Default = DEFAULTS[block.type];
  if (!Default) {
    // Graceful fallback for unknown block types (block_compat: graceful).
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
    if (!action || !onAction) return;
    return onAction({ action, block, surface, payload: optionPayload });
  };
}
