"""curl タイプのテストケースを 1 件実行する。"""

from __future__ import annotations

import datetime as _dt
import shutil
import subprocess
from pathlib import Path

from scenario_test.config import Config
from scenario_test.testcase import CurlCheck, StepRecord, TestCase, TestCaseResult


_STATUS_MARKER = "__CURL_STATUS__:"


def _curl(
    base_url: str,
    path: str,
    *,
    basic_auth: tuple[str, str] | None,
    verify_tls: bool,
    timeout: int = 20,
) -> tuple[int, str]:
    """curl で指定パスを叩き (HTTP コード, 全 body) を返す。"""
    cmd = ["curl", "-sS", "-o", "-", "-w", f"\n{_STATUS_MARKER}%{{http_code}}"]
    if not verify_tls:
        cmd.append("-k")
    if basic_auth is not None:
        cmd.extend(["-u", f"{basic_auth[0]}:{basic_auth[1]}"])
    cmd.extend(["--max-time", str(timeout), f"{base_url}{path}"])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return 0, "<timeout>"
    except FileNotFoundError as exc:
        raise RuntimeError("curl コマンドが見つかりません。") from exc

    out = proc.stdout
    idx = out.rfind(_STATUS_MARKER)
    if idx < 0:
        return 0, out
    body = out[:idx].rstrip("\n")
    code_str = out[idx + len(_STATUS_MARKER):].strip()
    try:
        code = int(code_str)
    except ValueError:
        code = 0
    return code, body


def _run_check(
    check: CurlCheck,
    base_url: str,
    auth_pair: tuple[str, str],
    verify_tls: bool,
) -> tuple[StepRecord, str]:
    """1 件の CurlCheck を実行し (StepRecord, ログ用 1 行) を返す。"""
    auth = auth_pair if check.basic_auth == "required" else None
    code, body = _curl(base_url, check.path, basic_auth=auth, verify_tls=verify_tls)

    status_ok = code in check.expect_status_in
    missing_in_body = [s for s in check.body_must_contain if s not in body]
    ok = status_ok and not missing_in_body

    detail = [f"path={check.path}", f"status={code}"]
    if not status_ok:
        detail.append(f"期待={check.expect_status_in}")
    if missing_in_body:
        detail.append(f"body 未検出: {missing_in_body}")

    record = StepRecord(name=check.name, ok=ok, detail=" / ".join(detail), sub_id=check.id)
    log = f"[{check.id}] {'OK' if ok else 'FAIL'}: {check.name} -> HTTP {code}"
    return record, log


def _make_result(
    tc: TestCase, case_dir: Path, started: _dt.datetime,
    *, ok: bool, error: str = "", steps: list[StepRecord] | None = None,
) -> TestCaseResult:
    return TestCaseResult(
        testcase_id=tc.id, title=tc.title, phase=tc.phase, type=tc.type,
        role=tc.role, priority=tc.priority, tags=tc.tags,
        started_at=started, finished_at=_dt.datetime.now(),
        case_dir=case_dir, ok=ok, error=error,
        video_relpath=None, steps=steps or [],
    )


def run_curl_testcase(
    tc: TestCase,
    config: Config,
    case_dir: Path,
) -> TestCaseResult:
    """curl タイプのテストケースを実行し、各 check を StepRecord に変換する。"""
    started = _dt.datetime.now()
    case_dir.mkdir(parents=True, exist_ok=True)

    if not shutil.which("curl"):
        return _make_result(tc, case_dir, started, ok=False, error="curl コマンドが見つかりません")

    auth_pair = (config.basic_auth.user, config.basic_auth.password)
    steps: list[StepRecord] = []
    log_lines: list[str] = []
    for check in tc.checks:
        record, log = _run_check(check, config.base_url, auth_pair, config.verify_tls)
        steps.append(record)
        log_lines.append(log)

    (case_dir / "log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return _make_result(tc, case_dir, started, ok=all(s.ok for s in steps), steps=steps)
