"""テストケース YAML のロードとデータクラス。"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# --- 入力モデル: テストケース YAML ----------------------------------

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


@dataclass
class NavStep:
    """playwright タイプのテストケース内の 1 ページ訪問。"""
    name: str
    path: str
    method: str = "GET"                          # "GET" | "POST"
    data: dict[str, str] = field(default_factory=dict)  # POST フォームデータ
    extract: dict[str, str] = field(default_factory=dict)
    skip_if_missing: list[str] = field(default_factory=list)
    expect_content_type: str | None = None
    expect_status: int = 200
    expect_url_contains: str | None = None       # 遷移先 URL に含まれることを要求

    @classmethod
    def from_raw(cls, raw: str | dict[str, Any]) -> "NavStep":
        if isinstance(raw, str):
            return cls(name=raw, path=raw)
        return cls(
            name=str(raw.get("name") or raw["path"]),
            path=str(raw["path"]),
            method=str(raw.get("method", "GET")).upper(),
            data={str(k): str(v) for k, v in (raw.get("data") or {}).items()},
            extract=dict(raw.get("extract") or {}),
            skip_if_missing=list(raw.get("skip_if_missing") or []),
            expect_content_type=_opt_str(raw.get("expect_content_type")),
            expect_status=int(raw.get("expect_status", 200)),
            expect_url_contains=_opt_str(raw.get("expect_url_contains")),
        )


def _opt_str(v: Any) -> str | None:
    return str(v) if v else None


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

    # docs/02-page-roles.md 上の page role (lp/list/item/edit/form/...)。
    # 単一文字列または複数 role の list。計画書から実行・report までトレース可能にする。
    page_role: list[str] = field(default_factory=list)

    # curl 用
    checks: list[CurlCheck] = field(default_factory=list)

    # playwright 用
    post_login_url_must_not_contain: list[str] = field(default_factory=list)
    steps: list[NavStep] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "TestCase":
        with path.open("r", encoding="utf-8") as fp:
            raw: dict[str, Any] = yaml.safe_load(fp)

        type_ = str(raw.get("type", "playwright"))
        post_login = raw.get("post_login") or {}

        checks = (
            [CurlCheck.from_raw(c) for c in (raw.get("checks") or [])]
            if type_ == "curl" else []
        )
        steps = (
            [NavStep.from_raw(s) for s in (raw.get("steps") or [])]
            if type_ == "playwright" else []
        )

        page_role_raw = raw.get("page_role")
        if isinstance(page_role_raw, str):
            page_role = [page_role_raw]
        elif isinstance(page_role_raw, list):
            page_role = [str(r) for r in page_role_raw]
        else:
            page_role = []

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
            post_login_url_must_not_contain=list(post_login.get("url_must_not_contain") or []),
            steps=steps,
        )


# --- 出力モデル: 実行結果 -------------------------------------------

@dataclass
class StepRecord:
    """テストケース内の 1 ステップ (curl check or playwright step) の結果。"""
    name: str
    ok: bool
    detail: str = ""
    sub_id: str | None = None              # curl check の場合 TC-00-01 等
    screenshot_relpath: str | None = None  # case_dir からの相対


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
    video_relpath: str | None              # case_dir からの相対パス
    steps: list[StepRecord]
    nav_vars: dict[str, str] = field(default_factory=dict)
    page_role: list[str] = field(default_factory=list)
    har_relpath: str | None = None         # HAR ファイルの相対パス
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)

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
        # 親 ID と curl サブ ID (例 TC-00-01) のどちらかにヒットすれば OK
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


_FILTER_RE = re.compile(r"^([a-z]+):(.+)$")


def parse_filter(spec: str) -> dict[str, list[str]]:
    """`--filter "phase:50,51 role:user"` のような文字列をパースする。"""
    out: dict[str, list[str]] = {}
    if not spec:
        return out
    for token in spec.replace(",", " ").split():
        m = _FILTER_RE.match(token.strip())
        if not m:
            continue
        out.setdefault(m.group(1), []).extend(v for v in m.group(2).split(",") if v)
    return out
