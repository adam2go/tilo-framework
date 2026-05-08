# Demo Screenshot Guidance

Do not commit fake screenshots.

If the README or docs need screenshots, capture them from the real local demo after it is running.

## Capture Flow

1. Start Tilo:

```bash
cp .env.example .env
docker compose up --build
```

2. Verify the demo:

```bash
bash scripts/verify_local_demo.sh
```

3. Open:

```text
http://localhost:3000/demo
```

4. Run the sample contract review.

5. Click `Approve revision`.

6. Use `Remember` or `Not now` so the memory prompt state is visible.

7. Capture the browser viewport and save a real image under:

```text
docs/assets/minimal-demo.png
```

Only commit the screenshot if it reflects the current UI and was captured from this flow.

The legacy `/demo/telegram` route may still be captured for internal docs, but it is no longer the primary public demo.
