"""新スキーマ (locator-first) の Step / LocatorSpec バリデーションを固定する。

旧 `path/method/data` 構造を完全に置き換えたため、既知 step kind / locator kind
の網羅と、欠落フィールド検出の境界値を厳密にテストする。
"""

from __future__ import annotations

import pytest

from scenario_test.testcase import KNOWN_STEP_KINDS, LocatorSpec, Step


class TestLocatorSpec:
    def test_role_with_name(self):
        spec = LocatorSpec.from_raw({"role": "button", "name": "保存"})
        assert spec.kind == "role"
        assert spec.selector == "button"
        assert spec.name == "保存"

    def test_label(self):
        spec = LocatorSpec.from_raw({"label": "メールアドレス"})
        assert spec.kind == "label"
        assert spec.selector == "メールアドレス"

    def test_testid(self):
        spec = LocatorSpec.from_raw({"testid": "submit-btn"})
        assert spec.kind == "testid"
        assert spec.selector == "submit-btn"

    def test_css_fallback(self):
        spec = LocatorSpec.from_raw({"css": ".alert-danger"})
        assert spec.kind == "css"

    def test_multiple_kinds_rejected(self):
        # codex Min-1: 複数 selector kind を黙って優先順で握りつぶさず ValueError
        with pytest.raises(ValueError, match="locator は 1 種類のみ"):
            LocatorSpec.from_raw({"role": "button", "css": ".btn"})

    def test_no_locator_raises(self):
        with pytest.raises(ValueError, match="有効な指定子"):
            LocatorSpec.from_raw({"foo": "bar"})

    def test_describe_includes_kind_and_name(self):
        spec = LocatorSpec.from_raw({"role": "button", "name": "送信"})
        s = spec.describe()
        assert "role=" in s and "送信" in s


class TestStep:
    def test_goto_minimal(self):
        s = Step.from_raw({"kind": "goto", "name": "open", "path": "/items"})
        assert s.kind == "goto"
        assert s.path == "/items"
        assert s.locator is None

    def test_goto_requires_path(self):
        with pytest.raises(ValueError, match="path"):
            Step.from_raw({"kind": "goto", "name": "x"})

    def test_click_requires_locator(self):
        with pytest.raises(ValueError, match="locator"):
            Step.from_raw({"kind": "click", "name": "x"})

    def test_fill_requires_value(self):
        with pytest.raises(ValueError, match="value"):
            Step.from_raw({"kind": "fill", "name": "x", "locator": {"label": "y"}})

    def test_extract_requires_var(self):
        with pytest.raises(ValueError, match="var"):
            Step.from_raw({"kind": "extract", "name": "x", "locator": {"label": "y"}})

    def test_expect_text_requires_text(self):
        with pytest.raises(ValueError, match="text"):
            Step.from_raw({
                "kind": "expect_text", "name": "x", "locator": {"label": "y"},
            })

    def test_expect_url_requires_contains_or_path(self):
        with pytest.raises(ValueError, match="contains"):
            Step.from_raw({"kind": "expect_url", "name": "x"})

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="未知の step kind"):
            Step.from_raw({"kind": "navigate", "name": "old schema"})

    def test_all_known_kinds_have_path(self):
        # 既知 kind のリストが空でないことの sanity
        assert len(KNOWN_STEP_KINDS) >= 17

    def test_known_kinds_match_dispatcher(self):
        # Min-8: KNOWN_STEP_KINDS と locator_steps._DISPATCH のキー集合が完全一致
        # することを保証する (片方の追加忘れを CI で検出)。
        from scenario_test.locator_steps import supported_kinds
        assert set(KNOWN_STEP_KINDS) == set(supported_kinds()), (
            "KNOWN_STEP_KINDS と _DISPATCH のキー集合が不一致 — "
            "片方への追加 / 削除を相手にも反映してください"
        )

    def test_full_fill_step(self):
        s = Step.from_raw({
            "kind": "fill",
            "name": "メール入力",
            "locator": {"label": "メールアドレス"},
            "value": "test@example.com",
            "timeout_ms": 5000,
        })
        assert s.kind == "fill"
        assert s.value == "test@example.com"
        assert s.timeout_ms == 5000
        assert s.locator and s.locator.kind == "label"
