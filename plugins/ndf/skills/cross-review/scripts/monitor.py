#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""cross-review codex/gemini プロセス監視 CLI。

`launch-codex.sh` / `launch-gemini.sh` で起動したバックグラウンドプロセスを
**複数の根拠で多重監視** し、失敗パターン (sentinel 不在 / 早期エラー / ハング /
pidfile stale / result.json 不在) を構造化して扱う。

監視軸:
  1. **pidfile** + `kill -0` でプロセス生存確認
     - 可能なら `/proc/<pid>/cmdline` で codex/gemini であることを再確認 (PID 再利用対策)
  2. **sentinel** (codex のみ): err.log に `^tokens used$` 出現
  3. **early-error pattern**: err.log に既知の致命的キーワードが出たら即中断
  4. **result.json**: プロセス終了後に `/tmp/<agent>-review-pr<PR>-result.json` が
     生成されていなければ失敗扱い
  5. **hard timeout**: 既定 30 分。`--timeout` または `MONITOR_TIMEOUT` で上書き可
  6. **stall timeout**: err.log のサイズが既定 10 分変化しなければ stalled として中断
     (`--stall-timeout` または `MONITOR_STALL` で上書き可)

Usage:
  monitor.py <PR> <target>          target ∈ {codex, gemini, both}
  monitor.py <PR> both --timeout 1200 --stall-timeout 600

Exit codes (target=both は最悪値を返す):
  0  OK            プロセス正常終了 + result.json 確認
  1  USAGE / IO error
  2  TIMEOUT       hard timeout 超過
  3  NO_RESULT     プロセス終了したが result.json 未生成
  4  EARLY_ERROR   err.log に致命的パターン検出
  5  STALLED       err.log が一定時間進捗なし
  6  PIDFILE_BAD   pidfile が無い / 内容が不正 / プロセスが起動していない

Stdout: 各 agent の最終ステータスを JSON で 1 行ずつ吐く（メインがパース可能）。
Stderr: 人間向けの進捗ログ（poll ごとに 1 行）。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


# ---------- 設定 ----------

DEFAULT_TIMEOUT = int(os.environ.get("MONITOR_TIMEOUT", "1800"))   # 30 min
DEFAULT_STALL = int(os.environ.get("MONITOR_STALL", "600"))        # 10 min no progress
DEFAULT_POLL = int(os.environ.get("MONITOR_POLL", "15"))           # 15 sec

# err.log 内で見つけたら即中断する致命的パターン
EARLY_ERROR_PATTERNS = [
    re.compile(r"\bpanic:", re.IGNORECASE),
    re.compile(r"^Traceback ", re.MULTILINE),
    re.compile(r"\b(Permission denied|Authentication failed|401 Unauthorized)\b"),
    re.compile(r"\b(403 Forbidden|429 Too Many Requests)\b"),
    re.compile(r"\bfatal:", re.IGNORECASE),
    re.compile(r"\bquota exceeded\b", re.IGNORECASE),
    re.compile(r"\bConnection refused\b"),
    # gemini 固有: untrusted directory で YOLO が落ちる
    re.compile(r"Approval mode overridden to \"default\""),
    # codex 固有: API キーやサンドボックスエラー
    re.compile(r"sandbox error", re.IGNORECASE),
    re.compile(r"API key (not found|missing|invalid)", re.IGNORECASE),
]

# False positive 避けのためのホワイトリスト（致命的でないが似た語）
EARLY_ERROR_BENIGN = [
    re.compile(r"warning: ", re.IGNORECASE),
    re.compile(r"\bdeprecat", re.IGNORECASE),
]

CODEX_SENTINEL = re.compile(r"^tokens used$", re.MULTILINE)


# ---------- データ型 ----------

@dataclass
class AgentPaths:
    agent: str
    pr: int
    pidfile: pathlib.Path
    err_log: pathlib.Path
    stdout_log: pathlib.Path
    result: pathlib.Path

    @classmethod
    def for_(cls, agent: str, pr: int) -> "AgentPaths":
        base = f"/tmp/{agent}-review-pr{pr}"
        return cls(
            agent=agent, pr=pr,
            pidfile=pathlib.Path(f"{base}.pid"),
            err_log=pathlib.Path(f"{base}-err.log"),
            stdout_log=pathlib.Path(f"{base}-stdout.log"),
            result=pathlib.Path(f"{base}-result.json"),
        )


@dataclass
class AgentStatus:
    agent: str
    status: str = "RUNNING"
    exit_code: int = 0
    pid: Optional[int] = None
    elapsed: float = 0.0
    detail: str = ""
    err_log_size: int = 0
    result_exists: bool = False
    sentinel_seen: bool = False


# ---------- 監視ロジック ----------

def _read_pidfile(p: pathlib.Path) -> Optional[int]:
    try:
        s = p.read_text().strip()
        return int(s) if s else None
    except (FileNotFoundError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    """`kill -0` 相当。0 シグナルを送って例外で判定。"""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


def _pid_cmdline_matches(pid: int, expected: str) -> Optional[bool]:
    """`/proc/<pid>/cmdline` を読んで `expected` を含むか。

    /proc が読めない環境では None を返す（PID 再利用チェック非対応）。
    """
    try:
        cmdline = pathlib.Path(f"/proc/{pid}/cmdline").read_text()
        return expected.lower() in cmdline.lower()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _scan_early_errors(path: pathlib.Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        # 末尾 200KB のみ読む（巨大化対策）
        sz = path.stat().st_size
        with path.open("rb") as f:
            if sz > 200 * 1024:
                f.seek(sz - 200 * 1024)
            data = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None

    for pat in EARLY_ERROR_PATTERNS:
        m = pat.search(data)
        if not m:
            continue
        # 直前後 80 文字を見て benign パターンと重なってないか確認
        start = max(0, m.start() - 40)
        end = min(len(data), m.end() + 40)
        context = data[start:end]
        if any(b.search(context) for b in EARLY_ERROR_BENIGN):
            continue
        # 周辺 1 行を返す
        line_start = data.rfind("\n", 0, m.start()) + 1
        line_end = data.find("\n", m.end())
        line_end = line_end if line_end != -1 else len(data)
        return data[line_start:line_end].strip()
    return None


def _scan_codex_sentinel(path: pathlib.Path) -> bool:
    if not path.exists():
        return False
    try:
        # 末尾 64KB を読む（sentinel は最後の方に出る）
        sz = path.stat().st_size
        with path.open("rb") as f:
            if sz > 64 * 1024:
                f.seek(sz - 64 * 1024)
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return False
    return bool(CODEX_SENTINEL.search(tail))


def monitor_agent(
    agent: str,
    pr: int,
    timeout: int,
    stall_timeout: int,
    poll: int,
    require_result: bool,
    log_prefix: str = "",
) -> AgentStatus:
    """1 agent を監視する。"""
    paths = AgentPaths.for_(agent, pr)
    status = AgentStatus(agent=agent)
    started = time.monotonic()

    # 起動チェック: 30 秒待っても pidfile が無ければ起動失敗
    grace_end = started + 30
    while time.monotonic() < grace_end:
        if paths.pidfile.exists():
            break
        time.sleep(2)
    pid = _read_pidfile(paths.pidfile)
    if pid is None:
        status.status = "PIDFILE_BAD"
        status.exit_code = 6
        status.detail = f"pidfile not found: {paths.pidfile}"
        _emit_log(log_prefix, agent, status)
        return status

    status.pid = pid
    # cmdline 検証 (PID 再利用対策)
    cmdline_ok = _pid_cmdline_matches(pid, agent)
    if cmdline_ok is False:
        status.status = "PIDFILE_BAD"
        status.exit_code = 6
        status.detail = f"pid {pid} cmdline does not contain '{agent}' (stale pidfile?)"
        _emit_log(log_prefix, agent, status)
        return status

    last_err_size = paths.err_log.stat().st_size if paths.err_log.exists() else 0
    last_progress = time.monotonic()

    while True:
        elapsed = time.monotonic() - started
        status.elapsed = elapsed

        # 1. hard timeout
        if elapsed >= timeout:
            status.status = "TIMEOUT"
            status.exit_code = 2
            status.detail = f"hard timeout {timeout}s reached (pid {pid})"
            _emit_log(log_prefix, agent, status)
            return status

        # 2. early error
        err = _scan_early_errors(paths.err_log)
        if err:
            status.status = "EARLY_ERROR"
            status.exit_code = 4
            status.detail = f"early error in err.log: {err[:200]}"
            _emit_log(log_prefix, agent, status)
            return status

        # 3. プロセス生存 + sentinel チェック
        alive = _pid_alive(pid)
        if agent == "codex":
            status.sentinel_seen = _scan_codex_sentinel(paths.err_log)

        if not alive:
            # プロセス終了 — result.json を確認
            status.result_exists = paths.result.exists() and paths.result.stat().st_size > 0
            if status.result_exists or not require_result:
                status.status = "OK"
                status.exit_code = 0
                status.detail = (
                    f"process exited; sentinel={status.sentinel_seen}; "
                    f"result_exists={status.result_exists}"
                )
            else:
                status.status = "NO_RESULT"
                status.exit_code = 3
                status.detail = f"process exited but result.json missing: {paths.result}"
            _emit_log(log_prefix, agent, status)
            return status

        # 4. stall detection
        if paths.err_log.exists():
            cur = paths.err_log.stat().st_size
            status.err_log_size = cur
            if cur != last_err_size:
                last_err_size = cur
                last_progress = time.monotonic()
        if (time.monotonic() - last_progress) >= stall_timeout:
            status.status = "STALLED"
            status.exit_code = 5
            status.detail = (
                f"no err.log progress for {stall_timeout}s "
                f"(pid {pid} still alive, last size {last_err_size}B)"
            )
            _emit_log(log_prefix, agent, status)
            return status

        # poll 中の進捗ログ
        _emit_progress(log_prefix, agent, status, last_err_size)
        time.sleep(poll)


def _emit_progress(prefix: str, agent: str, st: AgentStatus, log_size: int) -> None:
    print(
        f"{prefix}⏳ {agent} elapsed={st.elapsed:.0f}s pid={st.pid} "
        f"err_log={log_size}B sentinel={'Y' if st.sentinel_seen else '-'}",
        file=sys.stderr, flush=True,
    )


def _emit_log(prefix: str, agent: str, st: AgentStatus) -> None:
    icon = {
        "OK": "✅", "TIMEOUT": "⏰", "NO_RESULT": "❌",
        "EARLY_ERROR": "💥", "STALLED": "🛑", "PIDFILE_BAD": "❓",
    }.get(st.status, "?")
    print(
        f"{prefix}{icon} {agent} {st.status} ({st.elapsed:.0f}s) — {st.detail}",
        file=sys.stderr, flush=True,
    )


# ---------- CLI ----------

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pr", type=int)
    p.add_argument("target", choices=["codex", "gemini", "both"])
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"hard timeout in seconds (default: {DEFAULT_TIMEOUT})")
    p.add_argument("--stall-timeout", type=int, default=DEFAULT_STALL,
                   help=f"stall timeout (err.log no progress) in seconds (default: {DEFAULT_STALL})")
    p.add_argument("--poll", type=int, default=DEFAULT_POLL,
                   help=f"poll interval in seconds (default: {DEFAULT_POLL})")
    p.add_argument("--no-require-result", action="store_true",
                   help="プロセス終了後に result.json が無くても OK 扱い")
    args = p.parse_args()

    agents = ["codex", "gemini"] if args.target == "both" else [args.target]
    require_result = not args.no_require_result

    results: dict[str, AgentStatus] = {}

    def run(agent: str) -> None:
        results[agent] = monitor_agent(
            agent=agent, pr=args.pr,
            timeout=args.timeout, stall_timeout=args.stall_timeout,
            poll=args.poll, require_result=require_result,
            log_prefix=f"[{agent}] ",
        )

    threads = [threading.Thread(target=run, args=(a,), daemon=False) for a in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 結果出力: 1 行 1 JSON
    for agent in agents:
        st = results[agent]
        print(json.dumps({
            "agent": agent,
            "status": st.status,
            "exit_code": st.exit_code,
            "pid": st.pid,
            "elapsed": round(st.elapsed, 1),
            "detail": st.detail,
            "err_log_size": st.err_log_size,
            "result_exists": st.result_exists,
            "sentinel_seen": st.sentinel_seen,
        }, ensure_ascii=False))

    # exit code: 全エージェントの最大値（OK=0 が最良、それ以外は失敗）
    sys.exit(max(results[a].exit_code for a in agents))


if __name__ == "__main__":
    main()
