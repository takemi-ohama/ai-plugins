"""テストケース YAML のロードとデータクラス (locator-first スキーマ)。

v0.3.0 で旧 `path`-only step は削除し、Playwright 公式推奨の locator-first
step kind に統一した。各 step は明示的な `kind` フィールドを持ち、
`locator_steps.dispatch()` で Playwright Locator/expect API へ変換される。
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# docs/02-page-roles.md で定義された page role 集合。
# scripts/generate_test_plan.py の ROLE_ITEM_COUNTS と同期させる。
KNOWN_PAGE_ROLES: frozenset[str] = frozenset({
    "lp", "list", "item", "edit", "form", "search", "dashboard", "auth",
    "cart", "checkout", "modal", "wizard", "error", "settings",
})


# --- Locator スキーマ -----------------------------------------------

# 公式 Playwright の locator API を YAML から呼び分けるためのキー集合。
# `get_by_role(name=...)` 系は accessibility tree ベースなのでテスト崩壊耐性が高い。
# `css` / `xpath` は最後の手段。
_LOCATOR_KIND_PRIORITY: tuple[str, ...] = (
    "role", "label", "placeholder", "text", "alt", "title", "testid", "css", "xpath",
)


@dataclass(frozen=True)
class LocatorSpec:
    """YAML の locator dict を Playwright Locator 構築引数に変換する仕様。

    例:
        {role: button, name: "保存"}      → page.get_by_role("button", name="保存")
        {label: "メールアドレス"}          → page.get_by_label("メールアドレス")
        {testid: submit-btn}              → page.get_by_test_id("submit-btn")
        {css: ".alert-danger"}            → page.locator(".alert-danger")

    name / exact / nth は role / label / text と組み合わせ可能なオプション。
    """
    kind: str               # role / label / placeholder / text / alt / title / testid / css / xpath
    selector: str           # role 名 (button) / ラベル文字列 / セレクタ文字列など
    name: str | None = None  # accessible name (role / alt 系で使用)
    exact: bool = False
    nth: int | None = None

    @classmethod
    def from_raw(cls, raw: Any) -> "LocatorSpec":
        if not isinstance(raw, dict):
            raise ValueError(f"locator は dict で指定してください: {raw!r}")
        # codex Min-1: 複数 selector kind を黙って優先順で握りつぶさず、
        # 「locator は 1 種類だけ」と明示エラーにする (typo 早期検出)。
        present = [k for k in _LOCATOR_KIND_PRIORITY if k in raw]
        if not present:
            raise ValueError(
                f"locator に有効な指定子がありません ({_LOCATOR_KIND_PRIORITY} のいずれか): {raw!r}"
            )
        if len(present) > 1:
            raise ValueError(
                f"locator は 1 種類のみ指定してください (複数検出: {present}): {raw!r}"
            )
        kind = present[0]
        return cls(
            kind=kind,
            selector=str(raw[kind]),
            name=str(raw["name"]) if raw.get("name") is not None else None,
            exact=bool(raw.get("exact", False)),
            nth=int(raw["nth"]) if raw.get("nth") is not None else None,
        )

    def describe(self) -> str:
        """ステップ名や log に出すための短い表現。"""
        parts = [f"{self.kind}={self.selector!r}"]
        if self.name is not None:
            parts.append(f"name={self.name!r}")
        if self.nth is not None:
            parts.append(f"nth={self.nth}")
        return "(" + ", ".join(parts) + ")"


# --- Step スキーマ ---------------------------------------------------

# 全 step kind の許容リスト (typo / 旧スキーマを早期検出するため)。
KNOWN_STEP_KINDS: frozenset[str] = frozenset({
    "goto", "click", "fill", "select", "check", "uncheck", "press", "hover",
    "extract", "wait_for", "wait_ms",
    "expect_visible", "expect_hidden", "expect_text", "expect_no_text",
    "expect_url", "expect_count", "expect_aria_snapshot",
})


@dataclass
class Step:
    """1 つの step。kind ごとに有効なフィールドが異なる (validation は from_raw で実施)。"""
    kind: str
    name: str
    # Locator が必要な kind (click / fill / expect_visible / ...) で必須
    locator: LocatorSpec | None = None
    # goto / wait_for / expect_url 用
    path: str | None = None
    expect_status: int | None = None
    # fill / select / press 用
    value: str | None = None
    # extract: locator から拾った text を変数に保存 (`{var_name}` で後続 step が参照)
    var: str | None = None
    # expect_text / expect_no_text / expect_aria_snapshot
    text: str | None = None
    # expect_count
    count: int | None = None
    # expect_url の URL substring 比較
    contains: str | None = None
    # wait_ms 用 (固定 sleep。最後の手段)
    ms: int | None = None
    # 任意 timeout override (ms)
    timeout_ms: int | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "Step":
        if not isinstance(raw, dict):
            raise ValueError(f"step は dict で指定してください: {raw!r}")
        kind = str(raw.get("kind") or "")
        if kind not in KNOWN_STEP_KINDS:
            raise ValueError(
                f"未知の step kind: {kind!r} (known: {sorted(KNOWN_STEP_KINDS)})"
            )
        name = str(raw.get("name") or kind)
        loc_raw = raw.get("locator")
        locator = LocatorSpec.from_raw(loc_raw) if loc_raw is not None else None

        step = cls(
            kind=kind,
            name=name,
            locator=locator,
            path=_opt_str(raw.get("path")),
            expect_status=int(raw["expect_status"]) if raw.get("expect_status") is not None else None,
            value=_opt_str(raw.get("value")),
            var=_opt_str(raw.get("var")),
            text=_opt_str(raw.get("text")),
            count=int(raw["count"]) if raw.get("count") is not None else None,
            contains=_opt_str(raw.get("contains")),
            ms=int(raw["ms"]) if raw.get("ms") is not None else None,
            timeout_ms=int(raw["timeout_ms"]) if raw.get("timeout_ms") is not None else None,
        )
        step._validate_required()
        return step

    def _validate_required(self) -> None:
        """kind ごとの必須フィールドを確認 (実行時エラー回避)。"""
        needs_locator = {
            "click", "fill", "select", "check", "uncheck", "press", "hover",
            "extract", "wait_for", "expect_visible", "expect_hidden",
            "expect_text", "expect_no_text", "expect_count", "expect_aria_snapshot",
        }
        if self.kind in needs_locator and self.locator is None:
            raise ValueError(f"step kind={self.kind!r} には locator: が必要 ({self.name})")
        if self.kind == "goto" and not self.path:
            raise ValueError(f"step kind=goto には path: が必要 ({self.name})")
        if self.kind in ("fill", "select", "press") and self.value is None:
            raise ValueError(f"step kind={self.kind!r} には value: が必要 ({self.name})")
        if self.kind == "extract" and not self.var:
            raise ValueError(f"step kind=extract には var: が必要 ({self.name})")
        if self.kind in ("expect_text", "expect_no_text", "expect_aria_snapshot") and self.text is None:
            raise ValueError(f"step kind={self.kind!r} には text: が必要 ({self.name})")
        if self.kind == "expect_count" and self.count is None:
            raise ValueError(f"step kind=expect_count には count: が必要 ({self.name})")
        if self.kind == "expect_url" and not (self.contains or self.path):
            raise ValueError(f"step kind=expect_url には contains: または path: が必要 ({self.name})")
        if self.kind == "wait_ms" and self.ms is None:
            raise ValueError(f"step kind=wait_ms には ms: が必要 ({self.name})")


# --- curl チェック ----------------------------------------------------

@dataclass
class CurlCheck:
    """curl タイプのテストケース内の 1 件のチェック。"""
    id: str
    name: str
    path: str
    basic_auth: str = "skip"   # "skip" | "required" | "optional"
    expect_status_in: list[int] = field(default_factory=lambda: [200])
    body_must_contain: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "CurlCheck":
        return cls(
            id=str(raw["id"]),
            name=str(raw["name"]),
            path=str(raw["path"]),
            basic_auth=str(raw.get("basic_auth", "skip")),
            expect_status_in=list(raw.get("expect_status_in") or [200]),
            body_must_contain=list(raw.get("body_must_contain") or []),
        )


def _opt_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v)
    return s if s else None


# --- ログイン定義 (config.py から移譲されてくる Login と一対一) ----------

@dataclass
class LoginOverride:
    """testcase 単位でログイン後 URL アサーションを上書きする (任意)。"""
    url_must_not_contain: list[str] = field(default_factory=list)


# --- TestCase --------------------------------------------------------

@dataclass
class TestCase:
    """1 YAML ファイル = 1 テストケース。"""
    id: str
    title: str
    phase: int
    type: str               # "curl" | "playwright"
    role: str | None
    priority: str = "medium"
    tags: list[str] = field(default_factory=list)
    description: str = ""
    source_path: Path | None = None

    # docs/02-page-roles.md 上の page role (lp/list/item/edit/form/...).
    # 計画書から実行・report までトレース可能にするための分類軸。
    page_role: list[str] = field(default_factory=list)

    # curl 用
    checks: list[CurlCheck] = field(default_factory=list)

    # playwright 用
    post_login: LoginOverride = field(default_factory=LoginOverride)
    steps: list[Step] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "TestCase":
        with path.open("r", encoding="utf-8") as fp:
            raw: dict[str, Any] = yaml.safe_load(fp)

        type_ = str(raw.get("type", "playwright"))
        post_login_raw = raw.get("post_login") or {}

        checks = (
            [CurlCheck.from_raw(c) for c in (raw.get("checks") or [])]
            if type_ == "curl" else []
        )
        steps = (
            [Step.from_raw(s) for s in (raw.get("steps") or [])]
            if type_ == "playwright" else []
        )

        page_role_raw = raw.get("page_role")
        if isinstance(page_role_raw, str):
            page_role = [page_role_raw]
        elif isinstance(page_role_raw, list):
            page_role = [str(r) for r in page_role_raw]
        else:
            page_role = []

        unknown = [r for r in page_role if r not in KNOWN_PAGE_ROLES]
        if unknown:
            print(
                f"[testcase warning] {path}: 未知の page_role を検出: {unknown} "
                f"(known: {sorted(KNOWN_PAGE_ROLES)})",
                file=sys.stderr,
            )

        return cls(
            id=str(raw["id"]),
            title=str(raw.get("title", raw["id"])),
            phase=int(raw.get("phase", 99)),
            type=type_,
            role=_opt_str(raw.get("role")),
            priority=str(raw.get("priority", "medium")),
            tags=list(raw.get("tags") or []),
            description=str(raw.get("description", "")),
            source_path=path.resolve(),
            page_role=page_role,
            checks=checks,
            post_login=LoginOverride(
                url_must_not_contain=list(post_login_raw.get("url_must_not_contain") or [])
            ),
            steps=steps,
        )


# --- 出力モデル: 実行結果 -------------------------------------------

@dataclass
class StepRecord:
    """テストケース内の 1 ステップ (curl check or playwright step) の結果。"""
    name: str
    ok: bool
    detail: str = ""
    sub_id: str | None = None
    screenshot_relpath: str | None = None


@dataclass
class TestCaseResult:
    testcase_id: str
    title: str
    phase: int
    type: str
    role: str | None
    priority: str
    tags: list[str]
    started_at: _dt.datetime
    finished_at: _dt.datetime
    case_dir: Path
    ok: bool
    error: str
    video_relpath: str | None
    steps: list[StepRecord]
    nav_vars: dict[str, str] = field(default_factory=dict)
    page_role: list[str] = field(default_factory=list)
    har_relpath: str | None = None
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    # v0.3.0: a11y / CWV の集計を report に流す
    axe_violations: list[dict[str, Any]] = field(default_factory=list)
    cwv_metrics: dict[str, float] = field(default_factory=dict)
    cwv_passed: bool = True

    @property
    def duration_sec(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def passed_steps(self) -> int:
        return sum(1 for s in self.steps if s.ok)

    @property
    def total_steps(self) -> int:
        return len(self.steps)


def discover_testcases(testcases_dir: Path) -> list[TestCase]:
    """testcases_dir 配下の *.yaml をすべて読み込んで返す。"""
    if not testcases_dir.exists():
        raise FileNotFoundError(f"testcases ディレクトリが存在しません: {testcases_dir}")
    cases: list[TestCase] = []
    for path in sorted(testcases_dir.glob("*.yaml")):
        try:
            cases.append(TestCase.load(path))
        except Exception as exc:
            raise RuntimeError(f"テストケース読み込み失敗: {path}: {exc}") from exc
    return cases


def filter_testcases(
    cases: list[TestCase],
    *,
    ids: list[str] | None = None,
    phases: list[int] | None = None,
    roles: list[str] | None = None,
    types: list[str] | None = None,
    tags: list[str] | None = None,
    page_roles: list[str] | None = None,
) -> list[TestCase]:
    """指定された条件に合致するケースのみを返す。"""
    tag_set = set(tags) if tags else None
    page_role_set = set(page_roles) if page_roles else None

    def matches(c: TestCase) -> bool:
        if ids and c.id not in ids and not any(ck.id in ids for ck in c.checks):
            return False
        if phases and c.phase not in phases:
            return False
        if roles and (c.role or "") not in roles:
            return False
        if types and c.type not in types:
            return False
        if tag_set and not (tag_set & set(c.tags)):
            return False
        if page_role_set and not (page_role_set & set(c.page_role)):
            return False
        return True

    return [c for c in cases if matches(c)]


_FILTER_RE = re.compile(r"^([a-z][a-z_]*):(.+)$")


def parse_filter(spec: str) -> dict[str, list[str]]:
    """`--filter "phase:50,51 role:user"` のような文字列をパースする。

    区切り規則:
      - フィールド間は **空白** で区切る (`phase:50 role:user`)
      - 同一フィールド内の複数値は **カンマ** で区切る (`phase:50,51`)
    """
    out: dict[str, list[str]] = {}
    if not spec:
        return out
    for token in spec.split():
        m = _FILTER_RE.match(token.strip())
        if not m:
            continue
        out.setdefault(m.group(1), []).extend(v for v in m.group(2).split(",") if v)
    return out
