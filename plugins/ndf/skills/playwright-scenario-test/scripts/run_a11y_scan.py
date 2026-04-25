"""axe-core で a11y 違反を検出する。

docs/checklists/checklist-common.md の C1 (a11y) を機械的に走査する。
WCAG 2.0 / 2.1 / 2.2 タグを指定。

Usage:
    python run_a11y_scan.py --url https://example.com
    python run_a11y_scan.py --url-list urls.txt --output a11y-report.json
    python run_a11y_scan.py --url https://example.com --storage-state alice.json --tags wcag22aa
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


DEFAULT_TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]


def scan(
    url: str,
    *,
    storage_state: str | None = None,
    tags: list[str] | None = None,
    timeout_ms: int = 30_000,
    headless: bool = True,
) -> dict[str, Any]:
    """1 URL をスキャンして axe の結果 dict を返す。"""
    try:
        from axe_playwright_python.sync_playwright import Axe
    except ImportError as exc:
        raise SystemExit(
            "axe-playwright-python が未インストール。\n"
            "  uv sync --extra a11y\n"
            "または\n"
            "  uv add axe-playwright-python"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_kwargs: dict = {"ignore_https_errors": True}
        if storage_state:
            ctx_kwargs["storage_state"] = storage_state
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception as exc:
            return {"url": url, "error": str(exc)}

        axe = Axe()
        # axe-playwright-python 0.1.x は run(page) のみ。タグ絞り込みは
        # 内部 axe-core の options で実施するため context options を渡す。
        try:
            results = axe.run(
                page,
                options={"runOnly": {"type": "tag", "values": tags or DEFAULT_TAGS}},
            )
        except TypeError:
            # 古いバージョンは options 非対応
            results = axe.run(page)

        violations: list[dict[str, Any]] = []
        for v in results.response.get("violations", []):
            violations.append({
                "id": v.get("id"),
                "impact": v.get("impact"),
                "tags": v.get("tags", []),
                "help": v.get("help"),
                "helpUrl": v.get("helpUrl"),
                "nodes": [
                    {
                        "html": n.get("html", "")[:200],
                        "target": n.get("target", []),
                        "failureSummary": n.get("failureSummary", "")[:300],
                    }
                    for n in v.get("nodes", [])
                ],
            })

        out = {
            "url": url,
            "violations_count": len(violations),
            "violations": violations,
            "passes_count": len(results.response.get("passes", [])),
            "incomplete_count": len(results.response.get("incomplete", [])),
            "tags": tags or DEFAULT_TAGS,
        }
        browser.close()
        return out


def main() -> int:
    parser = argparse.ArgumentParser(description="axe-core で a11y 違反を検出")
    parser.add_argument("--url", help="検査対象 URL")
    parser.add_argument("--url-list", type=Path, help="URL を 1 行 1 件で書いたファイル")
    parser.add_argument("--storage-state", default=None, help="ログイン済 storage_state.json")
    parser.add_argument("--tags", nargs="+", default=DEFAULT_TAGS,
                        help=f"axe-core タグ (default: {DEFAULT_TAGS})")
    parser.add_argument("--output", type=Path, default=None,
                        help="JSON 出力先 (省略時 stdout)")
    parser.add_argument("--fail-on-violations", action="store_true",
                        help="violations_count > 0 で exit 1")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    if not args.url and not args.url_list:
        parser.error("--url または --url-list が必要です")

    urls = (
        [line.strip() for line in args.url_list.read_text().splitlines() if line.strip()]
        if args.url_list else [args.url]
    )

    results = [
        scan(u, storage_state=args.storage_state, tags=args.tags,
             headless=not args.headed)
        for u in urls
    ]

    text = json.dumps(results, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"OK: a11y scan → {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text + "\n")

    total_violations = sum(r.get("violations_count", 0) for r in results)
    print(f"violations: {total_violations}", file=sys.stderr)
    return 1 if args.fail_on_violations and total_violations > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
