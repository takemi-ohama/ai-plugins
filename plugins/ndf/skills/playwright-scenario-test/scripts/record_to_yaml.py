"""Playwright codegen の Python 出力を新スキーマ testcase YAML に変換する。

`record_scenario.py` で codegen を回し Python ファイルを得たあと、本スクリプトに
通すと `goto / click / fill / press / select` 系の操作行を抽出して
locator-first の YAML steps として出力する。

Maj-10 対応: 旧版は手書き string parser (`_parse_args_kv`) で codegen 出力をパース
していたが、引数内の `)` や escape の扱いが脆弱だった。codegen 出力は valid Python
なので `ast.parse(...)` で AST を作り `Call` ノードを抽出する方が遥かに堅牢。

Usage:
    python record_scenario.py --target python --output recorded.py https://example.com
    python record_to_yaml.py recorded.py --id TC-AUTH-login --role user --page-role auth
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any
from urllib.parse import urlparse

import yaml


# `page.get_by_role` 等の locator factory → 新スキーマでの key
_LOCATOR_KIND_REMAP: dict[str, str] = {
    "get_by_role": "role",
    "get_by_label": "label",
    "get_by_placeholder": "placeholder",
    "get_by_text": "text",
    "get_by_alt_text": "alt",
    "get_by_title": "title",
    "get_by_test_id": "testid",
}

# 取り扱う action method
_SUPPORTED_ACTIONS: frozenset[str] = frozenset({
    "goto", "click", "fill", "press", "check", "uncheck",
    "hover", "select_option", "set_input_files",
})


def _literal(node: ast.AST) -> Any:
    """`ast.Constant` 等を Python 値に評価する (literal のみ)。"""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def _kw_dict(call: ast.Call) -> dict[str, Any]:
    """`Call.keywords` から literal 評価できるものだけ dict 化する。"""
    return {kw.arg: _literal(kw.value) for kw in call.keywords if kw.arg}


def _build_locator_from_call(call: ast.Call) -> dict[str, Any] | None:
    """`page.get_by_role("button", name="保存")` の Call → locator dict。"""
    if not isinstance(call.func, ast.Attribute):
        return None
    method = call.func.attr
    if method not in _LOCATOR_KIND_REMAP:
        return None
    kind = _LOCATOR_KIND_REMAP[method]
    selector = _literal(call.args[0]) if call.args else None
    if selector is None:
        return None
    out: dict[str, Any] = {kind: str(selector)}
    kw = _kw_dict(call)
    if "name" in kw and kw["name"] is not None:
        out["name"] = str(kw["name"])
    if "exact" in kw:
        out["exact"] = bool(kw["exact"])
    return out


def _extract_action_call(call: ast.Call) -> tuple[str, dict[str, Any] | None, list[Any], dict[str, Any]] | None:
    """`page.X(args)` または `page.locator_factory(...).X(args)` を解析する。

    Returns: (action_method, locator_dict | None, positional_args, kwargs)
             dispatch 対象でない場合は None。
    """
    if not isinstance(call.func, ast.Attribute):
        return None
    action = call.func.attr
    if action not in _SUPPORTED_ACTIONS:
        return None

    receiver = call.func.value  # page or page.get_by_role(...)
    locator: dict[str, Any] | None = None

    if isinstance(receiver, ast.Call):
        locator = _build_locator_from_call(receiver)
        if locator is None:
            # locator_factory 以外の chain は処理対象外
            return None
    elif isinstance(receiver, ast.Name) and receiver.id == "page":
        # `page.goto(...)` のように直接呼ぶ form
        if action != "goto":
            return None  # locator なしの click/fill 等は無効
    else:
        return None

    pos = [_literal(a) for a in call.args]
    kw = _kw_dict(call)
    return action, locator, pos, kw


def _convert(action: str, locator: dict[str, Any] | None,
             pos: list[Any], kw: dict[str, Any]) -> dict[str, Any] | None:
    """1 件の action call → 新スキーマの step dict に変換する。"""
    if action == "goto":
        url = pos[0] if pos else None
        if not isinstance(url, str):
            return None
        path = urlparse(url).path or "/"
        return {"kind": "goto", "name": f"goto {path}", "path": path}

    if locator is None:
        return None

    name_summary = ", ".join(f"{k}={v!r}" for k, v in locator.items())

    if action == "click":
        return {"kind": "click", "name": f"click {name_summary}", "locator": locator}
    if action == "hover":
        return {"kind": "hover", "name": f"hover {name_summary}", "locator": locator}
    if action == "check":
        return {"kind": "check", "name": f"check {name_summary}", "locator": locator}
    if action == "uncheck":
        return {"kind": "uncheck", "name": f"uncheck {name_summary}", "locator": locator}
    if action == "fill":
        value = pos[0] if pos else ""
        return {
            "kind": "fill", "name": f"fill {name_summary}",
            "locator": locator, "value": str(value),
        }
    if action == "press":
        key = pos[0] if pos else "Enter"
        return {
            "kind": "press", "name": f"press {key} on {name_summary}",
            "locator": locator, "value": str(key),
        }
    if action == "select_option":
        # Playwright codegen は select_option(label="…") など多形式を出力するが、
        # 新スキーマは単純な value 指定を想定。代表的な kw を順に拾う。
        value = pos[0] if pos else (
            kw.get("value") or kw.get("label") or kw.get("index") or ""
        )
        return {
            "kind": "select", "name": f"select {value!r} on {name_summary}",
            "locator": locator, "value": str(value),
        }
    return None  # set_input_files 等は当面非対応


def parse_codegen(text: str) -> list[dict[str, Any]]:
    """Playwright codegen Python 出力を新スキーマ step 候補のリストに変換する (Maj-10)。

    AST ベースで `page.X(...)` / `page.locator_factory(...).X(...)` を抽出する。
    invalid Python (構文エラー) の場合は空 list を返す。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    steps: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        parsed = _extract_action_call(node)
        if parsed is None:
            continue
        step = _convert(*parsed)
        if step is not None:
            steps.append(step)
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
