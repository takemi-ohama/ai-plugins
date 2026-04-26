"""scenario_test/testcase.py の `parse_filter` と nav_helpers.slug_for / detect_body_errors の単体テスト。"""

from __future__ import annotations

from scenario_test.nav_helpers import detect_body_errors, slug_for
from scenario_test.testcase import parse_filter


class TestParseFilter:
    def test_empty(self):
        assert parse_filter("") == {}

    def test_single_key(self):
        assert parse_filter("phase:50,51") == {"phase": ["50", "51"]}

    def test_multi_key_space_separated(self):
        assert parse_filter("phase:50 role:user") == {"phase": ["50"], "role": ["user"]}

    def test_page_role_filter(self):
        # Min-3 で SKILL.md に追加した使い方
        assert parse_filter("page_role:cart,checkout") == {
            "page_role": ["cart", "checkout"],
        }

    def test_unknown_token_silently_ignored(self):
        # `_FILTER_RE` にマッチしない token は無視される (壊れた filter で全件落ちないため)
        assert parse_filter("garbage no_colon_here") == {}

    def test_comma_in_lieu_of_space(self):
        assert parse_filter("id:TC-50-01,TC-50-02") == {
            "id": ["TC-50-01", "TC-50-02"],
        }


class TestSlugFor:
    def test_root_path(self):
        assert slug_for("/") == "root"

    def test_nested_path(self):
        assert slug_for("/items/edit") == "items_edit"

    def test_strip_extension(self):
        assert slug_for("/items/show.php", strip_extensions=[".php"]) == "items_show"

    def test_query_capture(self):
        assert slug_for(
            "/items.php?Cmd=Edit",
            strip_extensions=[".php"],
            query_capture_re=r"Cmd=(\w+)",
        ) == "items-Edit"


class TestDetectBodyErrors:
    def test_empty_body(self):
        assert detect_body_errors("") == (False, False, "")

    def test_no_patterns_means_no_detection(self):
        # config.body_check 未設定でも安全に通る
        assert detect_body_errors("hello world") == (False, False, "")

    def test_fatal_pattern_anywhere(self):
        body = "x" * 1000 + " Fatal error: somewhere"
        fatal, nf, warn = detect_body_errors(body, fatal_patterns=["Fatal error"])
        assert fatal is True
        assert nf is False
        assert warn == ""

    def test_warning_only_in_head(self):
        # warning は先頭 head_chars 文字内のみで判定
        body = ("a" * 500) + "Warning: late"
        _, _, warn = detect_body_errors(
            body, warning_patterns=["Warning:"], head_chars=300,
        )
        assert warn == ""  # 先頭 300 文字に無いので非検出

    def test_warning_in_head_detected(self):
        body = "Warning: head\n" + ("z" * 1000)
        _, _, warn = detect_body_errors(body, warning_patterns=["Warning:"])
        assert warn == "Warning:"

    def test_not_found_string(self):
        _, nf, _ = detect_body_errors(
            "<h1>File not found</h1>", not_found_strings=["File not found"],
        )
        assert nf is True
