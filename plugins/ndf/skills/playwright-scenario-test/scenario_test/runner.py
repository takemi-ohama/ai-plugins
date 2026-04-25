"""テストケースの並列実行オーケストレーター。

各テストケースを ProcessPoolExecutor の独立プロセスで実行し、
それぞれが独自の Playwright インスタンスと動画ファイルを生成する。
"""

from __future__ import annotations

import datetime as _dt
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from scenario_test.config import Config
from scenario_test.curl_executor import run_curl_testcase
from scenario_test.playwright_executor import run_playwright_testcase
from scenario_test.testcase import TestCase, TestCaseResult


_EXECUTORS = {
    "curl": run_curl_testcase,
    "playwright": run_playwright_testcase,
}


def _empty_result(tc: TestCase, case_dir: Path, error: str) -> TestCaseResult:
    """エラー時の空 TestCaseResult を生成する。"""
    now = _dt.datetime.now()
    return TestCaseResult(
        testcase_id=tc.id, title=tc.title, phase=tc.phase, type=tc.type,
        role=tc.role, priority=tc.priority, tags=tc.tags,
        started_at=now, finished_at=now,
        case_dir=case_dir, ok=False, error=error,
        video_relpath=None, steps=[],
    )


def _execute_one(
    testcase_path: str,
    config_path: str,
    out_dir: str,
) -> TestCaseResult:
    """サブプロセス側で 1 ケース分を実行するエントリーポイント。

    引数はすべて文字列（pickle 互換性確保のため）。
    """
    tc = TestCase.load(Path(testcase_path))
    config = Config.load(Path(config_path))
    case_dir = Path(out_dir) / tc.id

    executor = _EXECUTORS.get(tc.type)
    if executor is None:
        return _empty_result(tc, case_dir, error=f"unknown type: {tc.type}")
    return executor(tc, config, case_dir)


def run_parallel(
    testcases: list[TestCase],
    config: Config,
    *,
    out_dir: Path,
    workers: int,
    on_complete: Callable[[TestCaseResult], None] | None = None,
) -> list[TestCaseResult]:
    """testcases を並列実行する。

    workers <= 1 の場合は逐次実行。on_complete はケース完了ごとに呼ばれる。
    """
    args = [(str(tc.source_path), str(config.config_path), str(out_dir)) for tc in testcases]
    results: list[TestCaseResult] = []

    if workers <= 1:
        for tc, a in zip(testcases, args):
            try:
                result = _execute_one(*a)
            except Exception as exc:  # noqa: BLE001
                result = _empty_result(
                    tc, out_dir / tc.id,
                    error=f"runner exception: {type(exc).__name__}: {exc}",
                )
            if on_complete:
                on_complete(result)
            results.append(result)
        return results

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_execute_one, *a): tc for tc, a in zip(testcases, args)}
        for fut in as_completed(futures):
            tc = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                result = _empty_result(
                    tc, out_dir / tc.id,
                    error=f"runner exception: {type(exc).__name__}: {exc}",
                )
            if on_complete:
                on_complete(result)
            results.append(result)

    results.sort(key=lambda r: r.testcase_id)
    return results


def print_progress(result: TestCaseResult) -> None:
    """ケース完了時にコンソールへ 1 行レポート。"""
    mark = "OK  " if result.ok else "FAIL"
    role = result.role or "-"
    print(
        f"  [{mark}] {result.testcase_id:8} ({role:13}) "
        f"{result.passed_steps}/{result.total_steps} {result.duration_sec:.1f}s "
        f"{result.title}",
        flush=True,
    )
    if result.error:
        print(f"         error: {result.error.splitlines()[0]}", file=sys.stderr, flush=True)
