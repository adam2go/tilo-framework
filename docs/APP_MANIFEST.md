# App Manifest

Tilo apps are declared with an `app.yaml` manifest. The manifest makes an agent app inspectable and reusable instead of embedding app behavior only in React components or route handlers.

Current example:

```text
examples/apps/contract-review-agent/app.yaml
```

Core fields:

- `id`, `version`, `name`, `description`: app identity.
- `entry`: the default conversation entry point.
- `runtime`: model fallback, memory behavior, and policy file.
- `surfaces`: mini and rich surfaces the app may render.
- `sample_inputs`: fixtures that demos or tests can load.
- `tools`: optional app tools.
- `channels`: supported channels such as `web` and `telegram`.

Apps are loaded by `AgentAppLoader` and exposed through:

```text
GET /api/apps
GET /api/apps/{app_id}
```

Manifests must not contain secrets. Model keys and channel tokens stay in environment configuration.
