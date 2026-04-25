"""page_role + URL からテスト計画 (testcase YAML 雛形 + Markdown checklist) を生成する。

「経験で計画する」を「checklist + 技法マトリクスから機械的に生成する」に置換する。
docs/03-test-techniques.md の「役割×データ型→必須技法」マッピングを実装。

Usage:
    python generate_test_plan.py --role list --url https://example.com/items \\
        --output testcases/TC-LST-items.yaml
    python generate_test_plan.py --role form --url https://example.com/contact \\
        --factors "country=JP,US,EU" --factors "type=individual,corporate"
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent

# checklist の項目数 (役割ごと、ハードコード = docs/checklists/ の実数を反映)。
# 計画生成時に「全 N 項目を必ず参照したか」を AI に確認させる。
ROLE_ITEM_COUNTS: dict[str, int] = {
    "lp": 12, "list": 15, "item": 13, "edit": 14, "form": 15,
    "search": 13, "dashboard": 15, "auth": 15, "cart": 17, "checkout": 17,
    "modal": 10, "wizard": 10,
    # cart と checkout は同一 checklist (cart-checkout.md) を共有。
    # error / settings は専用 checklist がなく checklist-common.md + 関連 role で代用。
    "error": 0, "settings": 0,
}

# 各 role の checklist ファイル名 (docs/checklists/ 内の実ファイルにマップ)。
# 一部 role は共通ファイルを共有する。
ROLE_CHECKLIST_FILES: dict[str, str] = {
    "lp": "checklist-lp.md",
    "list": "checklist-list.md",
    "item": "checklist-item.md",
    "edit": "checklist-edit.md",
    "form": "checklist-form.md",
    "search": "checklist-search.md",
    "dashboard": "checklist-dashboard.md",
    "auth": "checklist-auth.md",
    "cart": "checklist-cart-checkout.md",      # cart と checkout で共有
    "checkout": "checklist-cart-checkout.md",
    "modal": "checklist-modal-wizard.md",      # modal と wizard で共有
    "wizard": "checklist-modal-wizard.md",
    # error / settings には専用 checklist がない。共通 + 近接 role を参照する。
    "error": "checklist-common.md",
    "settings": "checklist-edit.md",
}

# 役割 × 必須技法 (docs/03-test-techniques.md § 11 のマッピング)
ROLE_TECHNIQUES: dict[str, list[str]] = {
    "lp": ["Claims", "Domain (viewport)", "Automatic (axe)"],
    "list": ["EP (Count: 0/1/Many)", "BVA (page)", "Pairwise (filter)", "State Transition"],
    "item": ["Domain (id partition)", "Risk (IDOR)", "Claims"],
    "edit": ["BVA", "EP", "Decision Table", "State Transition (dirty/saving)"],
    "form": ["Decision Table 必須", "Classification Tree + Pairwise", "State Transition"],
    "search": ["Domain (clean/inj)", "Claims (relevance)", "Pairwise (facets)"],
    "dashboard": ["Domain (period)", "Claims (real-time)", "Multi-user (race)"],
    "auth": ["Decision Table (auth flow)", "Risk (列挙/ロック)", "BVA (PW length)"],
    "cart": ["Decision Table (price calc)", "BVA (amount)", "Multi-user (stock)"],
    "checkout": ["Decision Table", "BVA (CVV/amount)", "State Transition (cart→paid)", "Risk (PCI)"],
    "modal": ["State Transition (open/focus/close)", "ARIA APG conformance"],
    "wizard": ["State Transition", "Decision Table (動的 step)"],
    "error": ["Claims (status code)", "Risk (情報露出)", "User (復帰導線)"],
    "settings": ["BVA", "Decision Table (再認証要否)", "State Transition (退会フロー)"],
}


@dataclass
class Factor:
    """Decision Table / Pairwise 用の入力因子。"""
    name: str
    values: list[str]


def _all_pairs(factors: list[Factor]) -> list[dict[str, str]]:
    """All-Pairs (簡易実装: 全組合せから 2 因子被覆を greedy 選択)。

    厳密な orthogonal array ではないが、組合せ削減としては実用範囲。
    因子 ≤ 5 / 各因子の値 ≤ 5 を想定。
    """
    if len(factors) < 2:
        if len(factors) == 1:
            return [{factors[0].name: v} for v in factors[0].values]
        return []

    # 必要な 2 因子組合せを集める
    required: set[tuple[str, str, str, str]] = set()
    for fa, fb in itertools.combinations(factors, 2):
        for va in fa.values:
            for vb in fb.values:
                required.add((fa.name, va, fb.name, vb))

    # 全組合せ
    keys = [f.name for f in factors]
    full = [
        dict(zip(keys, vals))
        for vals in itertools.product(*(f.values for f in factors))
    ]

    # 必要 pair を最も多くカバーするケースを greedy 選択
    chosen: list[dict[str, str]] = []
    while required and full:
        best_idx = 0
        best_cover = 0
        for i, case in enumerate(full):
            cover = sum(
                1 for r in required
                if case.get(r[0]) == r[1] and case.get(r[2]) == r[3]
            )
            if cover > best_cover:
                best_cover = cover
                best_idx = i
        if best_cover == 0:
            break
        chosen.append(full[best_idx])
        # この case がカバーする pair を required から除去
        case = full.pop(best_idx)
        required = {
            r for r in required
            if not (case.get(r[0]) == r[1] and case.get(r[2]) == r[3])
        }

    return chosen


def _parse_factor(spec: str) -> Factor:
    """`country=JP,US,EU` → Factor。"""
    if "=" not in spec:
        raise ValueError(f"--factors は name=v1,v2,... 形式: {spec}")
    name, values_csv = spec.split("=", 1)
    values = [v.strip() for v in values_csv.split(",") if v.strip()]
    if not values:
        raise ValueError(f"--factors の値が空: {spec}")
    return Factor(name=name.strip(), values=values)


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", s.lower()).strip("-")
    return re.sub(r"-+", "-", s)[:60]


def _yaml_dump(data: dict | list, indent: int = 0) -> str:
    """単純な YAML 整形 (依存追加を避けるため自前で)。"""
    pad = "  " * indent
    if isinstance(data, dict):
        out = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                out.append(_yaml_dump(v, indent + 1))
            else:
                out.append(f"{pad}{k}: {_yaml_repr(v)}")
        return "\n".join(out)
    if isinstance(data, list):
        out = []
        for item in data:
            if isinstance(item, (dict, list)):
                head = f"{pad}- "
                body = _yaml_dump(item, indent + 1)
                # body の最初の行を head と結合
                lines = body.splitlines()
                lines[0] = head + lines[0].lstrip()
                out.extend(lines)
            else:
                out.append(f"{pad}- {_yaml_repr(item)}")
        return "\n".join(out)
    return f"{pad}{_yaml_repr(data)}"


_YAML_RESERVED_RE = re.compile(
    r"^(true|false|null|yes|no|on|off|~)$|^[+-]?\d+(\.\d+)?$|^0x[0-9a-fA-F]+$|^0o[0-7]+$",
    re.IGNORECASE,
)


def _yaml_repr(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int) or isinstance(v, float):
        # 数値はそのまま (期待は数値型)
        return str(v)
    if isinstance(v, str):
        # 文字列は **常に JSON quote** で出力する。
        # 型保持のため: '01', 'true', 'null', '12345' (郵便番号) などが
        # safe_load 後に別型になるのを防ぐ。
        if (not v
            or re.search(r"[:#\[\]{},&*!|>'\"%@`\n\r\t]", v)
            or v.strip() != v
            or _YAML_RESERVED_RE.match(v)
            or (v[0].isdigit() and any(c not in "0123456789." for c in v[1:]) is False)):
            return json.dumps(v, ensure_ascii=False)
        return v
    return str(v)


def generate_yaml(
    role: str,
    url: str,
    *,
    test_id: str,
    title: str | None,
    role_actor: str = "user",
    factors: list[Factor] | None = None,
) -> str:
    """testcase YAML を生成する。"""
    item_count = ROLE_ITEM_COUNTS.get(role, 0)
    techniques = ROLE_TECHNIQUES.get(role, [])
    checklist_file = ROLE_CHECKLIST_FILES.get(role, "checklist-common.md")

    pairs = _all_pairs(factors) if factors else []

    title = title or f"{role.upper()} シナリオ ({url})"

    item_count_text = (
        f"全 {item_count} 項目を走査"
        if item_count > 0
        else "横断項目のみ (専用 checklist なし)"
    )

    header_comments = dedent(f"""\
        # ============================================================
        # 自動生成テスト計画 — page_role: {role}
        # ============================================================
        # 必須参照ドキュメント:
        #   - docs/checklists/{checklist_file} ({item_count_text})
        #   - docs/checklists/checklist-common.md (a11y/perf/sec/i18n 横断)
        #   - docs/03-test-techniques.md (適用技法)
        #   - docs/05-bug-report.md (失敗時の報告)
        #
        # 必須テスト技法 (docs/03-test-techniques.md § 11 マッピング):
        """).rstrip("\n") + "\n" + "\n".join(f"#   - {t}" for t in techniques) + "\n"

    if pairs:
        header_comments += "#\n# Pairwise 適用済み (--factors 指定):\n"
        header_comments += f"#   入力因子: {', '.join(f.name for f in (factors or []))}\n"
        header_comments += f"#   全組合せ {sum(1 for _ in itertools.product(*(f.values for f in (factors or []))))} → All-Pairs で {len(pairs)} 件に削減\n"

    base_yaml = {
        "id": test_id,
        "title": title,
        "phase": 10,
        "type": "playwright",
        "role": role_actor,
        "page_role": role,
        "priority": "high",
        "tags": [role, "scenario"],
        "description": (
            f"page_role={role} の必須 {item_count} 項目チェック。\n"
            f"docs/checklists/{checklist_file} の全項目を覆うこと。"
        ),
        "post_login": {"url_must_not_contain": []},
    }

    steps: list[dict] = [
        {
            "name": f"[{role}] 主要画面表示確認",
            "path": _path_from_url(url),
            "expect_status": 200,
        },
    ]

    if pairs:
        # Pairwise ケースを step として展開 (POST 入力分岐の例)
        for i, case in enumerate(pairs, 1):
            steps.append({
                "name": f"Pairwise #{i}: {', '.join(f'{k}={v}' for k,v in case.items())}",
                "path": _path_from_url(url),
                "method": "POST",
                "data": case,
            })

    base_yaml["steps"] = steps

    body = _yaml_dump(base_yaml)
    return header_comments + "\n" + body + "\n"


def _path_from_url(url: str) -> str:
    """URL からパス部分のみ抽出 (config.yaml の base_url が前置されるため)。"""
    from urllib.parse import urlparse
    p = urlparse(url)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")


def generate_checklist_summary(role: str) -> str:
    """role 別 checklist の要約を Markdown で生成 (テスト計画書補助)。"""
    item_count = ROLE_ITEM_COUNTS.get(role, 0)
    techniques = ROLE_TECHNIQUES.get(role, [])
    checklist_file = ROLE_CHECKLIST_FILES.get(role, "checklist-common.md")
    item_count_text = f"{item_count} 項目" if item_count > 0 else "横断項目のみ"
    return dedent(f"""\
        # テスト計画サマリ: {role.upper()}

        - 必須 checklist: docs/checklists/{checklist_file} ({item_count_text})
        - 共通 checklist: docs/checklists/checklist-common.md
        - 適用技法: {", ".join(techniques)}

        ## 参照すべき docs (順次)
        1. docs/02-page-roles.md  — {role} の識別と兼ね role
        2. docs/checklists/{checklist_file} — 必須テスト観点
        3. docs/checklists/checklist-common.md — a11y / perf / sec / i18n
        4. docs/03-test-techniques.md — 各観点に適用する技法
        5. docs/04-playwright-mapping.md — locator / assertion 戦略
        6. docs/05-bug-report.md — 失敗時の報告書式

        ## チェック完了の宣言
        テスト計画 YAML には次のいずれかの形で全項目への対応を記録すること:
        - 適用 → 該当 step の `technique` と `oracle` を明記
        - 不適用 → `description` 内に「項目 N: 不適用 (理由)」を記述
        """)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="page_role + URL から testcase YAML 雛形 + checklist サマリを生成"
    )
    parser.add_argument("--role", required=True,
                        choices=list(ROLE_ITEM_COUNTS.keys()),
                        help="page role (lp/list/item/edit/form/search/dashboard/auth/cart/checkout/modal/wizard)")
    parser.add_argument("--url", required=True, help="対象 URL")
    parser.add_argument("--id", default=None, help="テストケース ID (省略時は role+slug)")
    parser.add_argument("--title", default=None, help="テストケースタイトル")
    parser.add_argument("--actor", default="user", help="config 上の role (admin/user/...)")
    parser.add_argument("--factors", action="append", default=[],
                        help="Pairwise 入力因子 (例: country=JP,US,EU)。複数指定可")
    parser.add_argument("--output", type=Path, default=None,
                        help="testcase YAML 出力先 (省略時 stdout)")
    parser.add_argument("--summary", type=Path, default=None,
                        help="checklist サマリ Markdown 出力先 (省略時は出力しない)")
    args = parser.parse_args()

    factors = [_parse_factor(s) for s in args.factors]
    test_id = args.id or f"TC-{args.role.upper()[:4]}-{_slugify(args.url.split('/')[-1] or 'root')}"

    yaml_text = generate_yaml(
        args.role, args.url,
        test_id=test_id, title=args.title, role_actor=args.actor, factors=factors,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(yaml_text, encoding="utf-8")
        print(f"OK: testcase YAML → {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(yaml_text)

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(generate_checklist_summary(args.role), encoding="utf-8")
        print(f"OK: checklist サマリ → {args.summary}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
