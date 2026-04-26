"""YAML step kind → Playwright Locator/expect API への dispatcher。

`Step` (testcase.py) を受け取り、Playwright `Page` 上で実行して `StepRecord`
(成功/失敗 + detail) を返す。すべての assertion は web-first の `expect()` を
唯一の手段として使うため、auto-waiting と flake 耐性を Playwright に委ねられる。

各 step kind の dispatch は単一 dict (`_DISPATCH`) でテーブル駆動になっており、
新 kind を追加したいときは `_handle_*` 関数を実装して dict に登録するだけで済む。
"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass
from typing import Callable

from playwright.sync_api import Locator, Page, expect

from scenario_test.testcase import LocatorSpec, Step, StepRecord


# --- Locator 構築 ---------------------------------------------------

def build_locator(page: Page, spec: LocatorSpec) -> Locator:
    """`LocatorSpec` (YAML 由来) から Playwright Locator を組み立てる。"""
    kind = spec.kind
    if kind == "role":
        loc = page.get_by_role(spec.selector, name=spec.name, exact=spec.exact)  # type: ignore[arg-type]
    elif kind == "label":
        loc = page.get_by_label(spec.selector, exact=spec.exact)
    elif kind == "placeholder":
        loc = page.get_by_placeholder(spec.selector, exact=spec.exact)
    elif kind == "text":
        loc = page.get_by_text(spec.selector, exact=spec.exact)
    elif kind == "alt":
        loc = page.get_by_alt_text(spec.selector, exact=spec.exact)
    elif kind == "title":
        loc = page.get_by_title(spec.selector, exact=spec.exact)
    elif kind == "testid":
        loc = page.get_by_test_id(spec.selector)
    elif kind == "css":
        loc = page.locator(spec.selector)
    elif kind == "xpath":
        loc = page.locator(f"xpath={spec.selector}")
    else:
        raise ValueError(f"未対応の locator kind: {kind!r}")
    if spec.nth is not None:
        loc = loc.nth(spec.nth)
    return loc


# --- 変数展開 -------------------------------------------------------

_VAR_RE = _re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def expand_vars(value: str | None, vars_: dict[str, str]) -> str | None:
    """`{var_name}` 形式の placeholder を `vars_` 辞書で置換する。

    extract step で保存された値を後続 step の path / value / text に注入する。
    マッチしない placeholder はそのまま残す (typo 早期検出のため)。
    """
    if value is None:
        return None
    return _VAR_RE.sub(lambda m: vars_.get(m.group(1), m.group(0)), value)


# --- 結果の表現 -----------------------------------------------------

@dataclass
class StepContext:
    """dispatch 関数間で共有する実行コンテキスト。"""
    page: Page
    base_url: str
    nav_vars: dict[str, str]
    default_timeout_ms: int


# --- 各 step kind handler -------------------------------------------

def _handle_goto(step: Step, ctx: StepContext) -> str:
    path = expand_vars(step.path, ctx.nav_vars) or "/"
    url = path if path.startswith("http") else f"{ctx.base_url}{path}"
    response = ctx.page.goto(url, timeout=step.timeout_ms or ctx.default_timeout_ms)
    code = response.status if response else 0
    if step.expect_status is not None and code != step.expect_status:
        raise AssertionError(f"goto: HTTP {code} != 期待 {step.expect_status} ({url})")
    return f"goto {url} → {code}"


def _handle_click(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    loc.click(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"click {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_fill(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    value = expand_vars(step.value, ctx.nav_vars) or ""
    loc.fill(value, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"fill {step.locator.describe()} = {value!r}"  # type: ignore[union-attr]


def _handle_select(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    value = expand_vars(step.value, ctx.nav_vars) or ""
    loc.select_option(value=value, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"select {step.locator.describe()} = {value!r}"  # type: ignore[union-attr]


def _handle_check(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    loc.check(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"check {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_uncheck(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    loc.uncheck(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"uncheck {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_press(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    key = step.value or ""
    loc.press(key, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"press {step.locator.describe()} key={key!r}"  # type: ignore[union-attr]


def _handle_hover(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    loc.hover(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"hover {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_extract(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    text = loc.first.text_content(timeout=step.timeout_ms or ctx.default_timeout_ms) or ""
    text = text.strip()
    ctx.nav_vars[step.var] = text  # type: ignore[index]
    return f"extract {step.var}={text!r} from {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_wait_for(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    loc.wait_for(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"wait_for {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_wait_ms(step: Step, ctx: StepContext) -> str:
    ms = step.ms or 0
    ctx.page.wait_for_timeout(ms)
    return f"wait_ms {ms}"


def _handle_expect_visible(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    expect(loc).to_be_visible(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_visible {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_expect_hidden(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    expect(loc).to_be_hidden(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_hidden {step.locator.describe()}"  # type: ignore[union-attr]


def _handle_expect_text(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    text = expand_vars(step.text, ctx.nav_vars) or ""
    expect(loc).to_contain_text(text, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_text {step.locator.describe()} contains {text!r}"  # type: ignore[union-attr]


def _handle_expect_no_text(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    text = expand_vars(step.text, ctx.nav_vars) or ""
    expect(loc).not_to_contain_text(text, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_no_text {step.locator.describe()} ∌ {text!r}"  # type: ignore[union-attr]


def _handle_expect_url(step: Step, ctx: StepContext) -> str:
    needle = expand_vars(step.contains, ctx.nav_vars) or expand_vars(step.path, ctx.nav_vars) or ""
    expect(ctx.page).to_have_url(_re.compile(_re.escape(needle)),
                                 timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_url contains {needle!r}"


def _handle_expect_count(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    expect(loc).to_have_count(step.count, timeout=step.timeout_ms or ctx.default_timeout_ms)  # type: ignore[arg-type]
    return f"expect_count {step.locator.describe()} == {step.count}"  # type: ignore[union-attr]


def _handle_expect_aria_snapshot(step: Step, ctx: StepContext) -> str:
    loc = build_locator(ctx.page, step.locator)  # type: ignore[arg-type]
    snapshot = expand_vars(step.text, ctx.nav_vars) or ""
    expect(loc).to_match_aria_snapshot(snapshot,
                                       timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"expect_aria_snapshot {step.locator.describe()}"  # type: ignore[union-attr]


_DISPATCH: dict[str, Callable[[Step, StepContext], str]] = {
    "goto": _handle_goto,
    "click": _handle_click,
    "fill": _handle_fill,
    "select": _handle_select,
    "check": _handle_check,
    "uncheck": _handle_uncheck,
    "press": _handle_press,
    "hover": _handle_hover,
    "extract": _handle_extract,
    "wait_for": _handle_wait_for,
    "wait_ms": _handle_wait_ms,
    "expect_visible": _handle_expect_visible,
    "expect_hidden": _handle_expect_hidden,
    "expect_text": _handle_expect_text,
    "expect_no_text": _handle_expect_no_text,
    "expect_url": _handle_expect_url,
    "expect_count": _handle_expect_count,
    "expect_aria_snapshot": _handle_expect_aria_snapshot,
}


def supported_kinds() -> list[str]:
    """登録済 step kind の一覧を返す (テスト / `--list-kinds` 等で利用)。"""
    return sorted(_DISPATCH)


def execute_step(step: Step, ctx: StepContext) -> StepRecord:
    """1 つの Step を実行し StepRecord に変換する。

    例外は捕捉して `ok=False, detail=traceback summary` で返す。
    呼び出し側は StepRecord.ok だけ見れば pass/fail 判定できる。
    """
    handler = _DISPATCH.get(step.kind)
    if handler is None:
        return StepRecord(name=step.name, ok=False, detail=f"未対応の step kind: {step.kind}")
    try:
        detail = handler(step, ctx)
        return StepRecord(name=step.name, ok=True, detail=detail)
    except Exception as exc:
        return StepRecord(name=step.name, ok=False, detail=f"{type(exc).__name__}: {exc}")
