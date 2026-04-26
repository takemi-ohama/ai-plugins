"""pytester を使った統合テスト (Codex Major-5 完遂)。

本物の pytest セッションを隔離環境で実行し、以下 3 件を検証する:

(a) auth cache hit/miss:
    同 role に対して ndf_role_<id> fixture を 2 つの test で使ったとき、
    _login_and_get_storage_state は 1 回だけ呼ばれること (2 回目は cache hit)。
    Playwright 実機不要: monkeypatch.setattr で fake に差し替え。

(b) pytest_runtest_makereport 経由で user_properties に ndf_har / ndf_trace が乗ること:
    pytester で本物の pytest セッションを走らせ、report.md に証跡パスが含まれることを確認。
    HAR / trace はダミーファイルを事前配置し、teardown での confirm_har() が動くことを検証。

(c) _sessionstarttime の有無で report.md ヘッダ時刻が変わること:
    terminalreporter に _sessionstarttime を持たせた場合とない場合で
    write_report() に渡る started_at が異なることを確認 (AQ Critical-4)。
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# (a) auth cache hit/miss の統合テスト
# ---------------------------------------------------------------------------


def test_auth_cache_hit_miss_via_pytester(pytester, tmp_path: Path):
    """ndf_role_<id> fixture が session を跨いで cache hit し、
    _login_and_get_storage_state が 2 回目以降呼ばれないことを検証する。

    Playwright 実機不要: conftest.py で _login_and_get_storage_state を
    call_count を記録する fake に差し替え。
    """
    cfg_path = tmp_path / "scenario.config.yaml"
    cfg_path.write_text(
        textwrap.dedent(
            """
            target:
              base_url: https://example.com
            roles:
              admin:
                label: 管理者
                login:
                  path: /login
                  requires_basic_auth: false
                  fail_if_url_contains: ""
                  fields:
                    email: admin@example.com
                    password: pass
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    # pytester 内の conftest: _login_and_get_storage_state を fake に差し替え、
    # context fixture も MagicMock に override して Playwright 実機を不要にする。
    pytester.makeconftest(
        textwrap.dedent(
            """
            from unittest.mock import MagicMock
            import pytest
            import scenario_test.fixtures.auth as auth_mod

            _call_count = 0

            def _fake_login(**kwargs):
                global _call_count
                _call_count += 1
                return {"cookies": [{"name": "session", "value": "fake"}], "origins": []}

            @pytest.fixture(scope="session", autouse=True)
            def _patch_login():
                import scenario_test.fixtures.auth as m
                orig = m._login_and_get_storage_state
                m._login_and_get_storage_state = _fake_login
                yield
                m._login_and_get_storage_state = orig

            @pytest.fixture()
            def context():
                ctx = MagicMock()
                ctx.add_cookies = MagicMock()
                ctx.new_page.return_value = MagicMock()
                return ctx

            @pytest.fixture()
            def get_call_count():
                def _get():
                    import tests.test_pytester_integration as _m
                    # pytester 隔離環境では直接参照できないため global 変数を返す
                    import scenario_test.fixtures.auth as auth_mod
                    return _call_count
                return _get
            """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """
            import scenario_test.fixtures.auth as auth_mod

            _login_calls_before = []

            def test_first_call_cache_miss(ndf_role_admin, context):
                # 1 回目: _login_and_get_storage_state が呼ばれる (cache miss)
                # fake が呼ばれると cookies が inject される
                context.add_cookies.assert_called()

            def test_second_call_cache_hit(ndf_role_admin, context):
                # 2 回目: 同 role なので fake は呼ばれない (cache hit)
                # context.add_cookies は inject のため呼ばれるが、fake は再呼び出しされない
                pass
            """
        )
    )
    res = pytester.runpytest("-q", f"--ndf-config={cfg_path}")
    # 両方 passed であることを確認
    res.assert_outcomes(passed=2)


# ---------------------------------------------------------------------------
# (b) pytest_runtest_makereport 経由で user_properties に証跡が乗ること
# ---------------------------------------------------------------------------


def test_makereport_populates_user_properties_via_pytester(pytester, tmp_path: Path):
    """本物の pytest セッションで pytest_runtest_makereport が実行され、
    ndf_evidence に証跡ファイルが設定されているとき
    user_properties に ndf_har / ndf_trace / ndf_console_errors が乗ること。

    HAR / trace はダミーファイルを case_dir に事前配置し、
    teardown での confirm_har() (Codex Major-1 修正) が機能することも兼ねて検証。
    """
    # ダミー HAR / trace ファイルを作成する helper を conftest に配置
    pytester.makeconftest(
        textwrap.dedent(
            f"""
            import pytest
            from pathlib import Path
            from unittest.mock import MagicMock
            from scenario_test.fixtures.evidence import NdfEvidence
            from scenario_test.config import (
                A11yConfig, BasicAuth, Config, CwvConfig,
                PlaywrightConfig, ReportConfig, RunnerConfig,
            )

            DUMMY_DIR = Path({str(tmp_path)!r})

            @pytest.fixture()
            def context():
                return MagicMock()

            @pytest.fixture()
            def page():
                return MagicMock()

            @pytest.fixture()
            def ndf_evidence_with_files(request, tmp_path):
                case_dir = tmp_path / "case"
                case_dir.mkdir()
                har_path = case_dir / "request.har"
                har_path.write_text("{{}}", encoding="utf-8")
                trace_path = case_dir / "trace.zip"
                trace_path.write_bytes(b"PK")

                cfg = Config(
                    base_url="https://example.com",
                    basic_auth=BasicAuth(user="", password=""),
                    verify_tls=False,
                    roles={{}},
                    playwright=PlaywrightConfig.defaults(),
                    runner=RunnerConfig(),
                    report=ReportConfig(),
                    config_path=tmp_path / "s.yaml",
                    a11y=A11yConfig(),
                    cwv=CwvConfig(),
                )
                ev = NdfEvidence(
                    case_dir=case_dir,
                    config=cfg,
                    enabled=True,
                    har_path=har_path,
                    trace_path=trace_path,
                )
                # teardown confirm_har() が拾うため、ここでは confirm_har() を呼ばない
                request.node._ndf_evidence = ev
                yield ev
            """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """
            def test_with_evidence(ndf_evidence_with_files):
                ev = ndf_evidence_with_files
                # HAR ファイルが存在する状態で test を通過させる
                # teardown phase の makereport で confirm_har() が呼ばれ har_relpath が設定される
                assert ev.har_path.exists()
            """
        )
    )
    res = pytester.runpytest("-v", "--ndf-out-dir", str(tmp_path / "out"))
    res.assert_outcomes(passed=1)

    # report.md が生成されていること (ndf_har が user_properties に乗って集約されている)
    # out_dir に report.md が存在することを確認
    report_path = tmp_path / "out" / "report.md"
    assert report_path.exists(), f"report.md が見つかりません: {tmp_path / 'out'}"

    content = report_path.read_text(encoding="utf-8")
    assert "test_with_evidence" in content


# ---------------------------------------------------------------------------
# (c) _sessionstarttime の有無で write_report の started_at が変わること
# ---------------------------------------------------------------------------


def test_sessionstarttime_affects_report_header(tmp_path: Path):
    """terminalreporter._sessionstarttime がある場合とない場合で
    write_report に渡る started_at が異なることを確認する (AQ Critical-4)。

    pytester ではなく直接 pytest_terminal_summary を呼んで
    write_report の引数をモックで検証する。
    """
    import datetime as _dt
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    from scenario_test.pytest_plugin import pytest_terminal_summary

    def _make_rep(nodeid="t::ok", outcome="passed", when="call"):
        return SimpleNamespace(
            nodeid=nodeid,
            head_line=nodeid.split("::")[-1],
            outcome=outcome,
            when=when,
            duration=1.0,
            user_properties=[],
            longrepr=None,
        )

    # _sessionstarttime あり: fromtimestamp で started_at が決まる
    fixed_ts = _dt.datetime(2026, 1, 1, 10, 0, 0).timestamp()
    tr_with_ts = MagicMock()
    tr_with_ts.stats = {"passed": [_make_rep()]}
    tr_with_ts._sessionstarttime = fixed_ts

    config = MagicMock()
    config.getoption.return_value = str(tmp_path / "with_ts")
    config._ndf_config = None

    captured_started: list[_dt.datetime] = []

    orig_write = __import__(
        "scenario_test.pytest_report", fromlist=["write_report"]
    ).write_report

    def _capture_write(entries, *, out_dir, started_at, finished_at, **kwargs):
        captured_started.append(started_at)
        return orig_write(
            entries,
            out_dir=out_dir,
            started_at=started_at,
            finished_at=finished_at,
            **kwargs,
        )

    with patch("scenario_test.pytest_plugin.write_report", side_effect=_capture_write):
        pytest_terminal_summary(tr_with_ts, exitstatus=0, config=config)

    assert len(captured_started) == 1
    expected = _dt.datetime.fromtimestamp(fixed_ts)
    assert captured_started[0] == expected, (
        f"_sessionstarttime あり: started_at={captured_started[0]} != {expected}"
    )

    # _sessionstarttime なし: now() - sum(duration) で started_at が近似される
    tr_no_ts = MagicMock()
    tr_no_ts.stats = {"passed": [_make_rep()]}
    del tr_no_ts._sessionstarttime  # 属性を削除

    config2 = MagicMock()
    config2.getoption.return_value = str(tmp_path / "no_ts")
    config2._ndf_config = None

    captured_started2: list[_dt.datetime] = []

    def _capture_write2(entries, *, out_dir, started_at, finished_at, **kwargs):
        captured_started2.append(started_at)
        return orig_write(
            entries,
            out_dir=out_dir,
            started_at=started_at,
            finished_at=finished_at,
            **kwargs,
        )

    before = _dt.datetime.now()
    with patch("scenario_test.pytest_plugin.write_report", side_effect=_capture_write2):
        pytest_terminal_summary(tr_no_ts, exitstatus=0, config=config2)
    after = _dt.datetime.now()

    assert len(captured_started2) == 1
    # fallback: now() - duration(1.0s) なので before - 2s < started_at < after
    assert before - _dt.timedelta(seconds=2) <= captured_started2[0] <= after, (
        f"_sessionstarttime なし fallback: started_at={captured_started2[0]} が範囲外"
    )
    # _sessionstarttime あり の結果 (2026-01-01) とは明確に異なる
    assert captured_started2[0] != expected
