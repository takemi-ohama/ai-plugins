"""Phase 1 smoke: ``scenario_test.pytest_plugin`` がロードされて基本機能が動くこと。

ここでは Playwright を起動しない (auth fixture は session 内で 1 度ログインを
試みるため、Playwright browser binary が無くても落ちないこと、および
``--ndf-config`` が無い場合に skip されることを検証する)。
"""

from __future__ import annotations

import textwrap
from pathlib import Path


def test_plugin_module_importable():
    """plugin module が import 可能で pytest_plugins/markers が宣言されている。"""
    from scenario_test import pytest_plugin

    assert "scenario_test.fixtures.auth" in pytest_plugin.pytest_plugins
    names = [m for m, _ in pytest_plugin._NDF_MARKERS]
    assert {"page_role", "role", "phase", "priority"}.issubset(set(names))


def test_addoption_registered(pytester):
    """``--ndf-config`` 等の CLI option が pytest -h に出ること。"""
    pytester.makepyfile("def test_dummy(): pass\n")
    res = pytester.runpytest("--help")
    out = res.stdout.str()
    assert "--ndf-config" in out
    assert "--ndf-out-dir" in out
    assert "--ndf-no-evidence" in out
    assert "--ndf-hud" in out
    assert "--ndf-drive-folder" in out


def test_markers_registered(pytester):
    """``pytest --markers`` に ndf 系 marker が出ること。"""
    pytester.makepyfile("def test_dummy(): pass\n")
    res = pytester.runpytest("--markers")
    out = res.stdout.str()
    assert "page_role" in out
    assert "role(role_id)" in out
    assert "phase(num)" in out
    assert "priority(level)" in out


def test_ndf_config_skips_when_unset(pytester):
    """``--ndf-config`` 未指定 + ./scenario.config.yaml も無い場合、
    ``ndf_config`` を要求した test は skip される。"""
    pytester.makepyfile(
        textwrap.dedent(
            """
            def test_uses_config(ndf_config):
                assert ndf_config.base_url
            """
        )
    )
    res = pytester.runpytest("-q")
    res.assert_outcomes(skipped=1)


def test_ndf_config_loads_when_provided(pytester, tmp_path: Path):
    """``--ndf-config`` を YAML で渡せば ``ndf_config`` fixture が Config を返す。"""
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
                  fail_if_url_contains: /login
                  fields:
                    email: admin@example.com
                    password: pass
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            def test_loads(ndf_config):
                assert ndf_config.base_url == "https://example.com"
                assert "admin" in ndf_config.roles
            """
        )
    )
    res = pytester.runpytest("-q", f"--ndf-config={cfg_path}")
    res.assert_outcomes(passed=1)


def test_role_fixture_dynamically_registered(pytester, tmp_path: Path):
    """``ndf_role_<id>`` fixture が dynamic に登録されること
    (Playwright を起動せずに fixture 名解決のみ確認)。"""
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
                  fail_if_url_contains: /login
                  fields:
                    email: admin@example.com
                    password: pass
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            def test_fixture_visible(request):
                # `--fixtures` ではなく `getfixturedefs` で確認することで、
                # Playwright を起動せずに fixture の登録だけを assert する。
                defs = request._fixturemanager.getfixturedefs(
                    "ndf_role_admin", request.node
                )
                assert defs is not None and len(defs) > 0
            """
        )
    )
    res = pytester.runpytest("-q", f"--ndf-config={cfg_path}")
    res.assert_outcomes(passed=1)
