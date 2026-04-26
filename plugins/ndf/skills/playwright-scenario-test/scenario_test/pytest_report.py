"""pytest hook で集めた test result から Markdown レポートを生成する。

``pytest_terminal_summary`` から呼ばれ、``reports/<run-id>/report.md`` を生成する。
``--ndf-drive-folder`` 指定時は Drive アップロードと URL 差し込みも担当。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class NdfTestEntry:
    """1 test 関数分のレポート用エントリ。

    pytest の ``TestReport`` から要点だけを抽出して保持する
    (``user_properties`` 経由で ``ndf_evidence`` の状態が紐付く)。
    """

    nodeid: str
    name: str
    outcome: str  # passed / failed / skipped / xfailed / xpassed / error
    duration_s: float
    page_role: list[str] = field(default_factory=list)
    role: str | None = None
    phase: int = 0
    priority: str | None = None
    har_path: str | None = None
    trace_path: str | None = None
    console_errors: int = 0
    page_errors: int = 0
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.outcome in ("passed", "xfailed")

    @property
    def status_label(self) -> str:
        return {
            "passed": "OK",
            "failed": "FAIL",
            "skipped": "SKIP",
            "xfailed": "XFAIL",
            "xpassed": "XPASS",
            "error": "ERROR",
        }.get(self.outcome, self.outcome.upper())


def render_markdown(
    entries: Iterable[NdfTestEntry],
    *,
    started_at: _dt.datetime,
    finished_at: _dt.datetime,
    title: str = "シナリオ E2E テスト 実施報告書",
    base_url: str | None = None,
) -> str:
    """test entries から Markdown 文字列を生成する。"""
    entries_list = list(entries)
    total = len(entries_list)
    passed = sum(1 for e in entries_list if e.outcome == "passed")
    failed = sum(1 for e in entries_list if e.outcome == "failed")
    skipped = sum(1 for e in entries_list if e.outcome == "skipped")
    errors = sum(1 for e in entries_list if e.outcome == "error")
    duration = (finished_at - started_at).total_seconds()
    all_pass = total > 0 and passed == total

    lines: list[str] = [
        f"# {title}",
        "",
        f"- 実行開始: {started_at:%Y-%m-%d %H:%M:%S}",
        f"- 実行終了: {finished_at:%Y-%m-%d %H:%M:%S}",
        f"- 所要時間: {duration:.1f} 秒",
    ]
    if base_url:
        lines.append(f"- 対象URL : {base_url}")
    lines.extend([
        f"- **結果: {passed}/{total} test PASS"
        + (f" (全PASS)" if all_pass else f" / FAIL {failed} / SKIP {skipped} / ERROR {errors}")
        + "**",
        "",
        "## サマリ",
        "",
        "| nodeid | role | page_role | status | duration | console.error | pageerror |",
        "|---|---|---|---|---|---|---|",
    ])

    # phase / priority / nodeid の順でソート
    sorted_entries = sorted(
        entries_list,
        key=lambda e: (e.phase, e.priority or "", e.nodeid),
    )
    for e in sorted_entries:
        page_role = ",".join(e.page_role) if e.page_role else "-"
        lines.append(
            f"| `{e.nodeid}` | {e.role or '-'} | {page_role} | "
            f"{e.status_label} | {e.duration_s:.2f}s | "
            f"{e.console_errors} | {e.page_errors} |"
        )

    failures = [e for e in sorted_entries if e.outcome in ("failed", "error")]
    if failures:
        lines.extend(["", "## FAIL / ERROR の詳細", ""])
        for e in failures:
            lines.append(f"### `{e.nodeid}` — {e.status_label}")
            lines.append("")
            if e.error_message:
                lines.append("```")
                lines.append(e.error_message[:2000])
                lines.append("```")
            if e.trace_path:
                lines.append(f"- trace: `{e.trace_path}`")
            if e.har_path:
                lines.append(f"- HAR: `{e.har_path}`")
            lines.append("")

    return "\n".join(lines) + "\n"


def write_report(
    entries: Iterable[NdfTestEntry],
    *,
    out_dir: Path,
    started_at: _dt.datetime,
    finished_at: _dt.datetime,
    title: str = "シナリオ E2E テスト 実施報告書",
    base_url: str | None = None,
) -> Path:
    """``out_dir/report.md`` を書き出してそのパスを返す。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    md = render_markdown(
        entries,
        started_at=started_at,
        finished_at=finished_at,
        title=title,
        base_url=base_url,
    )
    path = out_dir / "report.md"
    path.write_text(md, encoding="utf-8")
    return path
