"""record_to_yaml.parse_codegen が Playwright codegen Python 出力を新スキーマに変換できることをテストする。"""

from __future__ import annotations

import yaml

from record_to_yaml import parse_codegen, to_yaml


_CODEGEN_SAMPLE = """\
import re
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://example.com/login")
    page.get_by_label("Email").fill("user@example.com")
    page.get_by_label("Password").fill("secret")
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("link", name="Logout").click()
"""


class TestParseCodegen:
    def test_extracts_main_actions(self):
        steps = parse_codegen(_CODEGEN_SAMPLE)
        kinds = [s["kind"] for s in steps]
        # goto + 2 fill + 2 click を抽出
        assert kinds.count("goto") == 1
        assert kinds.count("fill") == 2
        assert kinds.count("click") == 2

    def test_goto_extracts_path_only(self):
        steps = parse_codegen(_CODEGEN_SAMPLE)
        goto = next(s for s in steps if s["kind"] == "goto")
        assert goto["path"] == "/login"

    def test_fill_extracts_label_and_value(self):
        steps = parse_codegen(_CODEGEN_SAMPLE)
        email_fill = next(s for s in steps if s["kind"] == "fill" and s["value"] == "user@example.com")
        assert email_fill["locator"] == {"label": "Email"}

    def test_click_extracts_role_and_name(self):
        steps = parse_codegen(_CODEGEN_SAMPLE)
        signin = next(s for s in steps if s["kind"] == "click" and s["locator"].get("name") == "Sign in")
        assert signin["locator"] == {"role": "button", "name": "Sign in"}


class TestToYaml:
    def test_round_trip(self):
        steps = parse_codegen(_CODEGEN_SAMPLE)
        text = to_yaml(
            test_id="TC-AUTH-recorded-001",
            title="Recorded login",
            role="user",
            page_role="auth",
            steps=steps,
        )
        loaded = yaml.safe_load(text)
        assert loaded["id"] == "TC-AUTH-recorded-001"
        assert loaded["page_role"] == "auth"
        assert loaded["type"] == "playwright"
        assert len(loaded["steps"]) == len(steps)
        assert loaded["steps"][0]["kind"] == "goto"
