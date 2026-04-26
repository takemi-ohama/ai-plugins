"""Phase 2 unit: evidence / a11y / cwv fixture の純関数ロジック。

Playwright を起動しないため、``NdfEvidence`` の listener / page_role marker
の解釈 / autouse の guard 条件など、純粋なロジック部分のみをテストする。
end-to-end は Phase 3 以降で smoke 化する。
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from scenario_test.config import (
    A11yConfig,
    BasicAuth,
    Config,
    CwvConfig,
    PlaywrightConfig,
    ReportConfig,
    RunnerConfig,
)
from scenario_test.fixtures.a11y import _page_roles_from_marker as a11y_marker
from scenario_test.fixtures.cwv import _page_roles_from_marker as cwv_marker
from scenario_test.fixtures.evidence import NdfEvidence, _safe_slug, _safe_case_slug


def _make_config(
    tolerated_console: list[str] | None = None,
    tolerated_page: list[str] | None = None,
) -> Config:
    return Config(
        base_url="https://example.com",
        basic_auth=BasicAuth(user="", password=""),
        verify_tls=False,
        roles={},
        playwright=PlaywrightConfig.defaults(),
        runner=RunnerConfig(),
        report=ReportConfig(),
        config_path=Path("/tmp/scenario.config.yaml"),
        tolerated_console_errors=tolerated_console or [],
        tolerated_page_errors=tolerated_page or [],
        a11y=A11yConfig(),
        cwv=CwvConfig(),
    )


# --- _safe_slug -----------------------------------------------------


@pytest.mark.parametrize(
    "name,expected_pattern",
    [
        ("test_simple", r"^test_simple$"),
        ("test/with/slashes", r"^test-with-slashes$"),
        ("Test ID with spaces!!", r"^test-id-with-spaces$"),
        ("", r"^test$"),  # fallback
    ],
)
def test_safe_slug(name: str, expected_pattern: str):
    assert re.match(expected_pattern, _safe_slug(name, fallback="test"))


# --- _safe_case_slug ------------------------------------------------


def _node(nodeid: str):
    return SimpleNamespace(nodeid=nodeid, name=nodeid.split("::")[-1])


def test_safe_case_slug_is_idempotent(monkeypatch):
    """同じ nodeid + 同じ worker は常に同じ slug (idempotent)。"""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    node = _node("tests/test_x.py::test_func")
    assert _safe_case_slug(node) == _safe_case_slug(node)


def test_safe_case_slug_different_nodeid_gives_different_slug(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    slug_a = _safe_case_slug(_node("tests/test_x.py::test_a"))
    slug_b = _safe_case_slug(_node("tests/test_x.py::test_b"))
    assert slug_a != slug_b


def test_safe_case_slug_xdist_worker_changes_slug(monkeypatch):
    """PYTEST_XDIST_WORKER が変われば slug も変わる。"""
    node = _node("tests/test_x.py::test_func")
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    slug_gw0 = _safe_case_slug(node)
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")
    slug_gw1 = _safe_case_slug(node)
    assert slug_gw0 != slug_gw1


def test_safe_case_slug_length_bounded(monkeypatch):
    """slug が適切な長さに収まる (70 文字以内)。"""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    long_nodeid = "tests/" + "a" * 100 + ".py::test_very_long_name"
    slug = _safe_case_slug(_node(long_nodeid))
    assert len(slug) <= 70


# --- NdfEvidence listeners ------------------------------------------


def test_ndf_evidence_console_listener_filters_tolerated():
    """tolerated パターンに合致する console.error は記録されない。"""
    cfg = _make_config(tolerated_console=[r"benign 3rd-party warning"])
    ev = NdfEvidence(case_dir=Path("/tmp/dummy"), config=cfg, enabled=True)

    benign = SimpleNamespace(
        type="error",
        text="benign 3rd-party warning: x",
        location={"url": "https://cdn.example.com/x.js"},
    )
    ev._on_console(benign)
    assert ev.console_errors == []

    real = SimpleNamespace(
        type="error",
        text="ReferenceError: foo is not defined",
        location={"url": "https://example.com/page"},
    )
    ev._on_console(real)
    assert len(ev.console_errors) == 1
    assert "ReferenceError" in ev.console_errors[0]


def test_ndf_evidence_pageerror_listener_filters_tolerated():
    cfg = _make_config(tolerated_page=[r"^Tolerable\b"])
    ev = NdfEvidence(case_dir=Path("/tmp/dummy"), config=cfg, enabled=True)

    ev._on_pageerror(Exception("Tolerable: ignore me"))
    assert ev.page_errors == []
    ev._on_pageerror(RuntimeError("Real bug here"))
    assert ev.page_errors == ["Real bug here"]


def test_ndf_evidence_console_listener_skips_non_error_type():
    cfg = _make_config()
    ev = NdfEvidence(case_dir=Path("/tmp/dummy"), config=cfg, enabled=True)
    info = SimpleNamespace(type="log", text="hello", location={})
    ev._on_console(info)
    assert ev.console_errors == []


def test_ndf_evidence_runtime_error_summary():
    cfg = _make_config()
    ev = NdfEvidence(case_dir=Path("/tmp/dummy"), config=cfg, enabled=True)
    assert ev.has_runtime_errors is False
    assert ev.runtime_error_summary() == ""

    ev.console_errors.append("foo")
    ev.page_errors.append("bar")
    assert ev.has_runtime_errors is True
    summary = ev.runtime_error_summary()
    assert "console.error 1 件" in summary
    assert "pageerror 1 件" in summary


def test_ndf_evidence_disabled_skips_tracing():
    cfg = _make_config()
    ev = NdfEvidence(
        case_dir=Path("/tmp/dummy"),
        config=cfg,
        enabled=False,
        trace_path=None,
    )
    fake_ctx = MagicMock()
    ev.start_tracing(fake_ctx)
    fake_ctx.tracing.start.assert_not_called()
    ev.stop_tracing(fake_ctx)
    fake_ctx.tracing.stop.assert_not_called()


def test_ndf_evidence_confirm_har_sets_relpath(tmp_path: Path):
    cfg = _make_config()
    har = tmp_path / "request.har"
    har.write_text("{}", encoding="utf-8")
    ev = NdfEvidence(case_dir=tmp_path, config=cfg, enabled=True, har_path=har)
    ev.confirm_har()
    assert ev.har_relpath == "request.har"


def test_ndf_evidence_confirm_har_skips_when_missing(tmp_path: Path):
    cfg = _make_config()
    ev = NdfEvidence(
        case_dir=tmp_path,
        config=cfg,
        enabled=True,
        har_path=tmp_path / "missing.har",
    )
    ev.confirm_har()
    assert ev.har_relpath is None


# --- page_role marker collector -------------------------------------


def test_page_role_marker_collector_handles_str_args():
    item = MagicMock()
    item.iter_markers.return_value = [SimpleNamespace(args=("form", "list"))]
    assert a11y_marker(item) == ["form", "list"]
    assert cwv_marker(item) == ["form", "list"]


def test_page_role_marker_collector_handles_list_arg():
    item = MagicMock()
    item.iter_markers.return_value = [SimpleNamespace(args=(["dashboard", "lp"],))]
    assert a11y_marker(item) == ["dashboard", "lp"]


def test_page_role_marker_collector_returns_empty_when_no_marker():
    item = MagicMock()
    item.iter_markers.return_value = []
    assert a11y_marker(item) == []
    assert cwv_marker(item) == []
