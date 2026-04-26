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
    # ログイン送信ボタンを特定するためのプロジェクト固有セレクタ (CSS / role / text)。
    # `playwright_executor._submit_login_form` が「これ → role/type=submit
    # フォールバック → Password で Enter」の順で試す。空のままでも汎用
    # フォールバックで通常はログインできる。
    submit_selectors: list[str] = field(default_factory=list)


@dataclass
class Role:
    id: str
    label: str
    login: Login


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
    # 録画後の動画フォーマット: "webm" (Playwright 既定) | "mp4" (H.264 変換)
    # mp4 は Google Drive プレビュアで再生互換性が高い。
    video_format: str = "mp4"

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "PlaywrightConfig":
        # 既定値は 1280x720 (HD 720p, 16:9) で統一。dataclass の default、
        # config.example.yaml、本メソッドの default すべて同じ値にする。
        viewport = raw.get("viewport") or {}
        video_size = raw.get("video_size") or {}
        return cls(
            headless=bool(raw.get("headless", True)),
            viewport_width=int(viewport.get("width", 1280)),
            viewport_height=int(viewport.get("height", 720)),
            slow_mo_ms=int(raw.get("slow_mo_ms", 0)),
            video_width=int(video_size.get("width", 1280)),
            video_height=int(video_size.get("height", 720)),
            navigation_timeout_ms=int(raw.get("navigation_timeout_ms", 30000)),
            step_delay_ms=int(raw.get("step_delay_ms", 1500)),
            enable_overlay=bool(raw.get("enable_overlay", True)),
            enable_trace=bool(raw.get("enable_trace", True)),
            video_format=str(raw.get("video_format", "mp4")).lower(),
        )

    @classmethod
    def defaults(cls) -> "PlaywrightConfig":
        """設定が完全に省略された場合の defaults。viewport=video_size=1280x720 で揃える。"""
        return cls()


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


# --- a11y / CWV (v0.3.0) ---------------------------------------------

@dataclass
class A11yConfig:
    """axe-core 自動スキャンの設定 (page_role に応じて runner が自動実行)。"""
    enabled: bool = True
    auto_roles: list[str] = field(default_factory=lambda: [
        "lp", "list", "form", "dashboard", "cart", "checkout", "settings", "auth",
    ])
    tags: list[str] = field(default_factory=lambda: [
        "wcag2a", "wcag2aa", "wcag21aa", "wcag22aa",
    ])
    # 検出した violations を testcase の FAIL 要因として扱うか (false なら情報出力のみ)
    fail_on_violations: bool = True


@dataclass
class CwvConfig:
    """Core Web Vitals 自動計測の設定 (page_role に応じて runner が自動実行)。"""
    enabled: bool = True
    auto_roles: list[str] = field(default_factory=lambda: [
        "lp", "list", "dashboard", "search",
    ])
    observe_ms: int = 5000
    # poor 判定が 1 件でもあれば testcase を FAIL とするか
    fail_on_poor: bool = True


# --- ルート ---------------------------------------------------------

@dataclass
class Config:
    base_url: str
    basic_auth: BasicAuth
    verify_tls: bool
    roles: dict[str, Role]
    playwright: PlaywrightConfig
    runner: RunnerConfig
    report: ReportConfig
    config_path: Path  # 設定ファイルの絶対パス（testcases_dir の解決基点）
    # docs/checklists/checklist-common.md C8/C9 の境界曖昧さに対応する「除外」設定。
    # console.error / pageerror の本文がいずれかの正規表現にマッチした場合は
    # 集計から除外し FAIL を抑制する。3rd party の既知 warning などを許容するための
    # 抜け穴。空 (デフォルト) なら従来どおり 1 件で FAIL。
    tolerated_console_errors: list[str] = field(default_factory=list)
    tolerated_page_errors: list[str] = field(default_factory=list)
    # a11y / CWV 自動実行 (page_role に応じて runner が判定)
    a11y: A11yConfig = field(default_factory=A11yConfig)
    cwv: CwvConfig = field(default_factory=CwvConfig)

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
        # basic_auth は省略可能 (サイトに Basic 認証が掛かっていない場合)。
        # 省略時は空 BasicAuth を使い、role 側で `requires_basic_auth: true` を
        # 指定したテストケースだけが basic_auth ヘッダを要求する設計。
        ba_raw = target.get("basic_auth") or {}
        basic_auth = BasicAuth(
            user=str(ba_raw.get("user", "")),
            password=str(ba_raw.get("password", "")),
        )
        roles = {rid: _role_from_raw(rid, r) for rid, r in (raw.get("roles") or {}).items()}

        cfg = cls(
            base_url=target["base_url"].rstrip("/"),
            basic_auth=basic_auth,
            verify_tls=bool(raw.get("verify_tls", False)),
            roles=roles,
            playwright=PlaywrightConfig.from_raw(raw.get("playwright") or {}),
            runner=RunnerConfig.from_raw(raw.get("runner") or {}),
            report=_report_from_raw(raw.get("report") or {}),
            config_path=config_path,
            tolerated_console_errors=list(raw.get("tolerated_console_errors") or []),
            tolerated_page_errors=list(raw.get("tolerated_page_errors") or []),
            a11y=_a11y_from_raw(raw.get("a11y") or {}),
            cwv=_cwv_from_raw(raw.get("cwv") or {}),
        )

        # fail-fast: requires_basic_auth=True なロールが宣言されているのに
        # basic_auth.user が空ならば実行時に HTTP 401 で必ず落ちる。先に検出して
        # 設定不備として ValueError を投げる (Maj-4)。
        for role in cfg.roles.values():
            if role.login.requires_basic_auth and not basic_auth.user:
                raise ValueError(
                    f"role '{role.id}' は requires_basic_auth=True だが、"
                    f"target.basic_auth.user が空 (config.yaml を確認してください)"
                )

        return cfg


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


def _report_from_raw(raw: dict[str, Any]) -> ReportConfig:
    labels_raw = raw.get("phase_labels") or {}
    return ReportConfig(
        title=str(raw.get("title", "シナリオ E2E テスト 実施報告書")),
        test_plan_link=str(raw.get("test_plan_link", "./test-plan.md")),
        phase_labels={int(k): str(v) for k, v in labels_raw.items()},
    )


def _a11y_from_raw(raw: dict[str, Any]) -> A11yConfig:
    base = A11yConfig()
    return A11yConfig(
        enabled=bool(raw.get("enabled", base.enabled)),
        auto_roles=list(raw.get("auto_roles") or base.auto_roles),
        tags=list(raw.get("tags") or base.tags),
        fail_on_violations=bool(raw.get("fail_on_violations", base.fail_on_violations)),
    )


def _cwv_from_raw(raw: dict[str, Any]) -> CwvConfig:
    base = CwvConfig()
    return CwvConfig(
        enabled=bool(raw.get("enabled", base.enabled)),
        auto_roles=list(raw.get("auto_roles") or base.auto_roles),
        observe_ms=int(raw.get("observe_ms", base.observe_ms)),
        fail_on_poor=bool(raw.get("fail_on_poor", base.fail_on_poor)),
    )
