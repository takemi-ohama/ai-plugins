"""共通設定 (config.yaml) のロードとデータクラス。

テストケース YAML ではなく、対象環境・ロール別ログイン・Playwright/Runner 設定、
およびページ検査・スラッグ正規化・レポート生成のプロジェクト固有パラメータを保持する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# --- 接続/認証 -------------------------------------------------------

@dataclass
class BasicAuth:
    user: str
    password: str


@dataclass
class Login:
    path: str
    requires_basic_auth: bool
    fields: dict[str, str]
    fail_if_url_contains: str
    # ログイン送信ボタンを特定するためのプロジェクト固有セレクタ。
    # nav_helpers.submit_login() が「これ → 汎用フォールバック → Password で Enter」
    # の順で試す。空のままでも汎用フォールバックで通常はログインできる。
    submit_selectors: list[str] = field(default_factory=list)


@dataclass
class Role:
    id: str
    label: str
    login: Login


# --- ページ検査・スラッグ正規化 -------------------------------------

@dataclass
class BodyCheckConfig:
    """ページ本文を見て「壊れている」と判定するためのパターン群。

    すべて空のままなら検査せず、HTTP ステータスと URL アサーションだけが効く。
    PHP プロジェクトなら Fatal/Warning パターンを足す、Rails なら別のパターンを
    入れる、といった具合に config.yaml で差し込む。
    """
    fatal_patterns: list[str] = field(default_factory=list)
    warning_patterns: list[str] = field(default_factory=list)
    not_found_strings: list[str] = field(default_factory=list)


@dataclass
class SlugConfig:
    """スクショファイル名生成用のスラッグ正規化ルール。

    - strip_extensions: path から削除する拡張子 (例: [".php"])
    - query_capture_re: クエリ文字列から拾うラベル (例: "Cmd=(\\w+)" → サフィックスに付与)
    """
    strip_extensions: list[str] = field(default_factory=list)
    query_capture_re: str | None = None


# --- レポート設定 ---------------------------------------------------

@dataclass
class ReportConfig:
    title: str = "シナリオ E2E テスト 実施報告書"
    test_plan_link: str = "./test-plan.md"
    phase_labels: dict[int, str] = field(default_factory=dict)


# --- Playwright / Runner -------------------------------------------

@dataclass
class PlaywrightConfig:
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    slow_mo_ms: int = 0
    video_width: int = 1280
    video_height: int = 720
    navigation_timeout_ms: int = 30000
    # 各ステップ遷移後の表示維持時間 (動画でじっくり見せるため)
    step_delay_ms: int = 1800
    # 動画にカーソル＋字幕オーバーレイを焼き込む (true 推奨)
    enable_overlay: bool = True
    # Playwright Trace (trace.zip) を出力する。クリック箇所のハイライト・
    # DOM スナップショット・コンソール・ネットワークなどを `playwright show-trace`
    # で対話的に確認できる。生成物が大きく (数MB〜) なるので必要時のみ。
    enable_trace: bool = True
    # ページ内容が viewport より長い場合、ナビゲーション前に「下までスクロール →
    # クリック対象の位置 (なければ最上部) に戻る」アニメーションを差し込む。
    enable_scroll_demo: bool = True
    # 録画後の動画フォーマット: "webm" (Playwright 既定) | "mp4" (H.264 変換)
    # mp4 は Google Drive プレビュアで再生互換性が高い。
    video_format: str = "mp4"

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "PlaywrightConfig":
        viewport = raw.get("viewport") or {}
        video_size = raw.get("video_size") or {}
        return cls(
            headless=bool(raw.get("headless", True)),
            viewport_width=int(viewport.get("width", 1280)),
            viewport_height=int(viewport.get("height", 800)),
            slow_mo_ms=int(raw.get("slow_mo_ms", 0)),
            video_width=int(video_size.get("width", 1280)),
            video_height=int(video_size.get("height", 800)),
            navigation_timeout_ms=int(raw.get("navigation_timeout_ms", 30000)),
            step_delay_ms=int(raw.get("step_delay_ms", 1500)),
            enable_overlay=bool(raw.get("enable_overlay", True)),
            enable_trace=bool(raw.get("enable_trace", True)),
            enable_scroll_demo=bool(raw.get("enable_scroll_demo", True)),
            video_format=str(raw.get("video_format", "mp4")).lower(),
        )


@dataclass
class RunnerConfig:
    workers: int = 4
    testcases_dir: str = "./testcases"

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "RunnerConfig":
        return cls(
            workers=int(raw.get("workers", 4)),
            testcases_dir=str(raw.get("testcases_dir", "./testcases")),
        )


# --- ルート ---------------------------------------------------------

@dataclass
class Config:
    base_url: str
    basic_auth: BasicAuth
    verify_tls: bool
    roles: dict[str, Role]
    playwright: PlaywrightConfig
    runner: RunnerConfig
    body_check: BodyCheckConfig
    slug: SlugConfig
    report: ReportConfig
    config_path: Path  # 設定ファイルの絶対パス（testcases_dir の解決基点）

    @property
    def testcases_dir(self) -> Path:
        d = Path(self.runner.testcases_dir)
        if not d.is_absolute():
            d = self.config_path.parent / d
        return d.resolve()

    def role(self, role_id: str) -> Role:
        if role_id not in self.roles:
            raise KeyError(f"未定義のロール: {role_id}. roles 設定を確認してください。")
        return self.roles[role_id]

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            raise FileNotFoundError(
                f"設定ファイルが見つかりません: {path}\n"
                "config.example.yaml をコピーして作成してください。"
            )
        with path.open("r", encoding="utf-8") as fp:
            raw: dict[str, Any] = yaml.safe_load(fp)
        return cls._from_dict(raw, config_path=path.resolve())

    @classmethod
    def _from_dict(cls, raw: dict[str, Any], *, config_path: Path) -> "Config":
        target = raw["target"]
        basic_auth = BasicAuth(
            user=target["basic_auth"]["user"],
            password=target["basic_auth"]["password"],
        )
        roles = {rid: _role_from_raw(rid, r) for rid, r in (raw.get("roles") or {}).items()}

        return cls(
            base_url=target["base_url"].rstrip("/"),
            basic_auth=basic_auth,
            verify_tls=bool(raw.get("verify_tls", False)),
            roles=roles,
            playwright=PlaywrightConfig.from_raw(raw.get("playwright") or {}),
            runner=RunnerConfig.from_raw(raw.get("runner") or {}),
            body_check=_body_check_from_raw(raw.get("body_check") or {}),
            slug=_slug_from_raw(raw.get("slug") or {}),
            report=_report_from_raw(raw.get("report") or {}),
            config_path=config_path,
        )


def _role_from_raw(rid: str, raw: dict[str, Any]) -> Role:
    login = raw["login"]
    return Role(
        id=rid,
        label=str(raw.get("label", rid)),
        login=Login(
            path=login["path"],
            requires_basic_auth=bool(login.get("requires_basic_auth", False)),
            fields=dict(login["fields"]),
            fail_if_url_contains=login["fail_if_url_contains"],
            submit_selectors=list(login.get("submit_selectors") or []),
        ),
    )


def _body_check_from_raw(raw: dict[str, Any]) -> BodyCheckConfig:
    return BodyCheckConfig(
        fatal_patterns=list(raw.get("fatal_patterns") or []),
        warning_patterns=list(raw.get("warning_patterns") or []),
        not_found_strings=list(raw.get("not_found_strings") or []),
    )


def _slug_from_raw(raw: dict[str, Any]) -> SlugConfig:
    return SlugConfig(
        strip_extensions=list(raw.get("strip_extensions") or []),
        query_capture_re=(str(raw["query_capture_re"]) if raw.get("query_capture_re") else None),
    )


def _report_from_raw(raw: dict[str, Any]) -> ReportConfig:
    labels_raw = raw.get("phase_labels") or {}
    return ReportConfig(
        title=str(raw.get("title", "シナリオ E2E テスト 実施報告書")),
        test_plan_link=str(raw.get("test_plan_link", "./test-plan.md")),
        phase_labels={int(k): str(v) for k, v in labels_raw.items()},
    )
