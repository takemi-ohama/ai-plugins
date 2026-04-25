"""Playwright タイプのテストケースを 1 件実行する。

並列実行を前提に、各テストケースは独自の Playwright インスタンス・
独自の BrowserContext (動画記録) で完結する。
"""

from __future__ import annotations

import datetime as _dt
import re
import traceback
from pathlib import Path

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Response,
    sync_playwright,
)

from scenario_test.config import (
    BodyCheckConfig,
    Config,
    Login,
    Role,
    SlugConfig,
)
from scenario_test.hud import (
    HUD_INIT_SCRIPT,
    flash_click,
    hide_cursor,
    set_caption,
)
from scenario_test.nav_helpers import (
    clamp_to_viewport,
    detect_body_errors,
    find_click_target,
    navigate_post,
    scroll_demo,
    slug_for,
    submit_login,
    take_screenshot,
)
from scenario_test.testcase import (
    NavStep,
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
    har_relpath: str | None = None,
    console_errors: list[str] | None = None,
    page_errors: list[str] | None = None,
) -> TestCaseResult:
    """TestCaseResult を簡潔に構築するファクトリ。"""
    return TestCaseResult(
        testcase_id=tc.id, title=tc.title, phase=tc.phase, type=tc.type,
        role=tc.role, priority=tc.priority, tags=tc.tags,
        started_at=started, finished_at=_dt.datetime.now(),
        case_dir=case_dir, ok=ok, error=error,
        video_relpath=video_relpath,
        steps=steps or [],
        nav_vars=nav_vars or {},
        page_role=list(tc.page_role),
        har_relpath=har_relpath,
        console_errors=console_errors or [],
        page_errors=page_errors or [],
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
    step_delay_ms: int,
    log_lines: list[str],
    screenshots_dir: Path,
) -> tuple[bool, str, Path | None, str]:
    """ログインを実施し (成功, 詳細, スクショ, 結果サマリ短文) を返す。"""
    url = f"{base_url}{login.path}"
    set_caption(
        page, previous="(シナリオ開始)",
        next_action=f"{role_label} のログインページを開く: {login.path}",
    )
    page.goto(url, wait_until="domcontentloaded")
    log_lines.append(f"[login] open {url}")
    set_caption(
        page, previous=f"{role_label} のログインページを表示",
        next_action=f"認証情報を入力して送信 ({', '.join(login.fields.keys())})",
    )
    _safe_wait(page, step_delay_ms)

    for name, value in login.fields.items():
        page.fill(f'input[name="{name}"]', value)
    log_lines.append(f"[login] fill {list(login.fields.keys())}")

    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=nav_timeout_ms):
            submit_login(page, selectors=login.submit_selectors)
    except Exception as exc:  # noqa: BLE001
        log_lines.append(f"[login] navigation 失敗: {exc}")
        shot = take_screenshot(page, screenshots_dir / "00-login-failed.png")
        return False, f"navigation 失敗: {type(exc).__name__}: {exc}", shot, (
            f"{role_label} ログイン navigation 失敗"
        )

    final_url = page.url
    ok = login.fail_if_url_contains not in final_url
    log_lines.append(f"[login] -> {final_url} ({'OK' if ok else 'STILL ON LOGIN'})")
    shot = take_screenshot(page, screenshots_dir / "00-after-login.png")
    return (
        ok,
        f"final_url={final_url}",
        shot,
        f"{role_label} ログイン{'成功' if ok else '失敗'} → {final_url}",
    )


def _resolve_template(
    text: str, nav_vars: dict[str, str],
) -> tuple[str | None, str | None]:
    """`{name}` 形式のテンプレートを nav_vars で展開。失敗時は (None, missing_key)。"""
    try:
        return text.format(**nav_vars), None
    except KeyError as exc:
        return None, str(exc).strip("'\"")


def _flash_click_target(
    page: Page,
    click_target_abs: tuple[int, int],
) -> tuple[int, int]:
    """絶対座標 → viewport 相対に直し、HUD リップルを発火させる。"""
    try:
        scroll_y_now = int(page.evaluate("() => window.scrollY"))
    except Exception:
        scroll_y_now = 0
    viewport = page.viewport_size or {"width": 1280, "height": 800}
    flash_xy = clamp_to_viewport(
        (click_target_abs[0], click_target_abs[1] - scroll_y_now),
        viewport["width"], viewport["height"],
    )
    flash_click(page, flash_xy[0], flash_xy[1], settle_ms=300)
    return flash_xy


def _judge_response(
    step: NavStep,
    page_url: str,
    status: int,
    content_type: str,
    body_text: str,
    fail_if_url_contains: str,
    body_check: BodyCheckConfig,
) -> tuple[bool, list[str]]:
    """ステップの成否と詳細メッセージリストを判定する。"""
    fatal_error, file_not_found, warning_pattern = (False, False, "")
    if "image/" not in content_type:
        fatal_error, file_not_found, warning_pattern = detect_body_errors(
            body_text,
            fatal_patterns=body_check.fatal_patterns,
            warning_patterns=body_check.warning_patterns,
            not_found_strings=body_check.not_found_strings,
        )

    ct_ok = (not step.expect_content_type) or step.expect_content_type in content_type
    url_contains_ok = (not step.expect_url_contains) or step.expect_url_contains in page_url
    still_on_login = fail_if_url_contains in page_url

    ok = (
        status == step.expect_status
        and ct_ok
        and url_contains_ok
        and not fatal_error
        and not file_not_found
        and not warning_pattern
        # expect_url_contains 指定 (logout 確認等) ではログイン画面に戻ってよい
        and (not still_on_login or step.expect_url_contains is not None)
    )

    detail = [f"status={status}", f"ct={content_type or '-'}", f"final_url={page_url}"]
    if fatal_error:
        detail.append("致命エラーパターンを検出")
    if file_not_found:
        detail.append("File not found 系文字列を検出")
    if warning_pattern:
        detail.append(f"警告パターン '{warning_pattern}' がページ先頭に漏れています")
    if still_on_login and step.expect_url_contains is None:
        detail.append("ログインページに留まっています")
    if not ct_ok:
        detail.append(f"Content-Type 不一致 (期待: {step.expect_content_type})")
    if not url_contains_ok:
        detail.append(f"URL に '{step.expect_url_contains}' を含まない")
    return ok, detail


def _apply_extracts(
    step: NavStep,
    html: str,
    nav_vars: dict[str, str],
) -> list[str]:
    """step.extract に従って HTML から変数を抽出し、結果メッセージを返す。"""
    if not step.extract:
        return []
    extracted = []
    for var_name, pattern in step.extract.items():
        m = re.search(pattern, html)
        if m and m.groups():
            nav_vars[var_name] = m.group(1)
            extracted.append(f"{var_name}={m.group(1)}")
    msgs = []
    if extracted:
        msgs.append(f"抽出: {', '.join(extracted)}")
    not_found = [v for v in step.extract if v not in nav_vars]
    if not_found:
        msgs.append(f"未抽出: {', '.join(not_found)}")
    return msgs


def _run_nav_step(
    page: Page,
    step: NavStep,
    idx: int,
    base_url: str,
    nav_vars: dict[str, str],
    fail_if_url_contains: str,
    screenshots_dir: Path,
    log_lines: list[str],
    *,
    body_check: BodyCheckConfig,
    slug_config: SlugConfig,
    nav_timeout_ms: int = 30000,
    next_action_text: str = "",
    hud_scroll_demo: bool = True,
) -> tuple[StepRecord, str]:
    """1 ステップを実行し (StepRecord, 結果サマリ短文) を返す。"""
    step_label = f"[{idx:02d}] {step.name}"

    def fail(msg: str, summary_suffix: str) -> tuple[StepRecord, str]:
        return (
            StepRecord(name=step_label, ok=False, detail=msg),
            f"{step_label} ({summary_suffix})",
        )

    # skip_if_missing
    missing = [v for v in step.skip_if_missing if v not in nav_vars]
    if missing:
        log_lines.append(f"[step{idx:02d}] SKIP (vars missing): {missing}")
        return (
            StepRecord(name=step_label, ok=True, detail=f"skipped: 変数未抽出 {missing}"),
            f"{step_label} (スキップ: 変数未抽出)",
        )

    # path / data のテンプレート展開
    path_resolved, missing_key = _resolve_template(step.path, nav_vars)
    if path_resolved is None:
        return fail(f"path テンプレート展開失敗: 未抽出 {missing_key}", "path 展開失敗")

    post_data: dict[str, str] = {}
    for k, v in step.data.items():
        resolved, missing_key = _resolve_template(v, nav_vars)
        if resolved is None:
            return fail(f"data テンプレート展開失敗: 未抽出 {missing_key}", "data 展開失敗")
        post_data[k] = resolved

    target_url = f"{base_url}{path_resolved}"
    log_lines.append(
        f"[step{idx:02d}] {step.method} {target_url}"
        + (f" data={list(post_data.keys())}" if post_data else "")
    )

    # 1) クリック対象を絶対座標で取得 (None の場合はスクロールも最上部に戻す)
    click_target_abs = find_click_target(page, path_resolved, step.method, post_data)

    # 2) スクロールデモ
    if hud_scroll_demo:
        return_to_y = max(0, click_target_abs[1] - 100) if click_target_abs else 0
        if scroll_demo(page, return_to_y=return_to_y, pause_ms=500):
            log_lines.append(
                f"[step{idx:02d}] scroll-demo executed (return_to_y={return_to_y})"
            )

    # 3) クリック対象が見つかれば擬似クリック発火、見つからなければカーソル非表示
    if click_target_abs is not None:
        flash_xy = _flash_click_target(page, click_target_abs)
        log_lines.append(
            f"[step{idx:02d}] click target abs={click_target_abs} viewport={flash_xy}"
        )
    else:
        hide_cursor(page)
        log_lines.append(f"[step{idx:02d}] click target not found — hide cursor")

    # 4) ナビゲーション
    response: Response | None
    try:
        if step.method == "POST":
            response = navigate_post(page, target_url, post_data, nav_timeout_ms)
        else:
            response = page.goto(target_url, wait_until="domcontentloaded")
    except Exception as exc:  # noqa: BLE001
        log_lines.append(f"[step{idx:02d}] navigation 失敗: {exc}")
        return fail(f"navigation 失敗: {type(exc).__name__}: {exc}", "遷移失敗")

    status = response.status if response else 0
    content_type = response.headers.get("content-type", "") if response else ""

    body_text = ""
    if "image/" not in content_type:
        try:
            body_text = page.locator("body").inner_text(timeout=2000)
        except Exception:
            pass

    ok, detail_parts = _judge_response(
        step, page.url, status, content_type, body_text, fail_if_url_contains,
        body_check,
    )

    # 抽出
    if step.extract and "image/" not in content_type:
        try:
            html = page.content()
        except Exception:
            html = ""
        detail_parts.extend(_apply_extracts(step, html, nav_vars))

    # 字幕更新 → スクショ
    summary = f"{step_label} → HTTP {status} ({'OK' if ok else 'FAIL'})"
    set_caption(page, previous=summary, next_action=next_action_text)
    _safe_wait(page, 150)
    slug = slug_for(
        path_resolved,
        strip_extensions=slug_config.strip_extensions,
        query_capture_re=slug_config.query_capture_re,
    )
    shot_target = screenshots_dir / f"{idx:02d}-{slug}.png"
    saved = take_screenshot(page, shot_target)

    log_lines.append(
        f"[step{idx:02d}] {'OK' if ok else 'FAIL'} status={status} url={page.url}"
    )
    return (
        StepRecord(
            name=step_label, ok=ok,
            detail=" / ".join(detail_parts),
            screenshot_relpath=saved.name if saved else None,
        ),
        summary,
    )


def _next_action_text_factory(tc: TestCase) -> "callable[[int], str]":
    """after_idx ステップ完了後の「次にやること」を返すクロージャ。"""
    total_steps = len(tc.steps)

    def _f(after_idx: int) -> str:
        if after_idx == 0:
            if total_steps == 0:
                return "ログアウト/シナリオ完了"
            return f"[01/{total_steps:02d}] {tc.steps[0].name}"
        if after_idx >= total_steps:
            return "シナリオ完了"
        return f"[{after_idx + 1:02d}/{total_steps:02d}] {tc.steps[after_idx].name}"

    return _f


def _start_tracing(context: BrowserContext, tc: TestCase, log_lines: list[str]) -> bool:
    try:
        context.tracing.start(
            name=tc.id, title=tc.title,
            snapshots=True, screenshots=True, sources=False,
        )
        return True
    except Exception as exc:
        log_lines.append(f"[trace] tracing.start 失敗: {exc}")
        return False


def _save_video(
    video_handle, case_dir: Path, tc_id: str, video_format: str,
    log_lines: list[str],
) -> str | None:
    """動画ファイルを確定し、必要なら mp4 変換する。final relpath を返す。

    `video_handle.path()` は sync_playwright() ブロック内でしか呼べない。
    """
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
    converted = convert_webm_to_mp4(webm_path, mp4_path)
    if converted is None:
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


def run_playwright_testcase(
    tc: TestCase,
    config: Config,
    case_dir: Path,
) -> TestCaseResult:
    """Playwright タイプのテストケースを実行する。

    1 ケース = 1 sync_playwright インスタンス = 1 動画。
    """
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
    har_path = case_dir / f"{tc.id}.har"
    har_relpath: str | None = None
    console_errors: list[str] = []
    page_errors: list[str] = []
    next_action_text = _next_action_text_factory(tc)

    # 重要: video.path() は sync_playwright() ブロック内でしか呼べない。
    # よって動画ファイルの確定は with ブロックの中で行う。
    try:
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(
                headless=pw.headless, slow_mo=pw.slow_mo_ms or 0,
            )
            ctx_kwargs: dict = {
                "ignore_https_errors": not config.verify_tls,
                "viewport": {"width": pw.viewport_width, "height": pw.viewport_height},
                "record_video_dir": str(videos_dir),
                "record_video_size": {"width": pw.video_width, "height": pw.video_height},
                # HAR (HTTP Archive) を自動収集。bug report で network 往復を再現するため。
                # docs/05-bug-report.md の evidence 必須項目。
                "record_har_path": str(har_path),
                "record_har_content": "omit",   # body は trace 側で持つので重複回避
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

            tracing_started = pw.enable_trace and _start_tracing(context, tc, log_lines)

            page = context.new_page()

            # docs/checklists/checklist-common.md C8: console.error / pageerror を
            # 自動収集する。検出件数が >0 の testcase は無条件 FAIL とする (後段で集計)。
            def _on_console(msg) -> None:
                try:
                    if msg.type == "error":
                        console_errors.append(f"{msg.location.get('url', '?')}: {msg.text[:500]}")
                except Exception:
                    pass

            def _on_pageerror(exc) -> None:
                try:
                    page_errors.append(str(exc)[:1000])
                except Exception:
                    pass

            page.on("console", _on_console)
            page.on("pageerror", _on_pageerror)

            video_handle = page.video

            try:
                # --- ログイン ---
                login_ok, login_detail, _shot, login_summary = _do_login(
                    page, config.base_url, role.login, role.label,
                    pw.navigation_timeout_ms, pw.step_delay_ms,
                    log_lines, case_dir,
                )
                steps_records.append(StepRecord(
                    name="[login] ログイン",
                    ok=login_ok, detail=login_detail,
                    screenshot_relpath=(
                        "00-after-login.png" if login_ok else "00-login-failed.png"
                    ),
                ))
                last_summary = login_summary
                set_caption(page, previous=last_summary, next_action=next_action_text(0))
                _safe_wait(page, pw.step_delay_ms)

                # ログイン後 URL アサーション
                for forbid in tc.post_login_url_must_not_contain:
                    contains = forbid in page.url
                    steps_records.append(StepRecord(
                        name=f"[login] post_login URL に '{forbid}' を含まないこと",
                        ok=not contains, detail=f"final_url={page.url}",
                    ))

                # --- ステップ実行 (ログイン成功時のみ) ---
                if login_ok:
                    for idx, step in enumerate(tc.steps, start=1):
                        set_caption(
                            page, previous=last_summary,
                            next_action=f"[{idx:02d}/{len(tc.steps):02d}] {step.name}",
                        )
                        rec, last_summary = _run_nav_step(
                            page, step, idx, config.base_url, nav_vars,
                            role.login.fail_if_url_contains,
                            case_dir, log_lines,
                            body_check=config.body_check,
                            slug_config=config.slug,
                            nav_timeout_ms=pw.navigation_timeout_ms,
                            next_action_text=next_action_text(idx),
                            hud_scroll_demo=pw.enable_scroll_demo,
                        )
                        steps_records.append(rec)
                        _safe_wait(page, pw.step_delay_ms)
                else:
                    log_lines.append("[login] FAILED — steps を skip")
            finally:
                if tracing_started:
                    try:
                        trace_path = case_dir / f"{tc.id}.trace.zip"
                        context.tracing.stop(path=str(trace_path))
                        log_lines.append(f"[trace] saved: {trace_path}")
                    except Exception as exc:
                        log_lines.append(f"[trace] stop 失敗: {exc}")

                # 動画 / HAR は context.close() で初めてファイルに書き出される
                try:
                    page.close()
                except Exception:
                    pass
                try:
                    context.close()
                except Exception as exc:
                    log_lines.append(f"[video] context.close 失敗: {exc}")

                final_video_rel = _save_video(
                    video_handle, case_dir, tc.id, pw.video_format, log_lines,
                )

                if har_path.exists():
                    har_relpath = har_path.name
                    log_lines.append(f"[har] saved: {har_path.name}")

                if console_errors:
                    log_lines.append(f"[console.error] {len(console_errors)} 件:")
                    for line in console_errors[:10]:
                        log_lines.append(f"    {line}")
                if page_errors:
                    log_lines.append(f"[pageerror] {len(page_errors)} 件:")
                    for line in page_errors[:10]:
                        log_lines.append(f"    {line}")

                try:
                    browser.close()
                except Exception:
                    pass
    except Exception as exc:  # noqa: BLE001
        error_msg = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        log_lines.append(f"[FATAL] {error_msg}")

    # 中間 _video_tmp ディレクトリのクリーンアップ
    try:
        for f in videos_dir.glob("*"):
            f.unlink()
        videos_dir.rmdir()
    except Exception:
        pass

    (case_dir / "log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    # docs/checklists/checklist-common.md C8.1/C8.2: pageerror または console.error が
    # 1 件でも検出されたら無条件 FAIL。
    has_runtime_errors = bool(console_errors or page_errors)
    overall_ok = (
        (not error_msg)
        and all(s.ok for s in steps_records)
        and not has_runtime_errors
    )
    final_error = error_msg
    if has_runtime_errors and not final_error:
        parts = []
        if page_errors:
            parts.append(f"pageerror {len(page_errors)} 件")
        if console_errors:
            parts.append(f"console.error {len(console_errors)} 件")
        final_error = "Runtime errors detected: " + ", ".join(parts)

    return _result(
        tc, case_dir, started, ok=overall_ok, error=final_error,
        video_relpath=final_video_rel, steps=steps_records, nav_vars=nav_vars,
        har_relpath=har_relpath,
        console_errors=console_errors, page_errors=page_errors,
    )
