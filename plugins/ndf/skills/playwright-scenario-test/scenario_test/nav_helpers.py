"""Playwright 実行器が使うナビゲーション周りのヘルパー群。"""

from __future__ import annotations

import html as _html
import re
from pathlib import Path

from playwright.sync_api import Page, Response


# --- ログインフォーム送信 -----------------------------------------------------

# 汎用フォールバック: ほとんどの HTML ログインフォームに通用するセレクタ
_DEFAULT_LOGIN_SUBMIT_SELECTORS = (
    'form input[type="image"]',
    'form button[type="submit"]',
    'form input[type="submit"]',
)


def submit_login(
    page: Page,
    *,
    selectors: tuple[str, ...] | list[str] = (),
    password_field: str = "Password",
) -> None:
    """ログインフォームを送信する。

    `selectors` が指定されていればそちらを優先で試し、続いて汎用フォールバックを試し、
    最後に password_field 名の input で Enter を打つ。
    どれにもマッチしなければ RuntimeError。
    """
    for sel in (*selectors, *_DEFAULT_LOGIN_SUBMIT_SELECTORS):
        try:
            locator = page.locator(sel).first
            if locator.count() > 0:
                locator.click()
                return
        except Exception:
            continue
    pw = page.locator(f'input[name="{password_field}"]').first
    if pw.count() > 0:
        pw.press("Enter")
        return
    raise RuntimeError("ログイン送信ボタンが見つかりません")


# --- スクショ + ファイル名スラッグ -------------------------------------------

def slug_for(
    path_resolved: str,
    *,
    strip_extensions: tuple[str, ...] | list[str] = (),
    query_capture_re: str | None = None,
) -> str:
    """スクショファイル名用のスラッグを path から作る。

    - strip_extensions: 削除する拡張子 (例: [".php"])
    - query_capture_re: クエリ部分から拾うサフィックス (例: r"Cmd=(\\w+)")
    """
    base = path_resolved.split("?")[0].strip("/").replace("/", "_") or "root"
    for ext in strip_extensions:
        base = base.replace(ext, "")
    if query_capture_re:
        m = re.search(query_capture_re, path_resolved)
        if m and m.groups():
            base += f"-{m.group(1)}"
    return base or "root"


def take_screenshot(page: Page, target: Path) -> Path | None:
    """ビューポート (1280x800) のスクショを撮る。

    full_page=True だと Chromium が fixed 要素のテキストを描画切れさせるため、
    HUD オーバーレイを確実に映すためにビューポート領域のみで撮る。動画もビューポート
    録画なので、エビデンスとして整合する。
    """
    try:
        page.screenshot(path=str(target), full_page=False)
        return target
    except Exception:
        return None


# --- スクロールデモ ---------------------------------------------------------

_SCROLL_INFO_JS = """() => ({
    height: document.documentElement.scrollHeight,
    viewport_height: window.innerHeight,
    scrollY: window.scrollY,
})"""


def scroll_demo(
    page: Page,
    *,
    return_to_y: int | None = None,
    pause_ms: int = 600,
) -> bool:
    """ページが viewport より長ければ最下部までスクロール → 元 (またはクリック対象 Y) に戻る。

    return_to_y を渡すとそこに戻る。None なら最上部に戻る。
    実際にスクロールが発生したかを返す。
    """
    try:
        info = page.evaluate(_SCROLL_INFO_JS)
    except Exception:
        return False

    page_height = int(info.get("height", 0))
    viewport_h = int(info.get("viewport_height", 800))
    if page_height <= viewport_h + 60:
        return False

    target = 0 if return_to_y is None else max(0, return_to_y)
    try:
        page.evaluate(
            "() => window.scrollTo({ top: document.documentElement.scrollHeight,"
            " behavior: 'smooth' })"
        )
        page.wait_for_timeout(900)
        page.wait_for_timeout(pause_ms)
        page.evaluate("(y) => window.scrollTo({ top: y, behavior: 'smooth' })", target)
        page.wait_for_timeout(900)
    except Exception:
        return False
    return True


# --- クリック対象の自動検出 -------------------------------------------------

_FIND_CLICK_TARGET_JS = r"""(args) => {
    const path = args.path;
    const method = args.method;
    const data = args.data || {};
    const pathOnly = path.split('?')[0];

    function rectOf(el) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
            return [Math.round(r.left + r.width / 2),
                    Math.round(r.top + r.height / 2 + window.scrollY)];
        }
        return null;
    }

    if (method === 'GET') {
        const anchors = Array.from(document.querySelectorAll('a[href]'));
        for (const a of anchors) {
            const href = a.getAttribute('href') || '';
            const full = a.href || '';
            if (href === pathOnly || href.endsWith(pathOnly) ||
                full.endsWith(pathOnly)) {
                const r = rectOf(a);
                if (r) return r;
            }
        }
        for (const a of anchors) {
            const href = a.getAttribute('href') || '';
            const full = a.href || '';
            if (href.indexOf(pathOnly) >= 0 ||
                full.indexOf(pathOnly) >= 0) {
                const r = rectOf(a);
                if (r) return r;
            }
        }
    }

    const forms = Array.from(document.querySelectorAll('form'));
    for (const f of forms) {
        const action = f.getAttribute('action') || '';
        const fullAction = f.action || '';
        const actionMatch =
            action === pathOnly ||
            action.indexOf(pathOnly) >= 0 ||
            fullAction.indexOf(pathOnly) >= 0 ||
            (action === '' && document.location.pathname === pathOnly);
        if (!actionMatch) continue;

        let dataOk = true;
        for (const k of Object.keys(data)) {
            const inp = f.querySelector('input[name="' + k + '"]');
            if (!inp || inp.value !== String(data[k])) {
                dataOk = false;
                break;
            }
        }
        if (!dataOk) continue;

        const btn = f.querySelector(
            'button[type="submit"], button:not([type]),' +
            ' input[type="submit"], input[type="image"]'
        );
        const r = btn ? rectOf(btn) : rectOf(f);
        if (r) return r;
    }
    return null;
}"""


def find_click_target(
    page: Page,
    path: str,
    method: str,
    data: dict[str, str],
) -> tuple[int, int] | None:
    """target への遷移を引き起こす要素の **絶対座標** (page-relative) を返す。

    返り値の y は `clientY + window.scrollY` (= 文書先頭からの距離) なので、
    呼び出し側でスクロール後に viewport 相対座標へ変換すること。

    優先順位:
      1. GET の場合: `<a href>` で path を含むもの
      2. POST または上記で見つからない: `<form action>` が path にマッチし、
         hidden input が data の各キー/値と一致する form の submit ボタン
      3. 見つからない場合は None
    """
    try:
        coords = page.evaluate(
            _FIND_CLICK_TARGET_JS,
            {"path": path, "method": method, "data": data or {}},
        )
    except Exception:
        return None
    if coords is None:
        return None
    return int(coords[0]), int(coords[1])


def clamp_to_viewport(
    coords: tuple[int, int],
    viewport_width: int,
    viewport_height: int,
    margin: int = 12,
) -> tuple[int, int]:
    """座標を viewport 内に収める。上端は HUD 字幕領域 (~63px) を避ける。"""
    x, y = coords
    x = max(margin, min(viewport_width - margin, x))
    y = max(75, min(viewport_height - margin, y))
    return x, y


# --- POST ナビゲーション ----------------------------------------------------

def navigate_post(
    page: Page,
    target_url: str,
    data: dict[str, str],
    nav_timeout_ms: int,
) -> Response | None:
    """ブラウザに hidden form を inject して POST ナビゲーションを行う。

    返り値はターゲット URL に対する Response (status / headers を取得するため)。
    取れなかった場合は None。
    """
    inputs = "\n".join(
        f'<input type="hidden" name="{_html.escape(k)}" value="{_html.escape(v)}">'
        for k, v in data.items()
    )
    auto_html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>'
        f'<form id="autopost" method="POST" action="{_html.escape(target_url)}">'
        f'{inputs}</form>'
        '<script>document.getElementById("autopost").submit();</script>'
        '</body></html>'
    )

    captured: list[Response] = []
    target_path = target_url.split("?", 1)[0]

    def on_response(resp: Response) -> None:
        if resp.url.split("?", 1)[0] == target_path:
            captured.append(resp)

    page.on("response", on_response)
    try:
        with page.expect_navigation(
            wait_until="domcontentloaded", timeout=nav_timeout_ms
        ):
            # set_content の既定待機 ("load") はフォーム送信後の navigation で
            # 中断されてタイムアウトするため "commit" で済ませる
            page.set_content(auto_html, wait_until="commit", timeout=nav_timeout_ms)
    finally:
        page.remove_listener("response", on_response)

    for r in captured:
        if r.request.method == "POST":
            return r
    return captured[-1] if captured else None


# --- ページ本文のエラー検出 -------------------------------------------------

def detect_body_errors(
    body_text: str,
    *,
    fatal_patterns: tuple[str, ...] | list[str] = (),
    warning_patterns: tuple[str, ...] | list[str] = (),
    not_found_strings: tuple[str, ...] | list[str] = (),
    head_chars: int = 300,
) -> tuple[bool, bool, str]:
    """body_text を見て (fatal_error, file_not_found, warning_pattern) を返す。

    - fatal_patterns: 本文中に含まれていれば致命的エラー (例: "Fatal error", "Uncaught")
    - not_found_strings: 本文中に含まれていれば File not found 系 (例: "File not found")
    - warning_patterns: 本文先頭 head_chars 文字に出ていれば警告 (例: "Warning:" "Notice:")
      警告は業務テキストに偶然含まれることもあるため先頭領域のみで判定する。

    すべて空のままなら何も検出しない (副作用なし)。
    """
    if not body_text:
        return False, False, ""
    fatal = any(p in body_text for p in fatal_patterns)
    not_found = any(s in body_text for s in not_found_strings)
    head = body_text[:head_chars]
    warning = next((p for p in warning_patterns if p in head), "")
    return fatal, not_found, warning
