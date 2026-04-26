"""1 testcase 分の evidence (trace / HAR / video / console / pageerror) を集中管理する。

playwright_executor.py から evidence 関連コードを切り出すことで、
- runner 本体は「step を順に回す」ことだけに集中
- listener / tracing / HAR の細かい挙動を単独でテスト可能
- a11y / CWV など追加 evidence を `EvidenceCollectors` に append する形で拡張可能

になる。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page

from scenario_test.config import Config
from scenario_test.testcase import TestCase


@dataclass
class EvidenceCollectors:
    """1 testcase 分の証跡コレクタ。

    `attach_listeners()` で console/pageerror を購読、`start_tracing()` で trace を
    開始、`finalize()` + `confirm_artifacts()` で artifact ファイルを確定する。
    runner 本体はこのオブジェクトを 1 つ持ち回せばよい。
    """

    case_dir: Path
    tc: TestCase
    config: Config
    log_lines: list[str]

    har_path: Path | None = None
    trace_path: Path | None = None
    video_relpath: str | None = None
    har_relpath: str | None = None
    trace_relpath: str | None = None

    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    axe_violations: list[dict[str, Any]] = field(default_factory=list)
    cwv_metrics: dict[str, float] = field(default_factory=dict)
    cwv_passed: bool = True

    # Maj-6: 内部状態は `init=False, repr=False` で外部公開せず、`__post_init__` で
    # 確定する。`for_testcase` で渡す必要もなくなり、ファクトリの API が縮む。
    _trace_started: bool = field(default=False, init=False, repr=False)
    _tolerated_console_re: list[re.Pattern[str]] = field(
        default_factory=list, init=False, repr=False,
    )
    _tolerated_page_re: list[re.Pattern[str]] = field(
        default_factory=list, init=False, repr=False,
    )

    def __post_init__(self) -> None:
        self._tolerated_console_re = [
            re.compile(p) for p in self.config.tolerated_console_errors
        ]
        self._tolerated_page_re = [
            re.compile(p) for p in self.config.tolerated_page_errors
        ]

    # --- 構築 ----------------------------------------------------------

    @classmethod
    def for_testcase(
        cls, *, tc: TestCase, config: Config, case_dir: Path, log_lines: list[str],
    ) -> "EvidenceCollectors":
        return cls(
            case_dir=case_dir,
            tc=tc,
            config=config,
            log_lines=log_lines,
            har_path=case_dir / f"{tc.id}.har",
            trace_path=case_dir / f"{tc.id}.trace.zip",
        )

    # --- HAR / trace / listener の attach ------------------------------

    def context_kwargs(self) -> dict[str, Any]:
        """`browser.new_context(**kwargs)` に渡すべき HAR 関連 kwargs を返す。"""
        return {
            "record_har_path": str(self.har_path),
            "record_har_content": "omit",   # body は trace 側で持つ
        }

    def attach_listeners(self, page: Page) -> None:
        """console / pageerror を `tolerated_*_errors` 経由でフィルタしつつ収集する。"""
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)

    def start_tracing(self, context: BrowserContext) -> None:
        """trace.zip 生成を開始 (config.playwright.enable_trace=True のとき)。"""
        if not self.config.playwright.enable_trace:
            return
        try:
            context.tracing.start(
                name=self.tc.id, title=self.tc.title,
                snapshots=True, screenshots=True, sources=False,
            )
            self._trace_started = True
        except Exception as exc:
            self.log_lines.append(f"[trace] tracing.start 失敗: {exc}")

    # --- 終了処理 ------------------------------------------------------

    def finalize(self, context: BrowserContext) -> None:
        """trace.stop を呼び、HAR/trace の相対 path を確定する。

        context.close() の前に呼ぶ必要がある (HAR は close() 時にフラッシュされる
        ので relpath だけここで確定し、ファイル存在確認は close 後に行う)。
        """
        if self._trace_started and self.trace_path is not None:
            try:
                context.tracing.stop(path=str(self.trace_path))
                self.trace_relpath = self.trace_path.name
            except Exception as exc:
                self.log_lines.append(f"[trace] tracing.stop 失敗: {exc}")

    def confirm_artifacts(self) -> None:
        """context.close() 後に呼び、HAR ファイルの実在を確認して relpath を確定する。"""
        if self.har_path and self.har_path.exists():
            self.har_relpath = self.har_path.name
        else:
            self.log_lines.append(f"[har] HAR ファイル未生成: {self.har_path}")

    # --- listener 実装 -------------------------------------------------

    def _on_console(self, msg) -> None:
        try:
            if msg.type != "error":
                return
            loc = getattr(msg, "location", None) or {}
            text = msg.text[:500]
            for rx in self._tolerated_console_re:
                if rx.search(text):
                    return
            self.console_errors.append(f"{loc.get('url', '?')}: {text}")
        except Exception as exc:
            self.log_lines.append(f"[console listener] error: {exc}")

    def _on_pageerror(self, exc) -> None:
        try:
            text = str(exc)[:1000]
            for rx in self._tolerated_page_re:
                if rx.search(text):
                    return
            self.page_errors.append(text)
        except Exception as listener_exc:
            self.log_lines.append(f"[pageerror listener] error: {listener_exc}")

    # --- 集計 ---------------------------------------------------------

    @property
    def has_runtime_errors(self) -> bool:
        return bool(self.console_errors or self.page_errors)

    def runtime_error_summary(self) -> str:
        parts: list[str] = []
        if self.page_errors:
            parts.append(f"pageerror {len(self.page_errors)} 件")
        if self.console_errors:
            parts.append(f"console.error {len(self.console_errors)} 件")
        return "Runtime errors detected: " + ", ".join(parts) if parts else ""

    def append_log(self) -> None:
        """case_dir/log.txt に書き出す前に集計サマリを log_lines に注ぐ。"""
        if self.console_errors:
            self.log_lines.append(f"[console.error] {len(self.console_errors)} 件:")
            for line in self.console_errors[:10]:
                self.log_lines.append(f"  {line}")
        if self.page_errors:
            self.log_lines.append(f"[pageerror] {len(self.page_errors)} 件:")
            for line in self.page_errors[:10]:
                self.log_lines.append(f"  {line}")
        if self.axe_violations:
            self.log_lines.append(f"[a11y] axe-core 違反 {len(self.axe_violations)} 件:")
            for v in self.axe_violations[:5]:
                # Min-4: scan_page は 'help' を格納する (description は格納しない)。
                self.log_lines.append(
                    f"  {v.get('id')} ({v.get('impact', '?')}): "
                    f"{(v.get('help') or '')[:120]}",
                )
        if self.cwv_metrics:
            self.log_lines.append(
                "[cwv] " + ", ".join(f"{k}={v:.1f}" for k, v in self.cwv_metrics.items())
                + (" (PASS)" if self.cwv_passed else " (FAIL)")
            )
