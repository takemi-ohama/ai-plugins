"""YAML step kind → Playwright Locator/expect API への dispatcher。

`Step` (testcase.py) を受け取り、Playwright `Page` 上で実行して `StepRecord`
(成功/失敗 + detail) を返す。すべての assertion は web-first の `expect()` を
唯一の手段として使うため、auto-waiting と flake 耐性を Playwright に委ねられる。

各 step kind の dispatch は単一 dict (`_DISPATCH`) でテーブル駆動になっており、
新 kind を追加したいときは `_handle_*` 関数を実装して dict に登録するだけで済む。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

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


def _loc(step: Step) -> LocatorSpec:
    """Step.locator が None でないことを保証して返す narrowing helper。

    Step.from_raw が必須 kind に対して locator を要求するため実行時には到達しないが、
    型チェッカと読み手のために 1 箇所に集約する (Maj-1: `# type: ignore[union-attr]`
    の散在を解消)。
    """
    assert step.locator is not None, f"step kind={step.kind!r} に locator が必要"
    return step.locator


# --- 変数展開 -------------------------------------------------------

_VAR_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def expand_vars(value: str | None, variables: dict[str, str]) -> str | None:
    """`{var_name}` 形式の placeholder を `variables` 辞書で置換する。

    extract step で保存された値を後続 step の path / value / text に注入する。
    マッチしない placeholder はそのまま残す (typo 早期検出のため)。
    """
    if value is None:
        return None
    return _VAR_RE.sub(lambda m: variables.get(m.group(1), m.group(0)), value)


# --- 結果の表現 -----------------------------------------------------

@dataclass
class StepContext:
    """dispatch 関数間で共有する実行コンテキスト。"""
    page: Page
    base_url: str
    nav_vars: dict[str, str]
    default_timeout_ms: int


# --- 各 step kind handler -------------------------------------------

def _is_absolute_http_url(s: str) -> bool:
    """`http(s)://` で始まる絶対 URL かを urlparse で確認する (Maj-3)。"""
    return urlparse(s).scheme in ("http", "https")


def _handle_goto(step: Step, ctx: StepContext) -> str:
    path = expand_vars(step.path, ctx.nav_vars) or "/"
    url = path if _is_absolute_http_url(path) else f"{ctx.base_url}{path}"
    response = ctx.page.goto(url, timeout=step.timeout_ms or ctx.default_timeout_ms)
    code = response.status if response else 0
    if step.expect_status is not None and code != step.expect_status:
        raise AssertionError(f"goto: HTTP {code} != 期待 {step.expect_status} ({url})")
    return f"goto {url} → {code}"


def _handle_click(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    build_locator(ctx.page, spec).click(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"click {spec.describe()}"


def _handle_fill(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    value = expand_vars(step.value, ctx.nav_vars) or ""
    build_locator(ctx.page, spec).fill(value, timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"fill {spec.describe()} = {value!r}"


def _handle_select(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    value = expand_vars(step.value, ctx.nav_vars) or ""
    build_locator(ctx.page, spec).select_option(
        value=value, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"select {spec.describe()} = {value!r}"


def _handle_check(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    build_locator(ctx.page, spec).check(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"check {spec.describe()}"


def _handle_uncheck(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    build_locator(ctx.page, spec).uncheck(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"uncheck {spec.describe()}"


def _handle_press(step: Step, ctx: StepContext) -> str:
    # Maj-2: Step.from_raw が press の value 必須を validation 済み。fallback 不要。
    spec = _loc(step)
    assert step.value is not None, "press に value が必要 (validation バグ?)"
    build_locator(ctx.page, spec).press(
        step.value, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"press {spec.describe()} key={step.value!r}"


def _handle_hover(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    build_locator(ctx.page, spec).hover(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"hover {spec.describe()}"


def _handle_extract(step: Step, ctx: StepContext) -> str:
    # Maj-5: LocatorSpec.nth は build_locator で適用済み。loc.first を強制すると
    # nth 指定が無視されるため、locator 自体に対して text_content を呼ぶ。
    spec = _loc(step)
    assert step.var is not None, "extract に var が必要 (validation バグ?)"
    text = build_locator(ctx.page, spec).text_content(
        timeout=step.timeout_ms or ctx.default_timeout_ms,
    ) or ""
    text = text.strip()
    ctx.nav_vars[step.var] = text
    return f"extract {step.var}={text!r} from {spec.describe()}"


def _handle_wait_for(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    build_locator(ctx.page, spec).wait_for(timeout=step.timeout_ms or ctx.default_timeout_ms)
    return f"wait_for {spec.describe()}"


def _handle_wait_ms(step: Step, ctx: StepContext) -> str:
    ms = step.ms or 0
    ctx.page.wait_for_timeout(ms)
    return f"wait_ms {ms}"


def _handle_expect_visible(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    expect(build_locator(ctx.page, spec)).to_be_visible(
        timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_visible {spec.describe()}"


def _handle_expect_hidden(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    expect(build_locator(ctx.page, spec)).to_be_hidden(
        timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_hidden {spec.describe()}"


def _handle_expect_text(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    text = expand_vars(step.text, ctx.nav_vars) or ""
    expect(build_locator(ctx.page, spec)).to_contain_text(
        text, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_text {spec.describe()} contains {text!r}"


def _handle_expect_no_text(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    text = expand_vars(step.text, ctx.nav_vars) or ""
    expect(build_locator(ctx.page, spec)).not_to_contain_text(
        text, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_no_text {spec.describe()} ∌ {text!r}"


def _handle_expect_url(step: Step, ctx: StepContext) -> str:
    # Maj-4: re.compile(re.escape(...)) は冗長。Playwright `to_have_url` は
    # str を渡すと完全一致なので、`re.compile` で部分一致を表現する必要があるが、
    # `re.escape` を介すれば純粋な substring match と等価。代わりに lambda 述語形式
    # (一致判定を手書き) で部分一致を表現するのが docs の推奨。
    needle = expand_vars(step.contains, ctx.nav_vars) or expand_vars(step.path, ctx.nav_vars) or ""
    expect(ctx.page).to_have_url(
        lambda url: needle in url,
        timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_url contains {needle!r}"


def _handle_expect_count(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    assert step.count is not None, "expect_count に count が必要 (validation バグ?)"
    expect(build_locator(ctx.page, spec)).to_have_count(
        step.count, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_count {spec.describe()} == {step.count}"


def _handle_expect_aria_snapshot(step: Step, ctx: StepContext) -> str:
    spec = _loc(step)
    snapshot = expand_vars(step.text, ctx.nav_vars) or ""
    expect(build_locator(ctx.page, spec)).to_match_aria_snapshot(
        snapshot, timeout=step.timeout_ms or ctx.default_timeout_ms,
    )
    return f"expect_aria_snapshot {spec.describe()}"


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
