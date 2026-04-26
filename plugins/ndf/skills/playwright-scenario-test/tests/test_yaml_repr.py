"""scripts/generate_test_plan.py の `_yaml_repr` / `_yaml_dump` の単体テスト。

Maj-2 で冗長分岐を整理した後の挙動を固定し、Codex レビュー指摘の
「`'01'` / `'true'` / `'null'` / 郵便番号風数値が safe_load 後に変型する」
回帰を将来の変更で起こさないことを保証する。
"""

from __future__ import annotations

import yaml

from generate_test_plan import _yaml_dump, _yaml_repr


class TestYamlRepr:
    """`_yaml_repr` の型保持を中心に検証する。"""

    def test_none(self):
        assert _yaml_repr(None) == "null"

    def test_bool(self):
        assert _yaml_repr(True) == "true"
        assert _yaml_repr(False) == "false"

    def test_int_float(self):
        assert _yaml_repr(42) == "42"
        assert _yaml_repr(1.5) == "1.5"

    def test_plain_string_unquoted(self):
        # 安全な英字列 / 日本語はベタ書きで OK
        assert _yaml_repr("hello") == "hello"
        assert _yaml_repr("テスト") == "テスト"

    def test_reserved_words_quoted(self):
        # YAML 1.1/1.2 で bool/null として解釈されるトークンは quote 必須
        for s in ("true", "false", "null", "yes", "no", "on", "off", "~"):
            out = _yaml_repr(s)
            assert out.startswith('"') and yaml.safe_load(out) == s, f"{s!r} → {out!r}"

    def test_zero_padded_number_quoted(self):
        # '01' は素のままだと int 1 (or octal) として parse されてしまう
        out = _yaml_repr("01")
        assert out.startswith('"')
        assert yaml.safe_load(out) == "01"

    def test_postal_code_like_number_quoted(self):
        out = _yaml_repr("12345")
        assert out.startswith('"')
        assert yaml.safe_load(out) == "12345"

    def test_hex_literal_quoted(self):
        out = _yaml_repr("0xDEADBEEF")
        assert out.startswith('"')
        assert yaml.safe_load(out) == "0xDEADBEEF"

    def test_string_with_special_chars(self):
        # コロンや # は YAML 構文に干渉するので quote 必須
        for s in ("a: b", "x#y", "[item]", "{k:v}"):
            out = _yaml_repr(s)
            assert out.startswith('"')
            assert yaml.safe_load(out) == s

    def test_string_with_leading_trailing_space(self):
        out = _yaml_repr("  spaced  ")
        assert out.startswith('"')
        assert yaml.safe_load(out) == "  spaced  "

    def test_empty_string_quoted(self):
        out = _yaml_repr("")
        assert out == '""'
        assert yaml.safe_load(out) == ""


class TestYamlDumpRoundtrip:
    """`_yaml_dump` 出力が `yaml.safe_load` で同値に round-trip すること。"""

    def test_dict_with_problematic_strings(self):
        data = {
            "id": "01",
            "code": "12345",
            "flag_str": "true",
            "title": "Hello: World",
        }
        text = _yaml_dump(data)
        loaded = yaml.safe_load(text)
        assert loaded == data

    def test_nested_list(self):
        data = {
            "items": [
                {"name": "01", "value": 1},
                {"name": "true", "value": 2},
            ],
        }
        text = _yaml_dump(data)
        loaded = yaml.safe_load(text)
        assert loaded == data
