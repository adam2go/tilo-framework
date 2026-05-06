# Rich Surface Escalation

Rich surface should remain explicit escalation, not default UI.

Use `RichSurfaceLink` / `RichSurfaceTarget` payloads in conversation turns to represent intentional open actions (for example: Open Full Review).

Standard target payload:

```json
{
  "surface": "ContractReviewArtifact",
  "title": "Open Full Review",
  "target": {
    "type": "drawer",
    "artifactId": "...",
    "title": "Contract Review",
    "source": "user_action"
  },
  "channel": "web",
  "metadata": {}
}
```

Guidelines:
- Mini surfaces stay inline in the conversation.
- `Open Full Review` opens a drawer first.
- `Open Artifact` can navigate to `/artifacts/{id}`.
- Telegram should use a URL/WebApp button when a drawer is not available.
- Opening a rich surface should append a `rich_surface_link` conversation turn.
