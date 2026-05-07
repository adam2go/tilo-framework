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
http://localhost:3000/demo/telegram
```

4. Run the sample contract review.

5. Click `Approve Revision`.

6. Send the default follow-up suggestion so the Memory Candidate stage is visible.

7. Capture the browser viewport and save a real image under:

```text
docs/assets/telegram-demo.png
```

Only commit the screenshot if it reflects the current UI and was captured from this flow.
