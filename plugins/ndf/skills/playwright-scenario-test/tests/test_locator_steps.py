"""locator_steps のテーブル駆動 dispatch + 変数展開のテスト。

実 Playwright は使わず、Page を Mock 化して dispatch が正しい API を呼ぶことを
確認する。Locator 構築自体 (build_locator) は実 Playwright Page を使うと
セットアップが重いため Mock のみで済ませる。
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scenario_test.locator_steps import (
    StepContext,
    execute_step,
    expand_vars,
    supported_kinds,
)
from scenario_test.testcase import Step


class TestExpandVars:
    def test_no_placeholder(self):
        assert expand_vars("hello", {}) == "hello"

    def test_simple_substitution(self):
        assert expand_vars("/items/{id}", {"id": "42"}) == "/items/42"

    def test_missing_var_left_intact(self):
        # typo 早期検出のため未定義の placeholder はそのまま残す
        assert expand_vars("/items/{missing}", {}) == "/items/{missing}"

    def test_none_returns_none(self):
        assert expand_vars(None, {"x": "y"}) is None


class TestSupportedKinds:
    def test_includes_core_kinds(self):
        kinds = set(supported_kinds())
        for required in (
            "goto", "click", "fill", "select", "press", "extract",
            "expect_visible", "expect_url", "expect_no_text", "expect_aria_snapshot",
        ):
            assert required in kinds


class TestExecuteStepDispatch:
    """主要 step kind が成功時に StepRecord(ok=True) を返すことを確認する。"""

    def _make_ctx(self) -> StepContext:
        page = MagicMock()
        # build_locator が page.locator/get_by_* を返すので all-in-one Mock
        page.locator.return_value = MagicMock()
        page.get_by_role.return_value = MagicMock()
        page.get_by_label.return_value = MagicMock()
        page.get_by_text.return_value = MagicMock()
        page.get_by_test_id.return_value = MagicMock()
        page.get_by_placeholder.return_value = MagicMock()
        page.get_by_alt_text.return_value = MagicMock()
        page.get_by_title.return_value = MagicMock()
        # goto 用に response mock
        resp = MagicMock()
        resp.status = 200
        page.goto.return_value = resp
        page.url = "https://example.com/items"
        return StepContext(
            page=page, base_url="https://example.com", nav_vars={},
            default_timeout_ms=5000,
        )

    def test_goto_success(self):
        ctx = self._make_ctx()
        step = Step.from_raw({
            "kind": "goto", "name": "open", "path": "/items", "expect_status": 200,
        })
        rec = execute_step(step, ctx)
        assert rec.ok, rec.detail
        ctx.page.goto.assert_called_once()

    def test_goto_status_mismatch_fails(self):
        ctx = self._make_ctx()
        ctx.page.goto.return_value.status = 500
        step = Step.from_raw({
            "kind": "goto", "name": "open", "path": "/items", "expect_status": 200,
        })
        rec = execute_step(step, ctx)
        assert not rec.ok
        assert "AssertionError" in rec.detail or "500" in rec.detail

    def test_click_success(self):
        ctx = self._make_ctx()
        step = Step.from_raw({
            "kind": "click", "name": "保存", "locator": {"role": "button", "name": "保存"},
        })
        rec = execute_step(step, ctx)
        assert rec.ok, rec.detail
        ctx.page.get_by_role.assert_called_once()

    def test_fill_with_var_expansion(self):
        ctx = self._make_ctx()
        ctx.nav_vars["user_id"] = "42"
        step = Step.from_raw({
            "kind": "fill", "name": "id 入力",
            "locator": {"label": "ID"}, "value": "user-{user_id}",
        })
        rec = execute_step(step, ctx)
        assert rec.ok
        # locator.fill("user-42", ...) が呼ばれているはず
        loc = ctx.page.get_by_label.return_value
        loc.fill.assert_called_once()
        called_arg = loc.fill.call_args[0][0]
        assert called_arg == "user-42"

    def test_extract_saves_to_nav_vars(self):
        ctx = self._make_ctx()
        loc = ctx.page.get_by_label.return_value
        loc.first.text_content.return_value = "  TC-001  "
        step = Step.from_raw({
            "kind": "extract", "name": "id 取得",
            "locator": {"label": "ID"}, "var": "extracted_id",
        })
        rec = execute_step(step, ctx)
        assert rec.ok
        assert ctx.nav_vars["extracted_id"] == "TC-001"

    def test_unknown_kind_returns_failed_record(self):
        # Step.from_raw を bypass して未対応 kind を入れる
        # (本来は schema で弾かれるが dispatcher の defensive 動作確認)
        rec = execute_step(
            Step(kind="unknown_kind", name="x"),
            self._make_ctx(),
        )
        assert not rec.ok
        assert "未対応" in rec.detail

    def test_exception_captured_as_failed_record(self):
        ctx = self._make_ctx()
        ctx.page.goto.side_effect = RuntimeError("network down")
        step = Step.from_raw({"kind": "goto", "name": "x", "path": "/items"})
        rec = execute_step(step, ctx)
        assert not rec.ok
        assert "network down" in rec.detail
