"""Playwright codegen の Python 出力を新スキーマ testcase YAML に変換する。

`record_scenario.py` で codegen を回し Python ファイルを得たあと、本スクリプトに
通すと `goto / click / fill / press / select` 系の操作行を抽出して
locator-first の YAML steps として出力する。

Usage:
    python record_scenario.py --target python --output recorded.py https://example.com
    python record_to_yaml.py recorded.py --id TC-AUTH-login --role user --page-role auth
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml


# `page.get_by_role("button", name="保存")` 等を捉える共通パターン
_LOCATOR_GETBY_RE = re.compile(
    r"page\.get_by_(?P<kind>role|label|placeholder|text|alt_text|title|test_id)\("
    r"(?P<args>.+?)\)"
)
# locator dispatcher 側のキー名 (alt_text → alt, test_id → testid に合わせる)
_KIND_REMAP = {"alt_text": "alt", "test_id": "testid"}

# `.action(...)` 系
_ACTION_RE = re.compile(
    r"^\s*page(?:\.get_by_(?P<lkind>\w+)\((?P<largs>[^)]+)\))?\.(?P<action>"
    r"goto|click|fill|press|check|uncheck|select_option|hover|set_input_files"
    r")\((?P<aargs>[^)]*)\)\s*$"
)

# シンプルな `page.goto(...)`
_GOTO_RE = re.compile(r"^\s*page\.goto\(\s*['\"](?P<url>[^'\"]+)['\"]")


def _parse_args_kv(args: str) -> tuple[str | None, dict[str, str]]:
    """`"button", name="保存"` → ("button", {"name": "保存"})"""
    parts: list[str] = []
    depth = 0
    current = ""
    in_str: str | None = None
    for ch in args:
        if in_str:
            current += ch
            if ch == in_str and not current.endswith("\\" + in_str):
                in_str = None
            continue
        if ch in ("'", '"'):
            in_str = ch
            current += ch
            continue
        if ch in "([{":
            depth += 1
            current += ch
            continue
        if ch in ")]}":
            depth -= 1
            current += ch
            continue
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += ch
    if current.strip():
        parts.append(current.strip())

    positional: str | None = None
    kwargs: dict[str, str] = {}
    for p in parts:
        m = re.match(r"^([a-zA-Z_]\w*)\s*=\s*(.+)$", p)
        if m:
            kwargs[m.group(1)] = _strip_quotes(m.group(2))
        else:
            if positional is None:
                positional = _strip_quotes(p)
    return positional, kwargs


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _build_locator(lkind: str, largs: str) -> dict[str, Any]:
    """`get_by_role("button", name="X")` → {role: button, name: X}"""
    selector, kw = _parse_args_kv(largs)
    kind = _KIND_REMAP.get(lkind, lkind)
    out: dict[str, Any] = {kind: selector}
    if "name" in kw:
        out["name"] = kw["name"]
    if "exact" in kw:
        out["exact"] = kw["exact"].lower() == "true"
    return out


def parse_codegen(text: str) -> list[dict[str, Any]]:
    """Playwright codegen Python 出力を `Step` 候補 dict のリストに変換する。

    認識できなかった行 (with statement / 変数代入など) は黙ってスキップする。
    """
    steps: list[dict[str, Any]] = []
    for line in text.splitlines():
        m = _GOTO_RE.match(line)
        if m and "page.get_by_" not in line:
            url = m.group("url")
            from urllib.parse import urlparse
            path = urlparse(url).path or "/"
            steps.append({"kind": "goto", "name": f"goto {path}", "path": path})
            continue

        m = _ACTION_RE.match(line)
        if not m:
            continue

        action = m.group("action")
        aargs = m.group("aargs") or ""
        loc: dict[str, Any] | None = None
        if m.group("lkind"):
            loc = _build_locator(m.group("lkind"), m.group("largs") or "")

        if action == "goto":
            url, _ = _parse_args_kv(aargs)
            from urllib.parse import urlparse
            path = urlparse(url or "/").path or "/"
            steps.append({"kind": "goto", "name": f"goto {path}", "path": path})
            continue

        if loc is None:
            continue

        name_summary = ", ".join(f"{k}={v!r}" for k, v in loc.items())

        if action == "click":
            steps.append({"kind": "click", "name": f"click {name_summary}", "locator": loc})
        elif action == "hover":
            steps.append({"kind": "hover", "name": f"hover {name_summary}", "locator": loc})
        elif action == "check":
            steps.append({"kind": "check", "name": f"check {name_summary}", "locator": loc})
        elif action == "uncheck":
            steps.append({"kind": "uncheck", "name": f"uncheck {name_summary}", "locator": loc})
        elif action == "fill":
            value, _ = _parse_args_kv(aargs)
            steps.append({
                "kind": "fill", "name": f"fill {name_summary}", "locator": loc,
                "value": value or "",
            })
        elif action == "press":
            key, _ = _parse_args_kv(aargs)
            steps.append({
                "kind": "press", "name": f"press {key} on {name_summary}",
                "locator": loc, "value": key or "Enter",
            })
        elif action == "select_option":
            value, _ = _parse_args_kv(aargs)
            steps.append({
                "kind": "select", "name": f"select {value!r} on {name_summary}",
                "locator": loc, "value": value or "",
            })
    return steps


def to_yaml(
    *, test_id: str, title: str, role: str, page_role: str,
    steps: list[dict[str, Any]], priority: str = "medium", phase: int = 10,
) -> str:
    """Step 候補 dict を YAML testcase 全体に組み立てる。"""
    body = {
        "id": test_id,
        "title": title,
        "phase": phase,
        "type": "playwright",
        "role": role,
        "page_role": page_role,
        "priority": priority,
        "tags": [page_role, "scenario", "recorded"],
        "description": dedent(f"""\
            Playwright codegen 録画 → record_to_yaml.py で自動変換 (page_role={page_role}).
            録画したシナリオ後に expect_visible / expect_url 等の assertion を手動追加すること.
        """).rstrip(),
        "post_login": {"url_must_not_contain": []},
        "steps": steps,
    }
    return yaml.safe_dump(body, allow_unicode=True, sort_keys=False, width=100)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Playwright codegen Python 出力 → 新スキーマ testcase YAML",
    )
    parser.add_argument("input", type=Path, help="codegen の Python 出力ファイル")
    parser.add_argument("--id", required=True, help="テストケース ID")
    parser.add_argument("--role", required=True, help="config 上の role (admin/user/...)")
    parser.add_argument("--page-role", required=True,
                        help="page role (lp/list/edit/form/auth/...)")
    parser.add_argument("--title", default=None, help="testcase タイトル (省略時は ID)")
    parser.add_argument("--phase", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None,
                        help="YAML 出力先 (省略時 stdout)")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    raw = args.input.read_text(encoding="utf-8")
    steps = parse_codegen(raw)
    if not steps:
        print("WARNING: 変換可能な操作行が見つかりませんでした", file=sys.stderr)

    yaml_text = to_yaml(
        test_id=args.id,
        title=args.title or args.id,
        role=args.role,
        page_role=args.page_role,
        steps=steps,
        phase=args.phase,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(yaml_text, encoding="utf-8")
        print(f"OK: {len(steps)} step → {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(yaml_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
