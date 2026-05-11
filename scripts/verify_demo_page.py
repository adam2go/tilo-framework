#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value for key, value in attrs}
        if tag == "script" and attr.get("src"):
            self.scripts.append(attr["src"] or "")
        if tag == "link" and attr.get("rel") == "stylesheet" and attr.get("href"):
            self.stylesheets.append(attr["href"] or "")


def fetch(url: str, *, timeout: int = 8) -> tuple[int, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "tilo-demo-verifier/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, response.geturl(), body


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify(frontend_url: str) -> None:
    base = frontend_url.rstrip("/")
    status, final_url, html = fetch(f"{base}/demo")
    assert_true(status == 200, f"/demo returned HTTP {status}")
    assert_true("/demo" in final_url, f"/demo resolved to unexpected URL: {final_url}")
    assert_true("Tilo" in html, "/demo page is missing the Tilo product signal")
    assert_true("Review this AI service agreement" in html, "/demo page is missing the contract-review goal")
    assert_true("raw JSON" not in html, "/demo should not expose raw JSON by default")
    assert_true("hidden reasoning" not in html.lower(), "/demo should not expose hidden reasoning")

    parser = AssetParser()
    parser.feed(html)
    assets = [*parser.stylesheets[:2], *parser.scripts[:4]]
    assert_true(bool(assets), "/demo did not include Next.js assets")
    for asset in assets:
        asset_url = urllib.parse.urljoin(base, asset)
        asset_status, _, _ = fetch(asset_url)
        assert_true(asset_status == 200, f"asset failed: {asset_url} returned HTTP {asset_status}")

    legacy_status, legacy_final_url, legacy_html = fetch(f"{base}/demo/telegram")
    assert_true(legacy_status == 200, f"/demo/telegram returned HTTP {legacy_status}")
    assert_true("/demo" in legacy_final_url, f"/demo/telegram did not resolve to /demo: {legacy_final_url}")
    assert_true("TelegramDemoPage" not in legacy_html, "/demo/telegram appears to load legacy demo code")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Tilo /demo page contract.")
    parser.add_argument("--frontend-url", default="http://localhost:3000")
    args = parser.parse_args()
    try:
        verify(args.frontend_url)
    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(f"demo page verification failed: {exc}", file=sys.stderr)
        return 1
    print("demo page contract ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
