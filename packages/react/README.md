# @adam2go/tilo-react

React renderer SDK for [Tilo](https://github.com/adam2go/tilo-framework) — render agent-authored surfaces, artifact blocks, and the two-way AIP action loop in any React app.

```bash
npm install @adam2go/tilo-react recharts lucide-react
# or
pnpm add @adam2go/tilo-react recharts lucide-react
```

## Quick start

### Render a surface spec

```tsx
import { TiloRenderer, createTiloClient, useTiloSurface } from "@adam2go/tilo-react";

const client = createTiloClient({ baseUrl: "http://localhost:8000" });

function MyApp({ runId }: { runId: string }) {
  const { turns, loading } = useTiloSurface({ client, runId });

  return (
    <div>
      {turns.map((turn) => (
        <TiloRenderer
          key={turn.id}
          surface={turn.spec}
          onAction={async (event) => {
            await client.executeSurfaceAction({
              surface: turn.spec,
              actionId: event.action.id,
              workspaceId: "my-workspace-id",
              runId,
            });
          }}
        />
      ))}
    </div>
  );
}
```

### Render an artifact block

```tsx
import { renderArtifactBlock } from "@adam2go/tilo-react";

// Works with any AIP v1 block (chart, diff, code, timeline, kanban, …)
const block = {
  id: "chart-1",
  type: "chart",
  props: {
    chart_type: "bar",
    labels: ["Q1", "Q2", "Q3", "Q4"],
    datasets: [{ label: "Revenue", data: [120, 180, 150, 220] }],
  },
};

<div>{renderArtifactBlock(block)}</div>
```

### Override a block renderer

```tsx
import { TiloRenderer } from "@adam2go/tilo-react";
import type { BlockProps } from "@adam2go/tilo-react";

function MyDecision({ block, fire }: BlockProps<"decision">) {
  return (
    <div>
      {block.data.options.map((opt) => (
        <button key={opt.id} onClick={() => fire(opt.action_id)}>
          {opt.label}
        </button>
      ))}
    </div>
  );
}

<TiloRenderer surface={spec} components={{ decision: MyDecision }} />
```

## Block types

### Surface blocks (`TiloRenderer`)

| Type | Description |
|---|---|
| `heading` | Section header with severity badge |
| `text` | Plain text paragraph |
| `evidence` | Quoted excerpt with source reference |
| `comparison` | Side-by-side or table comparison |
| `decision` | Choice buttons (single / multi) |
| `form` | Input fields + submit |
| `progress` | Steps, percent bar, or status |
| `list` | Ordered / unordered list with severity |
| `link` | Link with external indicator |
| `editable` | Editable textarea with save action |
| `artifact_link` | Clickable card that opens a rich artifact |
| `fallback` | Graceful fallback for unknown types |

### Artifact blocks (`renderArtifactBlock`)

These match the block types produced by `tilo.generate()` and the
zero-setup Python viewer (`tilo.view`), so React rendering looks identical.

| Type | Description |
|---|---|
| `heading` | Section header with severity color |
| `markdown` | Plain text / markdown |
| `card` | Titled card with severity |
| `metric` | Single KPI value (label + value + delta) |
| `table` | Data table with header row |
| `list` | Bullet list with severity |
| `code` | Monospace code block with language label |
| `chart` | Bar, line, pie, or radar chart via Recharts |
| `diff` | Unified diff (color-coded) or before/after |
| `timeline` | Vertical dot-and-line timeline |
| `kanban` | Horizontal column board |
| `progress` | Progress bar |
| `checklist` | Interactive checkboxes |
| `rating` | Interactive star rating |
| `button_group` | Action buttons (primary / default) |
| `form` | Input fields + submit |
| `confirmation` | Human-approval gate with risk badge |
| `tool_preview` | Tool call result with status badge |
| `memory_card` | Memory candidate with confidence % |
| + custom | Unknown types fall back gracefully |

## Tailwind CSS

`@adam2go/tilo-react` components use Tailwind CSS utility classes. Add the package to your `tailwind.config.js` content scan:

```js
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@adam2go/tilo-react/dist/**/*.{js,mjs}",
  ],
};
```

## Peer dependencies

| Package | Version |
|---|---|
| `react` | ≥ 18 |
| `react-dom` | ≥ 18 |
| `recharts` | ≥ 2 (for chart blocks) |
| `lucide-react` | ≥ 0.400 (for icons) |

## API

### `<TiloRenderer>`

| Prop | Type | Description |
|---|---|---|
| `surface` | `SurfaceSpec` | The surface spec to render |
| `onAction` | `(event: TiloAction) => void \| Promise<void>` | Action callback |
| `components` | `BlockOverrides` | Per-type visual overrides |
| `blockWrapper` | `(block, child) => ReactNode` | Wrapper around each block |

### `createTiloClient(options)`

Returns a `TiloClient` with:
- `fetchRunSurfaceTurns(runId)` → `SurfaceTurn[]`
- `fetchSessionSurfaceTurns(sessionId, limit?)` → `SurfaceTurn[]`
- `executeSurfaceAction(params)` → `SurfaceActionResult`

### `useTiloSurface(options)`

| Option | Type | Description |
|---|---|---|
| `client` | `TiloClient` | Client from `createTiloClient` |
| `runId` | `string \| null` | Fetch turns for a specific run |
| `sessionId` | `string \| null` | Fetch turns for a conversation |
| `pollingMs` | `number` | Auto-refresh interval (0 = off) |
| `enabled` | `boolean` | Enable/disable fetching |

Returns `{ turns, loading, error, refresh }`.

## License

MIT — part of [Tilo Framework](https://github.com/adam2go/tilo-framework)
