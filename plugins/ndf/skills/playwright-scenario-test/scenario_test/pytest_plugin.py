"""playwright-scenario-test の pytest plugin (v0.3.0+)。

PLAN17 Task 1: 骨組みのみ (addoption / configure / markers / config fixture)。

- ``--ndf-config <path>``: scenario.config.yaml を指定
- ``--ndf-out-dir <path>``: 成果物 (HAR / trace / 動画 / report) の出力先
- ``--ndf-no-evidence``: evidence 収集を OFF (Phase 2 で本格利用)
- ``--ndf-hud``: HUD overlay を ON (Phase 3 で本格利用)
- ``--ndf-drive-folder <id>``: Drive 連携 (Phase 3 で本格利用)

markers:
- ``page_role(*roles)``: a11y / CWV autouse の判定材料 (Phase 2)
- ``role(role_id)``: login する role を明示 (`ndf_role_<id>` fixture と並用可)
- ``phase(num)``: report.md のフェーズ集計用 (Phase 3)
- ``priority(level)``: report.md のソート用 (Phase 3)

Phase 1 では fixture を提供するのみ。a11y / CWV / report 連携は Phase 2-3
で順次追加する。
"""

from __future__ import annotations

from typing import Any

import pytest

# 配下の fixture モジュールを pytest_plugins として読み込む
# (こうすると entry-point 経由で plugin がロードされた瞬間に fixture が
#  全 test に対して discover される)。
pytest_plugins = ["scenario_test.fixtures.auth"]


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
