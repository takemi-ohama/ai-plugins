"""Phase 3 unit: ``scenario_test.pytest_report`` の純粋関数テスト。

pytest_terminal_summary 経由の集約は Playwright を要するため smoke では扱わず、
``render_markdown`` と ``write_report`` を直接呼んで Markdown 出力を検証する。
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from scenario_test.pytest_report import NdfTestEntry, render_markdown, write_report


def _entry(**overrides) -> NdfTestEntry:
    base = dict(
        nodeid="tests/test_x.py::test_y",
        name="test_y",
        outcome="passed",
        duration_s=0.42,
    )
    base.update(overrides)
    return NdfTestEntry(**base)  # type: ignore[arg-type]


def test_status_label_mapping():
    assert _entry(outcome="passed").status_label == "OK"
    assert _entry(outcome="failed").status_label == "FAIL"
    assert _entry(outcome="skipped").status_label == "SKIP"
    assert _entry(outcome="xfailed").status_label == "XFAIL"
    assert _entry(outcome="xpassed").status_label == "XPASS"
    assert _entry(outcome="error").status_label == "ERROR"


def test_render_markdown_all_pass():
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 5)
    md = render_markdown(
        [
            _entry(nodeid="t::a"),
            _entry(nodeid="t::b", outcome="passed", duration_s=0.1),
        ],
        started_at=started,
        finished_at=finished,
        title="My Report",
        base_url="https://example.com",
    )
    assert "# My Report" in md
    assert "https://example.com" in md
    assert "2/2 test PASS" in md
    assert "全PASS" in md
    assert "`t::a`" in md
    assert "`t::b`" in md
    # FAIL section は出ない
    assert "FAIL / ERROR の詳細" not in md


def test_render_markdown_with_failure_includes_details():
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 10)
    md = render_markdown(
        [
            _entry(nodeid="t::ok"),
            _entry(
                nodeid="t::fail",
                outcome="failed",
                error_message="AssertionError: expected 1, got 2",
                trace_path="/tmp/runs/x/trace.zip",
                har_path="/tmp/runs/x/request.har",
            ),
        ],
        started_at=started,
        finished_at=finished,
    )
    assert "1/2 test PASS" in md
    assert "FAIL 1" in md
    assert "FAIL / ERROR の詳細" in md
    assert "AssertionError: expected 1, got 2" in md
    assert "trace.zip" in md
    assert "request.har" in md


def test_render_markdown_sorts_by_phase_then_priority_then_nodeid():
    """phase / priority / nodeid 昇順で並ぶ。"""
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 1)
    md = render_markdown(
        [
            _entry(nodeid="t::z", phase=2, priority="low"),
            _entry(nodeid="t::a", phase=1, priority="high"),
            _entry(nodeid="t::b", phase=1, priority="high"),
        ],
        started_at=started,
        finished_at=finished,
    )
    # `t::a` が `t::b` より先に出る
    pos_a = md.index("`t::a`")
    pos_b = md.index("`t::b`")
    pos_z = md.index("`t::z`")
    assert pos_a < pos_b < pos_z


def test_render_markdown_page_role_and_role_columns():
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 1)
    md = render_markdown(
        [_entry(nodeid="t::x", role="admin", page_role=["form", "list"])],
        started_at=started,
        finished_at=finished,
    )
    assert "admin" in md
    assert "form,list" in md


def test_render_markdown_xfailed_counted_in_header():
    """xfailed / xpassed がヘッダ集計に出ること (Codex Major 3)。"""
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 5)
    md = render_markdown(
        [
            _entry(nodeid="t::ok", outcome="passed"),
            _entry(nodeid="t::xf", outcome="xfailed"),
            _entry(nodeid="t::xp", outcome="xpassed"),
        ],
        started_at=started,
        finished_at=finished,
    )
    assert "XFAIL 1" in md
    assert "XPASS 1" in md
    # xpassed がある場合は全PASS にならない
    assert "全PASS" not in md


def test_render_markdown_xfailed_only_is_all_pass():
    """xfailed のみ (xpassed なし) は全PASS 扱い。"""
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 5)
    md = render_markdown(
        [
            _entry(nodeid="t::ok", outcome="passed"),
            _entry(nodeid="t::xf", outcome="xfailed"),
        ],
        started_at=started,
        finished_at=finished,
    )
    assert "全PASS" in md
    assert "XFAIL 1" in md


def test_render_markdown_xfailed_not_in_failure_section():
    """xfailed は FAIL / ERROR の詳細セクションに出ない。"""
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 5)
    md = render_markdown(
        [_entry(nodeid="t::xf", outcome="xfailed")],
        started_at=started,
        finished_at=finished,
    )
    assert "FAIL / ERROR の詳細" not in md


def test_write_report_produces_file(tmp_path: Path):
    started = _dt.datetime(2026, 4, 26, 12, 0, 0)
    finished = _dt.datetime(2026, 4, 26, 12, 0, 1)
    out = tmp_path / "out"
    path = write_report(
        [_entry()], out_dir=out, started_at=started, finished_at=finished
    )
    assert path == out / "report.md"
    assert path.exists()
    txt = path.read_text(encoding="utf-8")
    assert "1/1 test PASS" in txt
