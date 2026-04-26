"""CWV fixture: ``page_role`` marker に応じた Core Web Vitals 自動計測。

PLAN17 Task 4: ``@pytest.mark.page_role("dashboard")`` 等が付与された test の
終了直前に LCP / CLS / TTFB / longest_task を計測。
"""

from __future__ import annotations

from typing import Iterator

import pytest

from scenario_test import cwv as cwv_mod
from scenario_test.config import Config
from scenario_test.fixtures.evidence import NdfEvidence


def _page_roles_from_marker(item) -> list[str]:
    roles: list[str] = []
    for marker in item.iter_markers(name="page_role"):
        for arg in marker.args:
            if isinstance(arg, str):
                roles.append(arg)
            elif isinstance(arg, (list, tuple)):
                roles.extend(str(a) for a in arg)
    return roles


@pytest.fixture()
def ndf_cwv_measure(page, ndf_evidence: NdfEvidence, _ndf_config_optional):
    """明示呼び出し用: ``metrics = ndf_cwv_measure()`` で 1 度計測。"""
    config: Config | None = _ndf_config_optional

    def _measure(*, observe_ms: int | None = None) -> dict[str, float]:
        ms = (
            int(observe_ms)
            if observe_ms is not None
            else (
                int(config.cwv.observe_ms)
                if config is not None
                else 5000
            )
        )
        metrics = cwv_mod.measure_page(page, observe_ms=ms)
        ndf_evidence.cwv_metrics.update(metrics)
        ndf_evidence.cwv_passed = cwv_mod.passed(ndf_evidence.cwv_metrics)
        return metrics

    return _measure


@pytest.fixture(autouse=True)
def _ndf_cwv_autouse(request) -> Iterator[None]:
    """``page_role`` marker が付いた test の終了直前に CWV 計測を行う。

    a11y と同じく ``page`` fixture を要求している test のみ対象。
    """
    yield

    if "page" not in request.fixturenames:
        return
    if "ndf_evidence" not in request.fixturenames:
        return

    config: Config | None = request.getfixturevalue("_ndf_config_optional")
    if config is None or not config.cwv.enabled:
        return
    page_roles = _page_roles_from_marker(request.node)
    if not page_roles:
        return
    if not cwv_mod.should_auto_measure(
        page_roles, auto_roles=frozenset(config.cwv.auto_roles)
    ):
        return

    ndf_evidence: NdfEvidence = request.getfixturevalue("ndf_evidence")
    page = request.getfixturevalue("page")

    try:
        if page.is_closed():
            return
    except Exception:
        return

    metrics = cwv_mod.measure_page(page, observe_ms=int(config.cwv.observe_ms))
    ndf_evidence.cwv_metrics.update(metrics)
    ndf_evidence.cwv_passed = cwv_mod.passed(ndf_evidence.cwv_metrics)

    detail = ", ".join(
        f"{k}={v:.1f}({cwv_mod.judge(k, v)})" for k, v in metrics.items()
    ) or "no metrics collected"
    ndf_evidence.log_lines.append(f"[cwv autouse] {detail}")

    if not ndf_evidence.cwv_passed and config.cwv.fail_on_poor:
        pytest.fail(f"[cwv] poor metric を検出: {detail}")
