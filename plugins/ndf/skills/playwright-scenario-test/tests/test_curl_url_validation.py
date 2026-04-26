"""scenario_test/curl_executor.py の URL 検査関数の単体テスト。

amazon-q-developer bot の指摘 + Maj-8 の追加検査を回帰テストで固定する。
"""

from __future__ import annotations

import pytest

from scenario_test.curl_executor import _validate_base_url_scheme, _validate_url_part


class TestValidateUrlPart:
    @pytest.mark.parametrize("clean", [
        "https://example.com",
        "/items?id=1",
        "/",
        "%2Fencoded%20stuff",
    ])
    def test_clean_url_passes(self, clean):
        # 例外を投げない
        _validate_url_part(clean, "label")

    @pytest.mark.parametrize("ctrl", [
        "https://example.com\rINJECT",
        "https://example.com\nLine2",
        "/path\x00trunc",
        "/with\ttab",
    ])
    def test_control_chars_rejected(self, ctrl):
        with pytest.raises(ValueError, match="制御文字"):
            _validate_url_part(ctrl, "label")

    @pytest.mark.parametrize("bad", [
        "/path with space",
        '/path"quoted"',
    ])
    def test_space_or_quote_rejected(self, bad):
        with pytest.raises(ValueError):
            _validate_url_part(bad, "label")


class TestValidateBaseUrlScheme:
    @pytest.mark.parametrize("ok", [
        "http://example.com",
        "https://example.com/",
        "https://sub.example.com:8443/path",
    ])
    def test_http_https_pass(self, ok):
        _validate_base_url_scheme(ok)

    @pytest.mark.parametrize("bad", [
        "javascript:alert(1)",
        "data:text/html,<h1>x</h1>",
        "file:///etc/passwd",
        "gopher://evil.example.com",
        "//schemeless.example.com",  # urlparse → scheme=''
        "example.com/path",          # urlparse → scheme=''
    ])
    def test_unknown_scheme_rejected(self, bad):
        with pytest.raises(ValueError, match="scheme"):
            _validate_base_url_scheme(bad)
