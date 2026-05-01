# Mini Surface Registry

Mini surfaces are lightweight UI cards that can appear inside a conversation when chat alone is not enough.

Round 1 registry location:

```text
frontend/components/mini-surfaces/registry.ts
```

Initial surfaces:

- `MiniIssueCard`
- `MiniApprovalCard`
- `MiniRevisionPreview`
- `MiniMemoryCard`
- `MiniToolPreview`
- `MiniChoiceCard`

Each registration declares:

- component type
- display name
- supported channels
- fallback behavior
- React component

The registry prepares surfaces for channel-specific rendering. For example, web can render native React cards, while Telegram can fall back to message text plus inline buttons or a rich artifact link.

Mini surfaces should stay sparse. Tilo should render only one meaningful decision or information card at a time by default.
