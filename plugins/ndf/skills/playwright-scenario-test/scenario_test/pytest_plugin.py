"""playwright-scenario-test の pytest plugin。

CLI options:
- ``--ndf-config <path>``: scenario.config.yaml を指定
- ``--ndf-out-dir <path>``: 成果物 (HAR / trace / 動画 / report) の出力先
- ``--ndf-no-evidence``: evidence 収集を OFF
- ``--ndf-hud``: HUD overlay を ON
- ``--ndf-drive-folder <id>``: Drive 連携

markers:
- ``page_role(*roles)``: a11y / CWV autouse の判定材料
- ``role(role_id)``: login する role を明示 (`ndf_role_<id>` fixture と並用可)
- ``phase(num)``: report.md のフェーズ集計用
- ``priority(level)``: report.md のソート用
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import pytest

from scenario_test.pytest_report import NdfTestEntry, write_report

# 配下の fixture モジュールを pytest_plugins として読み込む
# (こうすると entry-point 経由で plugin がロードされた瞬間に fixture が
#  全 test に対して discover される)。
pytest_plugins = [
    "scenario_test.fixtures.auth",
    "scenario_test.fixtures.evidence",
    "scenario_test.fixtures.a11y",
    "scenario_test.fixtures.cwv",
]


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("ndf", "playwright-scenario-test (NDF)")
    group.addoption(
        "--ndf-config",
        action="store",
        default=None,
        help="scenario.config.yaml へのパス (env NDF_CONFIG, または ./scenario.config.yaml も可)",
    )
    group.addoption(
        "--ndf-out-dir",
        action="store",
        default=None,
        help="成果物出力先ディレクトリ (default: ./reports/<run-id>/)",
    )
    group.addoption(
        "--ndf-no-evidence",
        action="store_true",
        default=False,
        help="HAR / trace / video の収集を OFF にする",
    )
    group.addoption(
        "--ndf-hud",
        action="store_true",
        default=False,
        help="HUD overlay (字幕 + カーソル) を全 page に inject する",
    )
    group.addoption(
        "--ndf-drive-folder",
        action="store",
        default=None,
        help="Drive アップロード先フォルダ ID (terminal_summary 後に upload 実行)",
    )


# ---------------------------------------------------------------------------
# Markers / Config
# ---------------------------------------------------------------------------


_NDF_MARKERS: list[tuple[str, str]] = [
    ("page_role", "page_role(*roles): a11y / CWV autouse の判定 (例: form, list, dashboard)"),
    ("role", "role(role_id): test がどの login role を要求するか (`ndf_role_<id>` 経由でも可)"),
    ("phase", "phase(num): report.md のフェーズ集計用 (1〜N の整数)"),
    ("priority", "priority(level): report.md のソート用 (high/mid/low など任意文字列)"),
]


def pytest_configure(config: pytest.Config) -> None:
    """marker 登録 + config の早期 load を試みる。

    config 読み込みは ``ndf_config`` fixture でも遅延ロードされるが、
    ``ndf_role_<id>`` fixture を *動的登録* するためには
    ``pytest_configure`` で 1 度 Config をロードしておく必要がある。
    failure は警告にとどめ、利用者が NDF 機能を使わない場合に test 全体を
    潰さないようにする。
    """
    for name, doc in _NDF_MARKERS:
        config.addinivalue_line("markers", f"{name}: {doc}")

    # 動的 fixture 登録のため、可能なら Config を early load する。
    cfg = _try_load_config_silently(config)
    if cfg is not None:
        from scenario_test.fixtures import auth as auth_module

        registered = auth_module.register_role_fixtures(auth_module, cfg)
        if registered:
            # plugin 自体にも公開しておく (ユーザが import 元を調整しなくて良いように)。
            import scenario_test.pytest_plugin as plugin_self

            for name in registered:
                fn = getattr(auth_module, name, None)
                if fn is not None:
                    setattr(plugin_self, name, fn)
        # session 中で再利用するためにキャッシュする。
        config._ndf_config = cfg  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Reports / hooks
# ---------------------------------------------------------------------------


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """test の各 phase 終了時に ``ndf_evidence`` の状態をレポートに紐付ける。

    FAIL 時には evidence の trace/HAR path を log に追記し、
    成果物 path / marker を rep.user_properties に保存して
    ``pytest_terminal_summary`` で report.md に集約する。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when != "call":
        return

    # ndf_evidence fixture が attach した状態を直接参照
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

    # markers を user_properties に転写
    page_roles: list[str] = []
    for marker in item.iter_markers(name="page_role"):
        for arg in marker.args:
            if isinstance(arg, str):
                page_roles.append(arg)
            elif isinstance(arg, (list, tuple)):
                page_roles.extend(str(a) for a in arg)
    if page_roles:
        rep.user_properties.append(("ndf_page_role", page_roles))

    role_marker = item.get_closest_marker("role")
    if role_marker is not None and role_marker.args:
        rep.user_properties.append(("ndf_role", str(role_marker.args[0])))

    phase_marker = item.get_closest_marker("phase")
    if phase_marker is not None and phase_marker.args:
        try:
            rep.user_properties.append(("ndf_phase", int(phase_marker.args[0])))
        except (TypeError, ValueError):
            pass

    priority_marker = item.get_closest_marker("priority")
    if priority_marker is not None and priority_marker.args:
        rep.user_properties.append(("ndf_priority", str(priority_marker.args[0])))


# ---------------------------------------------------------------------------
# Terminal summary / session finish
# ---------------------------------------------------------------------------


def _collect_entries(terminalreporter) -> list[NdfTestEntry]:
    """terminalreporter から ``NdfTestEntry`` のリストを構築する。"""
    entries: list[NdfTestEntry] = []
    for outcome_key in ("passed", "failed", "skipped", "error"):
        for rep in terminalreporter.stats.get(outcome_key, []):
            # rep.when != "call" の setup/teardown error は集約スキップ
            if getattr(rep, "when", "call") not in ("call", "setup"):
                continue
            props = dict(rep.user_properties or [])
            entries.append(
                NdfTestEntry(
                    nodeid=getattr(rep, "nodeid", "?"),
                    name=getattr(rep, "head_line", getattr(rep, "nodeid", "?")),
                    outcome=outcome_key,
                    duration_s=float(getattr(rep, "duration", 0.0) or 0.0),
                    page_role=list(props.get("ndf_page_role") or []),
                    role=props.get("ndf_role"),
                    phase=int(props.get("ndf_phase") or 0),
                    priority=props.get("ndf_priority"),
                    har_path=props.get("ndf_har"),
                    trace_path=props.get("ndf_trace"),
                    console_errors=int(props.get("ndf_console_errors") or 0),
                    page_errors=int(props.get("ndf_page_errors") or 0),
                    # Amazon Q Critical-3: skipped 時の longrepr は tuple 形式のため
                    # failed / error のときのみ str() 化する。他 outcome は None のまま。
                    error_message=(
                        str(rep.longrepr)
                        if outcome_key in ("failed", "error") and rep.longrepr
                        else None
                    ),
                )
            )
    return entries


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """``reports/<run-id>/report.md`` を生成する。

    ``--ndf-out-dir`` 指定があればそこに、なければ session 開始時の
    ``ndf_out_dir`` fixture と同じ規則で path を解決する。
    """
    # session 中で 1 件も test を回していない (collect-only など) ならスキップ
    stats = terminalreporter.stats
    if not any(stats.get(k) for k in ("passed", "failed", "skipped", "error")):
        return

    cached_cfg = getattr(config, "_ndf_config", None)
    base_url = cached_cfg.base_url if cached_cfg is not None else None
    title = (
        cached_cfg.report.title
        if cached_cfg is not None
        else "シナリオ E2E テスト 実施報告書"
    )

    raw_out: str | None = config.getoption("ndf_out_dir", default=None)
    if raw_out:
        out_dir = Path(raw_out).resolve()
    else:
        run_id = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        out_dir = (Path.cwd() / "reports" / run_id).resolve()

    entries = _collect_entries(terminalreporter)
    if not entries:
        return

    started = _dt.datetime.now() - _dt.timedelta(
        seconds=sum(e.duration_s for e in entries)
    )
    finished = _dt.datetime.now()
    path = write_report(
        entries,
        out_dir=out_dir,
        started_at=started,
        finished_at=finished,
        title=title,
        base_url=base_url,
    )
    terminalreporter.write_sep("-", "ndf report")
    terminalreporter.write_line(f"report.md generated: {path}")

    # session 後の Drive アップロードに使うため pickle 不要な情報を保存
    config._ndf_report_path = path  # type: ignore[attr-defined]
    config._ndf_out_dir = out_dir  # type: ignore[attr-defined]


def pytest_sessionfinish(session, exitstatus):
    """``--ndf-drive-folder`` 指定時、生成済 report.md と evidence を Drive アップ。

    ``upload_evidence.upload`` を直接呼ぶ。失敗時は警告のみで test 結果には影響しない。
    """
    folder_id: str | None = session.config.getoption(
        "ndf_drive_folder", default=None
    )
    if not folder_id:
        return

    report_path: Path | None = getattr(session.config, "_ndf_report_path", None)
    out_dir: Path | None = getattr(session.config, "_ndf_out_dir", None)
    if report_path is None or out_dir is None:
        return

    try:
        # scripts/ を import path に追加して upload_evidence をロード
        import sys

        scripts_dir = (
            Path(__file__).resolve().parent.parent / "scripts"
        )
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        import upload_evidence  # type: ignore  # noqa: I001

        # report.md は kind=any でアップ
        if report_path.exists():
            upload_evidence.upload(
                report_path, kind="any", parent_folder_id=folder_id, public=False
            )

        # trace.zip / *.har / *.mp4 を 1 階層下から拾い上げる
        for sub in out_dir.iterdir():
            if not sub.is_dir():
                continue
            for f in sub.iterdir():
                if f.suffix in (".zip", ".har", ".mp4", ".webm"):
                    kind = upload_evidence.detect_kind(f)
                    upload_evidence.upload(
                        f, kind=kind, parent_folder_id=folder_id, public=False
                    )
    except Exception as exc:  # pragma: no cover - depends on Drive auth
        import warnings

        warnings.warn(
            f"[ndf] Drive upload 失敗 (session continues): {exc}",
            stacklevel=1,
        )


def _try_load_config_silently(config: pytest.Config) -> Any | None:
    """``--ndf-config`` 等から Config を試行ロードする。失敗時は None。"""
    import os
    from pathlib import Path

    raw_path: str | None = config.getoption("ndf_config", default=None)
    if not raw_path:
        env = os.environ.get("NDF_CONFIG")
        if env:
            raw_path = env
    if not raw_path:
        candidate = Path.cwd() / "scenario.config.yaml"
        if candidate.exists():
            raw_path = str(candidate)
    if not raw_path:
        return None

    try:
        from scenario_test.config import Config

        return Config.load(Path(raw_path).resolve())
    except Exception as exc:  # pragma: no cover - depends on user config
        import warnings

        warnings.warn(
            f"[ndf] config load 失敗 ({raw_path}): {exc}. "
            "ndf_role_<id> fixture は動的登録されません。",
            stacklevel=2,
        )
        return None
