"""body_check fixture: ``page.on("response", ...)`` でレスポンス本文を監視し、
PHP / SSR が HTML 本文に出力したエラー文字列を検出する (v0.4.0)。

config.yaml の ``body_check.enabled: true`` で opt-in 有効化。``page`` fixture を
要求している test に限り autouse で listener を attach する (a11y autouse と
同じ guard 戦略)。``@pytest.mark.no_body_check`` を test に付ければ個別に
opt-out 可能。

backward compat:
- ``body_check.enabled`` の default は False (config.py)
- 既存利用者は config に何も書かなければ従来挙動 (検出ロジックなし)
"""

from __future__ import annotations

import json
from typing import Any, Iterator

import pytest

from scenario_test.body_check import (
    is_html_response,
    scan_body,
)
from scenario_test.config import BodyCheckConfig, Config
from scenario_test.fixtures.evidence import NdfEvidence


def _build_response_handler(cfg: BodyCheckConfig, ev: NdfEvidence):
    """``page.on("response", ...)`` 用の handler を closure として作る。

    listener 内で発生する例外は test 失敗には伝播させず ``ev.log_lines`` に
    記録するに留める (a11y / pageerror listener と同じ防御方針)。
    """
    fatal = tuple(cfg.fatal_patterns)
    warn = tuple(cfg.warning_patterns)
    not_found = tuple(cfg.not_found_patterns)
    head_bytes = int(cfg.warning_head_bytes)

    def _on_response(response) -> None:
        try:
            headers = response.headers or {}
            if not is_html_response(headers.get("content-type") or headers.get("Content-Type")):
                return
            try:
                body = response.text()
            except Exception:
                # navigation 中の中断 / closed context などで text() が失敗するケース
                return
            violations = scan_body(
                body,
                response.url,
                fatal_patterns=fatal,
                warning_patterns=warn,
                warning_head_bytes=head_bytes,
                not_found_patterns=not_found,
            )
            for v in violations:
                ev.body_check_violations.append(v.to_dict())
        except Exception as exc:  # pragma: no cover - listener 内で test を落とさない
            ev.log_lines.append(f"[body_check listener] {exc}")

    return _on_response


def _write_jsonl(ev: NdfEvidence) -> None:
    """1 violation = 1 行で ``case_dir/body_check.jsonl`` に書き出す。"""
    if not ev.body_check_violations:
        return
    try:
        path = ev.case_dir / "body_check.jsonl"
        with path.open("w", encoding="utf-8") as fp:
            for v in ev.body_check_violations:
                fp.write(json.dumps(v, ensure_ascii=False) + "\n")
    except Exception as exc:  # pragma: no cover
        ev.log_lines.append(f"[body_check] jsonl write failed: {exc}")


def _format_violation_summary(violations: list[dict[str, Any]], limit: int = 5) -> str:
    """``pytest.fail`` メッセージ用の短いサマリ文字列。"""
    parts: list[str] = []
    for v in violations[:limit]:
        url = v.get("url", "?")
        cat = v.get("category", "?")
        pat = v.get("pattern", "?")
        parts.append(f"{cat}:{pat!r}@{url}")
    if len(violations) > limit:
        parts.append(f"... (+{len(violations) - limit} more)")
    return "; ".join(parts)


@pytest.fixture()
def ndf_body_check_scan(page, ndf_evidence: NdfEvidence, _ndf_config_optional):
    """明示呼び出し用: ``violations = ndf_body_check_scan()`` で現在の page 本文を 1 度スキャン。

    autouse 経路を使わず、特定タイミング (例: フォーム送信後の 200 応答) で
    本文を再評価したい場合の helper。
    """
    config: Config | None = _ndf_config_optional

    def _scan() -> list[dict[str, Any]]:
        if config is None or not config.body_check.enabled:
            return []
        try:
            body = page.content()
        except Exception as exc:
            ndf_evidence.log_lines.append(f"[body_check] page.content() failed: {exc}")
            return []
        violations = scan_body(
            body,
            page.url,
            fatal_patterns=config.body_check.fatal_patterns,
            warning_patterns=config.body_check.warning_patterns,
            warning_head_bytes=config.body_check.warning_head_bytes,
            not_found_patterns=config.body_check.not_found_patterns,
        )
        as_dicts = [v.to_dict() for v in violations]
        ndf_evidence.body_check_violations.extend(as_dicts)
        return as_dicts

    return _scan


@pytest.fixture(autouse=True)
def _ndf_body_check_autouse(request) -> Iterator[None]:
    """``page`` を要求する test に限り、HTML response への body_check を自動実行する。

    a11y autouse と同じガード戦略:
    - ``page`` を fixturename に持たない test は対象外 (browser を起動させない)
    - ``ndf_evidence`` を持たない test も対象外
    - config.body_check.enabled が False なら何もしない
    - ``@pytest.mark.no_body_check`` が付いている test は skip

    teardown 時に違反があれば ``case_dir/body_check.jsonl`` に書き出し、
    ``fail_on_match`` が True なら ``pytest.fail`` で test を失敗させる。
    """
    if (
        "page" not in request.fixturenames
        or "ndf_evidence" not in request.fixturenames
    ):
        yield
        return

    config: Config | None = request.getfixturevalue("_ndf_config_optional")
    if config is None or not config.body_check.enabled:
        yield
        return

    if request.node.get_closest_marker("no_body_check") is not None:
        yield
        return

    page = request.getfixturevalue("page")
    ev: NdfEvidence = request.getfixturevalue("ndf_evidence")
    handler = _build_response_handler(config.body_check, ev)

    try:
        page.on("response", handler)
    except Exception as exc:
        ev.log_lines.append(f"[body_check] page.on attach failed: {exc}")
        yield
        return

    try:
        yield
    finally:
        try:
            page.remove_listener("response", handler)
        except Exception:
            # page が既に閉じられている場合などは黙殺
            pass

        if not ev.body_check_violations:
            return

        _write_jsonl(ev)

        ev.log_lines.append(
            f"[body_check] {len(ev.body_check_violations)} 件の違反: "
            + _format_violation_summary(ev.body_check_violations)
        )

        if config.body_check.fail_on_match:
            pytest.fail(
                f"[body_check] {len(ev.body_check_violations)} 件の本文エラーを検出: "
                + _format_violation_summary(ev.body_check_violations)
            )
