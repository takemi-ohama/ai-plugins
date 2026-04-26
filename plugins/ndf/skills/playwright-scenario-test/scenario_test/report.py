"""テスト結果から Markdown レポートを生成する。

タイトル・フェーズラベル・計画書リンクは config.report.* から受け取る。
プロジェクト固有のラベル付けはコードを編集せず config.yaml で完結する。
"""

from __future__ import annotations

import datetime as _dt
from collections import OrderedDict
from pathlib import Path

from scenario_test.config import Config
from scenario_test.testcase import TestCaseResult


def _mark(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def render_report(
    results: list[TestCaseResult],
    *,
    config: Config,
    run_dir: Path,
    started_at: _dt.datetime,
    finished_at: _dt.datetime,
    workers: int,
) -> tuple[Path, dict]:
    """Markdown レポートを書き出し、(レポートパス, サマリ dict) を返す。"""

    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.ok)
    total_steps = sum(r.total_steps for r in results)
    passed_steps = sum(r.passed_steps for r in results)
    has_error = any(r.error for r in results)
    duration = (finished_at - started_at).total_seconds()
    all_pass = passed_cases == total_cases and not has_error
    report_cfg = config.report

    sorted_results = sorted(results, key=lambda r: (r.phase, r.testcase_id))
    by_phase: "OrderedDict[int, list[TestCaseResult]]" = OrderedDict()
    for r in sorted_results:
        by_phase.setdefault(r.phase, []).append(r)

    lines: list[str] = [
        f"# {report_cfg.title}",
        "",
        f"- 計画書: [{report_cfg.test_plan_link}]({report_cfg.test_plan_link})",
        f"- 実行開始: {started_at:%Y-%m-%d %H:%M:%S}",
        f"- 実行終了: {finished_at:%Y-%m-%d %H:%M:%S}",
        f"- 所要時間: {duration:.1f} 秒",
        f"- 並列ワーカ数: {workers}",
        f"- 対象URL : {config.base_url}",
        f"- **結果: {passed_cases}/{total_cases} ケース PASS "
        f"({'全PASS' if all_pass else f'FAIL {total_cases - passed_cases}件'})**",
        f"- ステップ集計: {passed_steps}/{total_steps} steps PASS",
        "",
        "## サマリ",
        "",
        "| ケースID | フェーズ | ロール | 結果 | ステップ | 時間 | タイトル |",
        "|---|---:|---|:---:|---:|---:|---|",
    ]
    lines.extend(
        f"| `{r.testcase_id}` | {r.phase} | {r.role or '-'} | "
        f"{_mark(r.ok)} | {r.passed_steps}/{r.total_steps} | "
        f"{r.duration_sec:.1f}s | {r.title} |"
        for r in sorted_results
    )
    lines.extend(["", "## 詳細", ""])
    for phase, phase_results in by_phase.items():
        label = report_cfg.phase_labels.get(phase, f"phase {phase}")
        lines.append(f"### Phase {phase} — {label}")
        lines.append("")
        for r in phase_results:
            _render_testcase(r, lines)
        lines.append("")

    report_path = run_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "total_steps": total_steps,
        "passed_steps": passed_steps,
        "all_pass": all_pass,
    }
    return report_path, summary


def _render_testcase(r: TestCaseResult, out: list[str]) -> None:
    tc_id = r.testcase_id
    out.append(f"#### `{tc_id}` — {r.title} [{_mark(r.ok)}]")
    out.append("")
    out.append(f"- ロール  : {r.role or '-'} / 優先度: {r.priority}")
    if r.page_role:
        out.append(f"- page_role: {', '.join(r.page_role)}")
    out.append(f"- 種別    : {r.type}")
    out.append(f"- 開始    : {r.started_at:%H:%M:%S} / 所要 {r.duration_sec:.1f}s")
    if r.tags:
        out.append(f"- タグ    : {', '.join(r.tags)}")
    if r.video_relpath:
        out.append(
            f"- 動画    : [`{tc_id}/{r.video_relpath}`](./{tc_id}/{r.video_relpath})"
        )
    # trace は playwright show-trace で対話的に確認可能 (生成有無を実ファイルで判定)
    trace_name = f"{tc_id}.trace.zip"
    if (r.case_dir / trace_name).exists():
        out.append(
            f"- Trace   : [`{tc_id}/{trace_name}`](./{tc_id}/{trace_name}) "
            "— `uv run playwright show-trace …` で閲覧可"
        )
    if r.har_relpath:
        out.append(
            f"- HAR     : [`{tc_id}/{r.har_relpath}`](./{tc_id}/{r.har_relpath}) "
            "— ブラウザ開発者ツールの Network 系で読み込み可"
        )
    out.append(f"- 個別ログ: [`{tc_id}/log.txt`](./{tc_id}/log.txt)")
    if r.nav_vars:
        out.append(f"- 抽出変数: `{r.nav_vars}`")
    if r.page_errors:
        out.append(f"- ⚠️ pageerror: {len(r.page_errors)} 件 (auto-FAIL 要因)")
    if r.console_errors:
        out.append(f"- ⚠️ console.error: {len(r.console_errors)} 件 (auto-FAIL 要因)")
    if r.axe_violations:
        out.append(f"- ⚠️ axe-core 違反: {len(r.axe_violations)} 件")
    if r.cwv_metrics:
        cwv_str = ", ".join(f"{k}={v:.0f}" for k, v in r.cwv_metrics.items())
        mark = "PASS" if r.cwv_passed else "FAIL"
        out.append(f"- 🚀 Core Web Vitals ({mark}): {cwv_str}")
    if r.error:
        out.extend(["", "**FATAL エラー**:", "", "```", r.error.strip(), "```"])
    if r.page_errors:
        out.extend(["", "**pageerror 詳細** (先頭 5 件):", "", "```"])
        for line in r.page_errors[:5]:
            out.append(line)
        out.append("```")
    if r.console_errors:
        out.extend(["", "**console.error 詳細** (先頭 5 件):", "", "```"])
        for line in r.console_errors[:5]:
            out.append(line)
        out.append("```")
    if r.axe_violations:
        out.extend(["", "**axe-core 違反 詳細** (先頭 5 件):", ""])
        out.append("| ID | impact | help |")
        out.append("|---|---|---|")
        for v in r.axe_violations[:5]:
            help_url = v.get("helpUrl") or ""
            help_text = v.get("help", "")
            help_md = f"[{help_text}]({help_url})" if help_url else help_text
            out.append(f"| `{v.get('id')}` | {v.get('impact', '?')} | {help_md} |")
    out.append("")
    if r.steps:
        out.append("| # | ステップ | 結果 | 詳細 | スクショ |")
        out.append("|---:|---|:---:|---|---|")
        for i, s in enumerate(r.steps, 1):
            shot = (
                f"[`{s.screenshot_relpath}`](./{tc_id}/{s.screenshot_relpath})"
                if s.screenshot_relpath else ""
            )
            sub_id = f" `{s.sub_id}`" if s.sub_id else ""
            out.append(f"| {i} |{sub_id} {s.name} | {_mark(s.ok)} | {s.detail} | {shot} |")
    out.append("")
