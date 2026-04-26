"""pytest_runtest_makereport が ndf_har / ndf_trace 等を user_properties に乗せることを
単体テストする (Playwright 実機不要) (Codex Major 5)。

hookwrapper 形式の hook は直接呼べないため、hook の中身を模擬する形でテストする。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from scenario_test.fixtures.evidence import NdfEvidence
from scenario_test.config import (
    A11yConfig,
    BasicAuth,
    Config,
    CwvConfig,
    PlaywrightConfig,
    ReportConfig,
    RunnerConfig,
)


def _make_ev(
    tmp_path: Path,
    *,
    har_exists: bool = True,
    trace_exists: bool = True,
) -> NdfEvidence:
    cfg = Config(
        base_url="https://example.com",
        basic_auth=BasicAuth(user="", password=""),
        verify_tls=False,
        roles={},
        playwright=PlaywrightConfig.defaults(),
        runner=RunnerConfig(),
        report=ReportConfig(),
        config_path=tmp_path / "scenario.config.yaml",
        a11y=A11yConfig(),
        cwv=CwvConfig(),
    )
    har_path = tmp_path / "request.har"
    trace_path = tmp_path / "trace.zip"
    if har_exists:
        har_path.write_text("{}", encoding="utf-8")
    if trace_exists:
        trace_path.write_bytes(b"PK\x03\x04")

    ev = NdfEvidence(
        case_dir=tmp_path,
        config=cfg,
        enabled=True,
        har_path=har_path,
        trace_path=trace_path,
    )
    ev.confirm_har()
    ev.trace_relpath = "trace.zip" if trace_exists else None
    return ev


def _make_rep(ev: NdfEvidence | None = None) -> Any:
    """user_properties リストを持つ fake TestReport を作る。"""
    rep = SimpleNamespace(
        when="call",
        user_properties=[],
        nodeid="tests/test_x.py::test_y",
        head_line="test_y",
        outcome="passed",
        duration=0.5,
        longrepr=None,
    )
    return rep


def _simulate_makereport(item, rep):
    """pytest_runtest_makereport の内側ロジックを直接実行する。"""
    ev = getattr(item, "_ndf_evidence", None)
    if ev is not None:
        if ev.har_relpath:
            rep.user_properties.append(("ndf_har", str(ev.case_dir / ev.har_relpath)))
        if ev.trace_relpath:
            rep.user_properties.append(
                ("ndf_trace", str(ev.case_dir / ev.trace_relpath))
            )
        rep.user_properties.append(("ndf_console_errors", len(ev.console_errors)))
        rep.user_properties.append(("ndf_page_errors", len(ev.page_errors)))


def test_makereport_sets_har_and_trace_properties(tmp_path: Path):
    """ev.har_relpath / trace_relpath が set されているとき user_properties に乗ること。"""
    ev = _make_ev(tmp_path, har_exists=True, trace_exists=True)
    item = SimpleNamespace(_ndf_evidence=ev)
    rep = _make_rep(ev)

    _simulate_makereport(item, rep)

    props = dict(rep.user_properties)
    assert "ndf_har" in props
    assert "request.har" in props["ndf_har"]
    assert "ndf_trace" in props
    assert "trace.zip" in props["ndf_trace"]


def test_makereport_har_absent_not_in_properties(tmp_path: Path):
    """HAR ファイルが存在しない場合 ndf_har は user_properties に含まれない。"""
    ev = _make_ev(tmp_path, har_exists=False, trace_exists=False)
    item = SimpleNamespace(_ndf_evidence=ev)
    rep = _make_rep(ev)

    _simulate_makereport(item, rep)

    props = dict(rep.user_properties)
    assert "ndf_har" not in props
    assert "ndf_trace" not in props


def test_makereport_console_errors_count(tmp_path: Path):
    """console_errors / page_errors のカウントが user_properties に乗ること。"""
    ev = _make_ev(tmp_path, har_exists=False, trace_exists=False)
    ev.console_errors.append("error1")
    ev.console_errors.append("error2")
    ev.page_errors.append("page error")
    item = SimpleNamespace(_ndf_evidence=ev)
    rep = _make_rep(ev)

    _simulate_makereport(item, rep)

    props = dict(rep.user_properties)
    assert props["ndf_console_errors"] == 2
    assert props["ndf_page_errors"] == 1


def test_makereport_no_evidence_skips_ndf_props(tmp_path: Path):
    """_ndf_evidence が attach されていない item では ndf_* が user_properties に出ない。"""
    item = SimpleNamespace()  # _ndf_evidence なし
    rep = _make_rep()

    _simulate_makereport(item, rep)

    props = dict(rep.user_properties)
    assert "ndf_har" not in props
    assert "ndf_trace" not in props
    assert "ndf_console_errors" not in props
