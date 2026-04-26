"""scenario_test/testcase.py の `parse_filter` と generate_test_plan._slugify / _default_test_id の単体テスト。"""

from __future__ import annotations

from generate_test_plan import _default_test_id, _slugify
from scenario_test.testcase import parse_filter


class TestParseFilter:
    def test_empty(self):
        assert parse_filter("") == {}

    def test_single_key(self):
        assert parse_filter("phase:50,51") == {"phase": ["50", "51"]}

    def test_multi_key_space_separated(self):
        assert parse_filter("phase:50 role:user") == {"phase": ["50"], "role": ["user"]}

    def test_page_role_filter(self):
        assert parse_filter("page_role:cart,checkout") == {
            "page_role": ["cart", "checkout"],
        }

    def test_unknown_token_silently_ignored(self):
        assert parse_filter("garbage no_colon_here") == {}

    def test_comma_in_lieu_of_space(self):
        assert parse_filter("id:TC-50-01,TC-50-02") == {
            "id": ["TC-50-01", "TC-50-02"],
        }


class TestSlugify:
    def test_basic(self):
        assert _slugify("Hello World") == "hello-world"

    def test_special_chars_to_dash(self):
        assert _slugify("foo/bar?baz=1") == "foo-bar-baz-1"

    def test_truncation(self):
        # Min-2 で 60 → 80 字に拡大
        s = "a" * 200
        assert len(_slugify(s)) == 80


class TestDefaultTestId:
    """`_default_test_id` (Min-2 衝突回避) の振る舞いを固定する。"""

    def test_distinct_paths_yield_distinct_ids(self):
        # 旧実装は末尾セグメントだけ見ていたため衝突していたケース
        a = _default_test_id("edit", "https://example.com/items/edit/1")
        b = _default_test_id("edit", "https://example.com/users/edit/1")
        assert a != b
        # 末尾 6 字は sha1 hash なので URL ごとにユニーク
        assert a.split("-")[-1] != b.split("-")[-1]

    def test_id_includes_role_and_path(self):
        tid = _default_test_id("form", "https://example.com/contact")
        assert tid.startswith("TC-FORM-")
        assert "contact" in tid

    def test_id_is_filename_safe(self):
        tid = _default_test_id("list", "https://example.com/items?page=1&sort=desc")
        # ASCII 識別子 + ハイフンのみで構成されるはず
        for ch in tid:
            assert ch.isalnum() or ch == "-", f"非 filename safe 文字: {ch!r} in {tid}"
