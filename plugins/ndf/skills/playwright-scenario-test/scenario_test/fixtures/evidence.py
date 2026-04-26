"""evidence fixture: HAR / trace / console / pageerror の収集。

pytest-playwright が提供する ``browser_context_args`` / ``context`` / ``page``
fixture と組み合わせて、test 関数ごとに以下を自動収集する:

- HAR: ``browser_context_args`` に ``record_har_path`` を inject
- trace: ``context.tracing.start`` / ``stop`` (``--ndf-no-evidence`` で無効化)
- console.error / pageerror: page listener として attach
  (``tolerated_console_errors`` / ``tolerated_page_errors`` でフィルタ)

artifact の出力先は ``--ndf-out-dir`` (default: ``./reports/<run-id>/``)。
test 関数 ID から sub-dir を作って 1 test = 1 dir で隔離する。
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import pytest

from scenario_test.config import Config


# ---------------------------------------------------------------------------
# Output directory resolver (session scope)
# ---------------------------------------------------------------------------


def _resolve_out_dir(pytestconfig) -> Path:
    """``--ndf-out-dir`` が指定されればそれを、なければ ``reports/<run-id>/``。"""
    raw: str | None = pytestconfig.getoption("ndf_out_dir", default=None)
    if raw:
        return Path(raw).resolve()
    run_id = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return (Path.cwd() / "reports" / run_id).resolve()


@pytest.fixture(scope="session")
def ndf_out_dir(pytestconfig) -> Path:
    """session 全体で共有する成果物ルート。session 開始時に作成する。"""
    out = _resolve_out_dir(pytestconfig)
    out.mkdir(parents=True, exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# Per-test evidence (function scope)
# ---------------------------------------------------------------------------


_FILENAME_SAFE_RE = re.compile(r"[^\w\-]+")


def _safe_slug(name: str, fallback: str = "test") -> str:
    s = _FILENAME_SAFE_RE.sub("-", name).strip("-").lower()
    return s[:80] or fallback


@dataclass
class NdfEvidence:
    """1 test 関数分の証跡コレクタ。"""

    case_dir: Path
    config: Config | None
    enabled: bool

    har_path: Path | None = None
    trace_path: Path | None = None
    har_relpath: str | None = None
    trace_relpath: str | None = None

    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    axe_violations: list[dict[str, Any]] = field(default_factory=list)
    cwv_metrics: dict[str, float] = field(default_factory=dict)
    cwv_passed: bool = True

    log_lines: list[str] = field(default_factory=list)

    _trace_started: bool = field(default=False, init=False, repr=False)
    _tolerated_console_re: list[re.Pattern[str]] = field(
        default_factory=list, init=False, repr=False
    )
    _tolerated_page_re: list[re.Pattern[str]] = field(
        default_factory=list, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if self.config is not None:
            self._tolerated_console_re = [
                re.compile(p) for p in self.config.tolerated_console_errors
            ]
            self._tolerated_page_re = [
                re.compile(p) for p in self.config.tolerated_page_errors
            ]

    # --- listener ------------------------------------------------------

    def attach_listeners(self, page) -> None:
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)

    def _on_console(self, msg) -> None:
        try:
            if msg.type != "error":
                return
            loc = getattr(msg, "location", None) or {}
            text = msg.text[:500]
            for rx in self._tolerated_console_re:
                if rx.search(text):
                    return
            self.console_errors.append(f"{loc.get('url', '?')}: {text}")
        except Exception as exc:  # pragma: no cover
            self.log_lines.append(f"[console listener] {exc}")

    def _on_pageerror(self, exc) -> None:
        try:
            text = str(exc)[:1000]
            for rx in self._tolerated_page_re:
                if rx.search(text):
                    return
            self.page_errors.append(text)
        except Exception as listener_exc:  # pragma: no cover
            self.log_lines.append(f"[pageerror listener] {listener_exc}")

    # --- trace lifecycle (context scope) -------------------------------

    def start_tracing(self, context) -> None:
        if not self.enabled or self.trace_path is None:
            return
        try:
            context.tracing.start(
                name=self.case_dir.name,
                title=self.case_dir.name,
                snapshots=True,
                screenshots=True,
                sources=False,
            )
            self._trace_started = True
        except Exception as exc:  # pragma: no cover
            self.log_lines.append(f"[trace] start 失敗: {exc}")

    def stop_tracing(self, context) -> None:
        if not self._trace_started or self.trace_path is None:
            return
        try:
            context.tracing.stop(path=str(self.trace_path))
            self.trace_relpath = self.trace_path.name
        except Exception as exc:  # pragma: no cover
            self.log_lines.append(f"[trace] stop 失敗: {exc}")

    def confirm_har(self) -> None:
        if self.har_path and self.har_path.exists():
            self.har_relpath = self.har_path.name

    # --- summary -------------------------------------------------------

    @property
    def has_runtime_errors(self) -> bool:
        return bool(self.console_errors or self.page_errors)

    def runtime_error_summary(self) -> str:
        parts: list[str] = []
        if self.page_errors:
            parts.append(f"pageerror {len(self.page_errors)} 件")
        if self.console_errors:
            parts.append(f"console.error {len(self.console_errors)} 件")
        return "Runtime errors detected: " + ", ".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _ndf_config_optional(pytestconfig) -> Config | None:
    """``ndf_config`` を session に 1 度だけ load する (失敗時は None)。

    evidence fixture は ndf_config が無くても動くように optional にしてある。
    """
    cached = getattr(pytestconfig, "_ndf_config", None)
    if cached is not None:
        return cached  # type: ignore[no-any-return]
    return None


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args, pytestconfig, ndf_out_dir
) -> dict[str, Any]:
    """pytest-playwright の ``browser_context_args`` を override し、
    HAR 記録 path を session 共通で 1 ファイルに集約する。

    1 test = 1 HAR にしたい場合は ``ndf_evidence`` fixture 内で
    ``context`` の ``new_context`` を別途張り替える方針 (今は session 内 1 HAR で
    十分なケースが多い)。

    ``--ndf-hud`` 指定時は ``ignore_https_errors`` 等の defaults と並んで
    HUD overlay を ``add_init_script`` で全 page に inject する。
    init_script の attach は ``new_context`` fixture (``ndf_new_context``) 経由
    で行う (browser_context_args は dict のみ受け取り、add_init_script は dict
    で渡せないため)。
    """
    no_evidence = bool(pytestconfig.getoption("ndf_no_evidence", default=False))
    args = dict(browser_context_args or {})
    if not no_evidence:
        args.setdefault(
            "record_har_path", str(ndf_out_dir / "session.har")
        )
        args.setdefault("record_har_content", "omit")
    return args


@pytest.fixture()
def ndf_evidence(
    request,
    pytestconfig,
    ndf_out_dir: Path,
    _ndf_config_optional,
    context,
    page,
) -> Iterator[NdfEvidence]:
    """1 test 関数分の evidence collector を返す。

    - ``--ndf-no-evidence`` が True なら trace/HAR を OFF にし、listener のみ動かす
    - ``page`` fixture から console / pageerror listener を attach
    - ``context.tracing.start/stop`` を裏で実行 (有効時)
    - ``--ndf-hud`` 指定時は ``hud.HUD_INIT_SCRIPT`` を ``context.add_init_script``
      で全 page に inject する
    - ``pytest_runtest_makereport`` から FAIL 時に ``ndf_evidence`` の状態を確認可能
    """
    enabled = not bool(pytestconfig.getoption("ndf_no_evidence", default=False))
    hud_enabled = bool(pytestconfig.getoption("ndf_hud", default=False))
    case_dir = ndf_out_dir / _safe_slug(request.node.name, "test")
    case_dir.mkdir(parents=True, exist_ok=True)

    ev = NdfEvidence(
        case_dir=case_dir,
        config=_ndf_config_optional,
        enabled=enabled,
        har_path=(case_dir / "request.har") if enabled else None,
        trace_path=(case_dir / "trace.zip") if enabled else None,
    )
    ev.attach_listeners(page)
    ev.start_tracing(context)

    # HUD overlay (赤丸カーソル + 字幕) を init_script で inject。
    if hud_enabled:
        try:
            from scenario_test.hud import HUD_INIT_SCRIPT

            context.add_init_script(HUD_INIT_SCRIPT)
        except Exception as exc:  # pragma: no cover
            ev.log_lines.append(f"[hud] add_init_script 失敗: {exc}")

    # request.node に ev を保持して makereport hook から参照可能にする
    request.node._ndf_evidence = ev  # type: ignore[attr-defined]

    try:
        yield ev
    finally:
        try:
            ev.stop_tracing(context)
        finally:
            ev.confirm_har()
