"""Playwright タイプのテストケースを 1 件実行する (locator-first / web-first)。

v0.3.0 で完全に locator-first 化:
- step は YAML スキーマ上で `kind` (`goto`/`click`/`fill`/`expect_*`...) を持つ
- 実行は `locator_steps.execute_step()` に委譲
- evidence (HAR / trace / console / pageerror) は `evidence.EvidenceCollectors`
- a11y / CWV は page_role に応じて runner が自動付加 (`a11y.py` / `cwv.py`)

`run_playwright_testcase()` は 1 testcase = 1 sync_playwright instance = 1 動画。
"""

from __future__ import annotations

import datetime as _dt
import re as _re
from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    sync_playwright,
)

from scenario_test import a11y as a11y_mod
from scenario_test import cwv as cwv_mod
from scenario_test.config import Config, Login, Role
from scenario_test.evidence import EvidenceCollectors
from scenario_test.hud import (
    HUD_INIT_SCRIPT,
    set_caption,
)
from scenario_test.locator_steps import StepContext, execute_step
from scenario_test.testcase import (
    StepRecord,
    TestCase,
    TestCaseResult,
)
from scenario_test.video import convert_webm_to_mp4


def _result(
    tc: TestCase, case_dir: Path, started: _dt.datetime,
    *, ok: bool, error: str = "",
    video_relpath: str | None = None,
    steps: list[StepRecord] | None = None,
    nav_vars: dict[str, str] | None = None,
    ev: EvidenceCollectors | None = None,
) -> TestCaseResult:
    return TestCaseResult(
        testcase_id=tc.id, title=tc.title, phase=tc.phase, type=tc.type,
        role=tc.role, priority=tc.priority, tags=tc.tags,
        started_at=started, finished_at=_dt.datetime.now(),
        case_dir=case_dir, ok=ok, error=error,
        video_relpath=video_relpath,
        steps=steps or [],
        nav_vars=nav_vars or {},
        page_role=list(tc.page_role),
        har_relpath=ev.har_relpath if ev else None,
        console_errors=ev.console_errors if ev else [],
        page_errors=ev.page_errors if ev else [],
        axe_violations=ev.axe_violations if ev else [],
        cwv_metrics=ev.cwv_metrics if ev else {},
        cwv_passed=ev.cwv_passed if ev else True,
    )


def _safe_wait(page: Page, ms: int) -> None:
    if ms <= 0:
        return
    try:
        page.wait_for_timeout(ms)
    except Exception:
        pass


def _do_login(
    page: Page,
    base_url: str,
    login: Login,
    role_label: str,
    nav_timeout_ms: int,
    log_lines: list[str],
) -> tuple[bool, str, str]:
    """ログインを実施し (成功, 詳細, 結果サマリ短文) を返す。"""
    url = f"{base_url}{login.path}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout_ms)
    except Exception as exc:
        return False, f"login page open failed: {exc}", f"{role_label} ログインページ表示失敗"
    log_lines.append(f"[login] open {url}")

    for name, value in login.fields.items():
        try:
            page.locator(f'input[name="{name}"]').fill(value, timeout=nav_timeout_ms)
        except Exception as exc:
            return False, f"fill {name!r} failed: {exc}", f"{role_label} {name!r} 入力失敗"
    log_lines.append(f"[login] fill {list(login.fields.keys())}")

    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=nav_timeout_ms):
            _submit_login_form(page, login)
    except Exception as exc:
        log_lines.append(f"[login] navigation 失敗: {exc}")
        return False, f"navigation 失敗: {type(exc).__name__}: {exc}", (
            f"{role_label} ログイン navigation 失敗"
        )

    final_url = page.url
    ok = login.fail_if_url_contains not in final_url
    log_lines.append(f"[login] -> {final_url} ({'OK' if ok else 'STILL ON LOGIN'})")
    return (
        ok,
        f"final_url={final_url}",
        f"{role_label} ログイン{'成功' if ok else '失敗'} → {final_url}",
    )


def _submit_login_form(page: Page, login: Login) -> None:
    """submit ボタンを click し、なければ password で Enter する。"""
    for sel in login.submit_selectors:
        try:
            page.locator(sel).first.click(timeout=2000)
            return
        except Exception:
            continue
    # 公式推奨セレクタへフォールバック (role / type=submit)
    for fallback in (
        'role=button[name=/login|sign.?in|ログイン/i]',
        'button[type="submit"]',
        'input[type="submit"]',
    ):
        try:
            page.locator(fallback).first.click(timeout=2000)
            return
        except Exception:
            continue
    # 最後の手段: Password フィールドで Enter
    pw_field = next(
        (n for n in login.fields if "pass" in n.lower() or "pwd" in n.lower()),
        None,
    )
    if pw_field:
        page.locator(f'input[name="{pw_field}"]').press("Enter")
        return
    raise RuntimeError("ログイン送信ボタンが見つかりません (submit_selectors を設定してください)")


_FILENAME_SAFE_RE = _re.compile(r"[^\w\-]+")


def _screenshot_slug(name: str, fallback: str = "step") -> str:
    s = _FILENAME_SAFE_RE.sub("-", name).strip("-").lower()
    return s[:60] or fallback


def _take_screenshot(page: Page, target: Path) -> Path | None:
    try:
        page.screenshot(path=str(target), full_page=False)
        return target
    except Exception:
        return None


def _save_video(
    video_handle, case_dir: Path, tc_id: str, video_format: str,
    log_lines: list[str],
) -> str | None:
    if video_handle is None:
        return None
    try:
        tmp_path = Path(video_handle.path())
    except Exception as exc:
        log_lines.append(f"[video] save failed: {exc}")
        return None
    if not tmp_path.exists():
        log_lines.append(f"[video] tmp file not found at {tmp_path}")
        return None

    webm_path = case_dir / f"{tc_id}.webm"
    if webm_path.exists():
        webm_path.unlink()
    tmp_path.rename(webm_path)
    log_lines.append(f"[video] saved (webm): {webm_path}")

    if video_format != "mp4":
        return webm_path.name

    mp4_path = case_dir / f"{tc_id}.mp4"
    if convert_webm_to_mp4(webm_path, mp4_path) is None:
        log_lines.append("[video] mp4 conversion failed — keeping webm")
        return webm_path.name

    try:
        webm_path.unlink()
    except Exception:
        pass
    log_lines.append(
        f"[video] converted to mp4: {mp4_path} ({mp4_path.stat().st_size:,} bytes)"
    )
    return mp4_path.name


def _run_a11y(
    page: Page, tc: TestCase, config: Config,
    ev: EvidenceCollectors, log_lines: list[str],
) -> StepRecord | None:
    if not config.a11y.enabled:
        return None
    if not a11y_mod.should_auto_scan(tc.page_role, auto_roles=frozenset(config.a11y.auto_roles)):
        return None
    violations = a11y_mod.scan_page(page, tags=tuple(config.a11y.tags))
    ev.axe_violations = violations
    n = len(violations)
    if not violations:
        return StepRecord(name="[a11y] axe-core scan", ok=True, detail="0 violations")
    detail = f"{n} violations: " + ", ".join(
        f"{v.get('id')}({v.get('impact', '?')})" for v in violations[:5]
    )
    log_lines.append(f"[a11y] {n} violations detected (impact: critical/serious/moderate/minor)")
    ok = not config.a11y.fail_on_violations
    return StepRecord(name="[a11y] axe-core scan", ok=ok, detail=detail)


def _run_cwv(
    page: Page, tc: TestCase, config: Config,
    ev: EvidenceCollectors, log_lines: list[str],
) -> StepRecord | None:
    if not config.cwv.enabled:
        return None
    if not cwv_mod.should_auto_measure(tc.page_role, auto_roles=frozenset(config.cwv.auto_roles)):
        return None
    metrics = cwv_mod.measure_page(page, observe_ms=config.cwv.observe_ms)
    ev.cwv_metrics = metrics
    ev.cwv_passed = cwv_mod.passed(metrics)
    detail = ", ".join(
        f"{k}={v:.1f}({cwv_mod.judge(k, v)})" for k, v in metrics.items()
    ) or "no metrics collected"
    log_lines.append(f"[cwv] {detail}")
    ok = ev.cwv_passed or not config.cwv.fail_on_poor
    return StepRecord(name="[cwv] Core Web Vitals", ok=ok, detail=detail)


def run_playwright_testcase(
    tc: TestCase,
    config: Config,
    case_dir: Path,
) -> TestCaseResult:
    """Playwright タイプのテストケースを実行する。"""
    started = _dt.datetime.now()
    case_dir.mkdir(parents=True, exist_ok=True)
    videos_dir = case_dir / "_video_tmp"
    videos_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    if not tc.role:
        return _result(
            tc, case_dir, started, ok=False,
            error="playwright タイプのテストケースには role が必須です",
        )
    try:
        role: Role = config.role(tc.role)
    except KeyError as exc:
        return _result(tc, case_dir, started, ok=False, error=str(exc))

    pw = config.playwright
    nav_vars: dict[str, str] = {}
    steps_records: list[StepRecord] = []
    error_msg = ""
    final_video_rel: str | None = None
    ev = EvidenceCollectors.for_testcase(
        tc=tc, config=config, case_dir=case_dir, log_lines=log_lines,
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=pw.headless, slow_mo=pw.slow_mo_ms)

            ctx_kwargs: dict = {
                "ignore_https_errors": not config.verify_tls,
                "viewport": {"width": pw.viewport_width, "height": pw.viewport_height},
                "record_video_dir": str(videos_dir),
                "record_video_size": {"width": pw.video_width, "height": pw.video_height},
                **ev.context_kwargs(),
            }
            if role.login.requires_basic_auth:
                ctx_kwargs["http_credentials"] = {
                    "username": config.basic_auth.user,
                    "password": config.basic_auth.password,
                }

            context: BrowserContext = browser.new_context(**ctx_kwargs)
            context.set_default_navigation_timeout(pw.navigation_timeout_ms)
            context.set_default_timeout(pw.navigation_timeout_ms)

            if pw.enable_overlay:
                try:
                    context.add_init_script(HUD_INIT_SCRIPT)
                except Exception as exc:
                    log_lines.append(f"[overlay] add_init_script 失敗: {exc}")

            ev.start_tracing(context)

            page = context.new_page()
            ev.attach_listeners(page)
            video_handle = page.video

            try:
                # --- ログイン ---
                login_ok, login_detail, login_summary = _do_login(
                    page, config.base_url, role.login, role.label,
                    pw.navigation_timeout_ms, log_lines,
                )
                steps_records.append(StepRecord(
                    name="[login] ログイン", ok=login_ok, detail=login_detail,
                ))
                last_summary = login_summary

                # post_login URL アサーション
                for forbid in tc.post_login.url_must_not_contain:
                    contains = forbid in page.url
                    steps_records.append(StepRecord(
                        name=f"[login] post_login URL に '{forbid}' を含まないこと",
                        ok=not contains, detail=f"final_url={page.url}",
                    ))

                # --- ステップ実行 ---
                if login_ok:
                    step_ctx = StepContext(
                        page=page, base_url=config.base_url,
                        nav_vars=nav_vars,
                        default_timeout_ms=pw.navigation_timeout_ms,
                    )
                    total = len(tc.steps)
                    for idx, step in enumerate(tc.steps, start=1):
                        set_caption(
                            page, previous=last_summary,
                            next_action=f"[{idx:02d}/{total:02d}] {step.name}",
                        )
                        rec = execute_step(step, step_ctx)
                        # スクショ
                        slug = _screenshot_slug(step.name, f"step{idx:02d}")
                        shot = _take_screenshot(page, case_dir / f"{idx:02d}-{slug}.png")
                        if shot:
                            rec.screenshot_relpath = shot.name
                        last_summary = (
                            f"[{idx:02d}] {step.name} → {'OK' if rec.ok else 'FAIL'}"
                        )
                        log_lines.append(
                            f"[step{idx:02d}] {'OK' if rec.ok else 'FAIL'}: {rec.detail}"
                        )
                        steps_records.append(rec)
                        _safe_wait(page, pw.step_delay_ms)
                else:
                    log_lines.append("[login] FAILED — steps を skip")

                # --- a11y / CWV 自動付加 ---
                if login_ok:
                    rec = _run_a11y(page, tc, config, ev, log_lines)
                    if rec is not None:
                        steps_records.append(rec)
                    rec = _run_cwv(page, tc, config, ev, log_lines)
                    if rec is not None:
                        steps_records.append(rec)
            finally:
                ev.finalize(context)
                try:
                    context.close()
                except Exception as exc:
                    log_lines.append(f"[ctx.close] {exc}")

            try:
                browser.close()
            except Exception:
                pass

            final_video_rel = _save_video(
                video_handle, case_dir, tc.id, pw.video_format, log_lines,
            )
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        log_lines.append(f"[fatal] {error_msg}")

    # context.close() 後 HAR が確定する
    ev.confirm_artifacts()
    ev.append_log()

    # videos_dir 後始末
    try:
        for f in videos_dir.glob("*"):
            f.unlink()
        videos_dir.rmdir()
    except Exception:
        pass

    (case_dir / "log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    final_error = error_msg
    if ev.has_runtime_errors and not final_error:
        final_error = ev.runtime_error_summary()

    overall_ok = (
        not error_msg
        and all(s.ok for s in steps_records)
        and not ev.has_runtime_errors
    )

    return _result(
        tc, case_dir, started, ok=overall_ok, error=final_error,
        video_relpath=final_video_rel, steps=steps_records, nav_vars=nav_vars,
        ev=ev,
    )
