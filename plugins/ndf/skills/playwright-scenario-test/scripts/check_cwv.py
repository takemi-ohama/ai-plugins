"""Core Web Vitals (LCP / CLS / TTFB) を Playwright で計測する。

field metric である INP は本スクリプトでは計測**しない**。代わりに「最大 Long Task
持続時間」(`longest_task_ms`) を取得する。これは INP の近似ではなく、UI 応答性の
**ラフな指標**としてのみ使う (50ms 超は応答性低下の兆候)。
正式な INP は web-vitals.js の attribution build を使うか、フィールド計測を実施。

docs/checklists/checklist-common.md の C2 (perf) を機械的に検証する。

Usage:
    python check_cwv.py --url https://example.com
    python check_cwv.py --url-list urls.txt --output cwv.json
    python check_cwv.py --url https://example.com --device "iPhone 13"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


# web.dev 公式閾値 (75 percentile 基準)
THRESHOLDS = {
    "lcp": {"good": 2500, "poor": 4000},      # ms (web.dev 公式)
    "cls": {"good": 0.1, "poor": 0.25},       # web.dev 公式
    "ttfb": {"good": 800, "poor": 1800},      # ms (web.dev 公式)
    # longest_task は INP ではない。50ms 超は応答性低下の兆候 (browser main thread block)。
    # 正式 INP の代替指標ではないことに注意。
    "longest_task": {"good": 50, "poor": 200},
}


# LCP / CLS を PerformanceObserver で取得する JS。
# 5 秒間観察してから値を返す (LCP はページ可視性が変わるまで更新され続けるため)。
_PERF_JS = r"""
() => new Promise((resolve) => {
    const result = {lcp: null, cls: 0, longest_task: 0};

    // LCP
    try {
        const lcpObs = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries.at(-1);
            if (last) result.lcp = last.startTime;
        });
        lcpObs.observe({type: 'largest-contentful-paint', buffered: true});
    } catch (e) {}

    // CLS (累積; hadRecentInput===false のみ)
    try {
        const clsObs = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (!entry.hadRecentInput) {
                    result.cls += entry.value;
                }
            }
        });
        clsObs.observe({type: 'layout-shift', buffered: true});
    } catch (e) {}

    // 最大 long task (INP の代理指標)
    try {
        const ltObs = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.duration > result.longest_task) {
                    result.longest_task = entry.duration;
                }
            }
        });
        ltObs.observe({type: 'longtask', buffered: true});
    } catch (e) {}

    // navigation timing から TTFB
    try {
        const nav = performance.getEntriesByType('navigation')[0];
        if (nav) result.ttfb = nav.responseStart - nav.requestStart;
    } catch (e) {}

    setTimeout(() => resolve(result), 5000);
});
"""


def _judge(metric: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    th = THRESHOLDS.get(metric)
    if not th:
        return "unknown"
    if value <= th["good"]:
        return "good"
    if value <= th["poor"]:
        return "needs-improvement"
    return "poor"


def measure(
    url: str,
    *,
    storage_state: str | None = None,
    device_name: str | None = None,
    timeout_ms: int = 30_000,
    headless: bool = True,
) -> dict[str, Any]:
    """1 URL を計測し CWV 値を返す。"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx_kwargs: dict[str, Any] = {"ignore_https_errors": True}
        if storage_state:
            ctx_kwargs["storage_state"] = storage_state
        if device_name:
            device = p.devices.get(device_name)
            if not device:
                browser.close()
                return {"url": url, "error": f"unknown device: {device_name}"}
            ctx_kwargs.update(device)
        context = browser.new_context(**ctx_kwargs)
        page = context.new_page()
        try:
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        except Exception as exc:
            browser.close()
            return {"url": url, "error": str(exc)}

        try:
            metrics = page.evaluate(_PERF_JS)
        except Exception as exc:
            metrics = {"error": str(exc)}

        result = {
            "url": url,
            "device": device_name or "desktop",
            "metrics": {
                "lcp_ms": metrics.get("lcp"),
                "cls": metrics.get("cls"),
                "ttfb_ms": metrics.get("ttfb"),
                "longest_task_ms": metrics.get("longest_task"),
            },
            "judgement": {
                "lcp": _judge("lcp", metrics.get("lcp")),
                "cls": _judge("cls", metrics.get("cls")),
                "ttfb": _judge("ttfb", metrics.get("ttfb")),
                "longest_task": _judge("longest_task", metrics.get("longest_task")),
            },
            "thresholds": THRESHOLDS,
        }
        browser.close()
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Core Web Vitals 計測")
    parser.add_argument("--url", help="計測 URL")
    parser.add_argument("--url-list", type=Path, help="URL を 1 行 1 件で書いたファイル")
    parser.add_argument("--storage-state", default=None)
    parser.add_argument("--device", default=None,
                        help="モバイル device 名 (例: 'iPhone 13'). 省略時は desktop")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--fail-on-poor", action="store_true",
                        help="いずれかの指標が poor なら exit 1")
    args = parser.parse_args()

    if not args.url and not args.url_list:
        parser.error("--url または --url-list が必要です")

    urls = (
        [line.strip() for line in args.url_list.read_text().splitlines() if line.strip()]
        if args.url_list else [args.url]
    )

    results = [measure(u, storage_state=args.storage_state,
                       device_name=args.device) for u in urls]

    text = json.dumps(results, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"OK: CWV → {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text + "\n")

    has_poor = any(
        v == "poor" for r in results for v in (r.get("judgement") or {}).values()
    )
    return 1 if args.fail_on_poor and has_poor else 0


if __name__ == "__main__":
    raise SystemExit(main())
