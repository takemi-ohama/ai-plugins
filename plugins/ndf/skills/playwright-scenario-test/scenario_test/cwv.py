"""runner 内蔵の Core Web Vitals 計測モジュール。

`scripts/check_cwv.py` (CLI) はこのモジュールの薄いラッパで、runner からは
`measure_page(page)` を直接呼び出して `EvidenceCollectors.cwv_metrics` に格納する。

page_role が `lp / list / dashboard` のとき runner が自動実行する
(config.cwv.auto_roles で上書き可能)。

注意:
- INP は実 user 入力ベースの指標であり Playwright で完全再現は不可能。
  `longest_task_ms` (50ms 超を 1 件以上検出) を「応答性低下の代理指標」として記録
  するが、INP の代わりにはならない。
- 計測は page.evaluate で 5 秒間 PerformanceObserver を回す ため、testcase の
  最後 (全 step 実行後) に呼ぶこと。
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page


# web.dev 公式閾値 (75 percentile 基準)
THRESHOLDS: dict[str, dict[str, float]] = {
    "lcp_ms": {"good": 2500, "poor": 4000},
    "cls": {"good": 0.1, "poor": 0.25},
    "ttfb_ms": {"good": 800, "poor": 1800},
    "longest_task_ms": {"good": 50, "poor": 200},
}

# page_role × CWV 自動実行のデフォルト対象。インタラクション主体 (form / cart) は
# 過度な負荷になるため除外し、初回表示性能が UX に直結する role に限定する。
DEFAULT_AUTO_ROLES: frozenset[str] = frozenset({"lp", "list", "dashboard", "search"})


_PERF_JS = r"""
() => new Promise((resolve) => {
    const result = {lcp: null, cls: 0, longest_task: 0, ttfb: null};

    try {
        const lcpObs = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries.at(-1);
            if (last) result.lcp = last.startTime;
        });
        lcpObs.observe({type: 'largest-contentful-paint', buffered: true});
    } catch (e) {}

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

    try {
        const nav = performance.getEntriesByType('navigation')[0];
        if (nav) result.ttfb = nav.responseStart - nav.requestStart;
    } catch (e) {}

    setTimeout(() => resolve(result), 5000);
});
"""


def measure_page(page: Page, *, observe_ms: int = 5000) -> dict[str, float]:
    """既にロード済みの Page で CWV を 5 秒観察し、metrics dict を返す。

    Returns: `{"lcp_ms": float, "cls": float, "ttfb_ms": float, "longest_task_ms": float}`
            計測失敗した metric は dict から除外される。
    """
    js = _PERF_JS.replace("5000", str(int(observe_ms)))
    try:
        raw: dict[str, Any] = page.evaluate(js)
    except Exception:
        return {}

    out: dict[str, float] = {}
    if raw.get("lcp") is not None:
        out["lcp_ms"] = float(raw["lcp"])
    if raw.get("cls") is not None:
        out["cls"] = float(raw["cls"])
    if raw.get("ttfb") is not None:
        out["ttfb_ms"] = float(raw["ttfb"])
    if raw.get("longest_task") is not None:
        out["longest_task_ms"] = float(raw["longest_task"])
    return out


def judge(metric: str, value: float | None) -> str:
    """値を `good` / `needs-improvement` / `poor` / `unknown` に分類する。"""
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


def passed(metrics: dict[str, float]) -> bool:
    """すべての metric が good または needs-improvement なら True (poor が 1 件でも あれば False)。"""
    return all(judge(k, v) != "poor" for k, v in metrics.items())


def should_auto_measure(
    page_roles: list[str],
    *,
    auto_roles: frozenset[str] = DEFAULT_AUTO_ROLES,
) -> bool:
    """testcase の page_role に基づき CWV を自動計測すべきか判定する。"""
    return any(r in auto_roles for r in page_roles)
