"""シナリオ E2E テストの CLI エントリーポイント。"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

from scenario_test.config import Config
from scenario_test.report import render_report
from scenario_test.runner import print_progress, run_parallel
from scenario_test.testcase import (
    TestCase,
    discover_testcases,
    filter_testcases,
    parse_filter,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scenario-test",
        description="Web シナリオ E2E テスト (curl + Playwright, 並列実行)。",
    )
    p.add_argument("-c", "--config", type=Path, default=Path("config.yaml"),
                   help="共通設定ファイル (default: ./config.yaml)")
    p.add_argument("-o", "--out-dir", type=Path, default=None,
                   help="レポート出力先ディレクトリ (default: ./reports/<timestamp>)")
    p.add_argument("-w", "--workers", type=int, default=None,
                   help="並列ワーカ数 (default: config.runner.workers)")
    p.add_argument("--filter", default="",
                   help='テストケース絞り込み。例: "phase:50,51 role:user", "id:TC-50-01"')
    p.add_argument("--list", action="store_true",
                   help="テストケースを表示するだけで実行しない")
    p.add_argument("--base-url", default=None, help="config.target.base_url を上書き")
    p.add_argument("--basic-user", default=None, help="Basic 認証ユーザを上書き")
    p.add_argument("--basic-pass", default=None, help="Basic 認証パスワードを上書き")
    p.add_argument("--headed", action="store_true",
                   help="ブラウザを headed で起動 (default: headless)")
    return p


def _apply_overrides(config: Config, args: argparse.Namespace) -> None:
    if args.base_url:
        config.base_url = args.base_url.rstrip("/")
    if args.basic_user is not None:
        config.basic_auth.user = args.basic_user
    if args.basic_pass is not None:
        config.basic_auth.password = args.basic_pass
    if args.headed:
        config.playwright.headless = False


def _load_and_filter(config: Config, filter_spec: str) -> list[TestCase]:
    cases = discover_testcases(config.testcases_dir)
    flt = parse_filter(filter_spec)
    return filter_testcases(
        cases,
        ids=flt.get("id"),
        phases=[int(p) for p in flt.get("phase", [])] or None,
        roles=flt.get("role"),
        types=flt.get("type"),
        tags=flt.get("tag"),
    )


def _print_listing(cases: list[TestCase]) -> None:
    print(f"# テストケース ({len(cases)} 件)")
    for c in cases:
        print(
            f"  {c.id:8} phase={c.phase:>2} type={c.type:10} "
            f"role={c.role or '-':12} prio={c.priority:6} {c.title}"
        )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        config = Config.load(args.config.resolve())
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    _apply_overrides(config, args)
    workers = max(1, int(args.workers if args.workers is not None else config.runner.workers))

    try:
        cases = _load_and_filter(config, args.filter)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not cases:
        print("ERROR: 該当するテストケースがありません。--filter を見直してください。",
              file=sys.stderr)
        return 2

    if args.list:
        _print_listing(cases)
        return 0

    started_at = _dt.datetime.now()
    out_dir = (args.out_dir or Path("reports") / started_at.strftime("%Y%m%d-%H%M%S")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] 対象URL : {config.base_url}")
    print(f"[INFO] テストケース: {len(cases)} 件 / 並列ワーカ: {workers}")
    print(f"[INFO] 出力先  : {out_dir}")
    print()
    print("[実行中] (case 完了順に表示)")

    results = run_parallel(
        cases, config,
        out_dir=out_dir, workers=workers,
        on_complete=print_progress,
    )

    report_path, summary = render_report(
        results, config=config, run_dir=out_dir,
        started_at=started_at, finished_at=_dt.datetime.now(),
        workers=workers,
    )

    print()
    print(f"[INFO] レポート: {report_path}")
    if summary["all_pass"]:
        print(f"[INFO] 結果   : 全 {summary['passed_cases']} 件 PASS")
        return 0
    failed = summary["total_cases"] - summary["passed_cases"]
    print(
        f"[INFO] 結果   : {summary['passed_cases']}/{summary['total_cases']} ケース PASS "
        f"(FAIL {failed} 件)"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
