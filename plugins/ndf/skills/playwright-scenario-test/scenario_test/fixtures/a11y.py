"""a11y fixture: ``page_role`` marker に応じた axe-core 自動スキャン。

``@pytest.mark.page_role("form")`` 等が付与された test 関数の終了直前に
axe-core を自動実行する。

利用方法:
- ``@pytest.mark.page_role("form")`` を test に付与すれば autouse 経由で
  axe-core が走る (config.a11y.auto_roles に該当する場合のみ)
- 違反があれば ``config.a11y.fail_on_violations`` (default True) に従い
  ``pytest.fail`` する
- 明示的に scan したい場合は ``ndf_a11y_scan`` fixture を直接呼ぶ
"""

from __future__ import annotations

from collections import Counter
from typing import Iterator

import pytest

from scenario_test import a11y as a11y_mod
from scenario_test.config import Config
from scenario_test.fixtures.evidence import NdfEvidence


def _page_roles_from_marker(item) -> list[str]:
    """test item から ``page_role`` marker の引数 (役割名 list) を集約する。"""
    roles: list[str] = []
    for marker in item.iter_markers(name="page_role"):
        for arg in marker.args:
            if isinstance(arg, str):
                roles.append(arg)
            elif isinstance(arg, (list, tuple)):
                roles.extend(str(a) for a in arg)
    return roles


@pytest.fixture()
def ndf_a11y_scan(page, ndf_evidence: NdfEvidence, _ndf_config_optional):
    """明示呼び出し用: ``violations = ndf_a11y_scan()`` で 1 度スキャン。"""
    config: Config | None = _ndf_config_optional

    def _scan(*, tags: tuple[str, ...] | None = None) -> list[dict]:
        if not a11y_mod.is_available():
            ndf_evidence.log_lines.append(
                "[a11y] axe-playwright-python 未インストール — SKIP "
                "(`uv sync --extra a11y` で有効化)"
            )
            return []
        actual_tags = (
            tuple(tags)
            if tags is not None
            else (
                tuple(config.a11y.tags)
                if config is not None
                else a11y_mod.DEFAULT_TAGS
            )
        )
        violations = a11y_mod.scan_page(page, tags=actual_tags)
        ndf_evidence.axe_violations.extend(violations)
        return violations

    return _scan


@pytest.fixture(autouse=True)
def _ndf_a11y_autouse(request) -> Iterator[None]:
    """``page_role`` marker が付いた test の終了直前に axe-core を実行する。

    ``page`` fixture を **要求している test のみ** 対象。autouse fixture が
    無条件に ``page`` を要求すると、pytest-playwright が全 test を browser
    parametrize してしまうため、ここでは ``request.fixturenames`` を見て
    必要な test だけ取得する。
    """
    yield

    # ``page`` を要求していない (= browser を使わない) test では何もしない。
    # これにより pure pytest test の挙動に影響を与えない。
    if "page" not in request.fixturenames:
        return
    if "ndf_evidence" not in request.fixturenames:
        return

    config: Config | None = request.getfixturevalue("_ndf_config_optional")
    if config is None or not config.a11y.enabled:
        return
    page_roles = _page_roles_from_marker(request.node)
    if not page_roles:
        return
    if not a11y_mod.should_auto_scan(
        page_roles, auto_roles=frozenset(config.a11y.auto_roles)
    ):
        return

    ndf_evidence: NdfEvidence = request.getfixturevalue("ndf_evidence")

    if not a11y_mod.is_available():
        ndf_evidence.log_lines.append(
            "[a11y autouse] axe-playwright-python 未インストール — SKIP"
        )
        return

    page = request.getfixturevalue("page")
    try:
        if page.is_closed():
            return
    except Exception:
        return

    violations = a11y_mod.scan_page(page, tags=tuple(config.a11y.tags))
    ndf_evidence.axe_violations.extend(violations)
    if not violations:
        return

    impacts = Counter(v.get("impact") or "unknown" for v in violations)
    impact_summary = ", ".join(f"{k}={n}" for k, n in impacts.most_common())
    ndf_evidence.log_lines.append(
        f"[a11y autouse] {len(violations)} violations: {impact_summary}"
    )

    if config.a11y.fail_on_violations:
        pytest.fail(
            f"[a11y] {len(violations)} 件の axe-core 違反 "
            f"[{impact_summary}]: "
            + ", ".join(
                f"{v.get('id')}({v.get('impact', '?')})" for v in violations[:5]
            )
        )
