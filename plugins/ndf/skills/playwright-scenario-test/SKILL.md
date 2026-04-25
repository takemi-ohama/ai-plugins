---
name: playwright-scenario-test
description: "Playwright + curl で Web アプリのシナリオ E2E テストを並列実行し、字幕・カーソル付き動画と Markdown レポートを生成、Google Drive へアップロードして Google Docs 化するまでの一式の Know-How とテンプレート。"
when_to_use: "E2E テスト・動画エビデンス・Google Drive 共有レポートが必要なとき (検証環境の動作確認、第三者向けエビデンス収集、定期回帰テスト、リリース前確認など)。Triggers: 'E2E テスト', 'シナリオテスト', '動画エビデンス', 'Playwright', 'リリース前確認', '回帰テスト'"
allowed-tools:
  - Read
  - Bash(uv *)
  - Bash(python *)
---

# Playwright シナリオテスト + 動画レポート Skill

Web アプリの E2E シナリオを並列実行し、**カーソル可視化 + 日本語字幕入りの動画**と **Markdown レポート**を出力、それを **Google Drive 共有 + Google Docs 化**するまでの一式の Know-How を集めたスキル。

OSS で再利用可能な汎用テンプレートとして提供する。プロジェクト固有のロール・URL・データ・バグ検出パターンは config / testcase YAML 側で吸収する。

## このスキルが提供するもの

1. **並列シナリオランナー** — 1 YAML = 1 シナリオ = 1 動画 = 1 並列ユニット
2. **動画エビデンス** — カーソル可視化、2 行字幕 (直前/次へ)、スクロールデモ、クリックリップル、PHP 警告等の自動 FAIL 判定
3. **Google Drive 互換 mp4** — H.264 High / 1280×720 16:9 / CFR 30fps / bt709 / AAC stereo / +faststart
4. **Drive アップロード自動化** — ディレクトリツリー保存 + Markdown→Google Docs 変換 + Drive リンク自動書き換え

## いつ使うか

- レビュアやステークホルダー向けに、Web アプリの主要フローを **動画と字幕付きで自動記録** したい
- 複数ロール (管理者 / 一般ユーザ / 等) の E2E シナリオを **並列で 1 分前後で実施** したい
- 結果を Google Drive に整理 → Google Docs で社内共有したい
- マスキング/再構築 した検証環境のリリース前動作確認を毎回やりたい
- PHP 警告 / 5xx / Fatal error / 想定外リダイレクトを CI で検出したい

## 設計方針

**ユーザのプロジェクトは設定ファイルしか持たない**。

Skill 自体が `pyproject.toml` を持つ独立した uv プロジェクトとして完結しており、フレームワーク本体 (Python パッケージ `scenario_test`) はそこに常駐。ユーザは自分のプロジェクトに `config.yaml` と `testcases/*.yaml` だけ置き、Skill 側のエントリポイントを `uv run --project $SKILL_DIR scenario-test --config ./config.yaml` で呼び出す。

これにより:
- ユーザ側にコードが入らない → AI による drift / 改変リスクなし
- Skill のバージョンアップが全プロジェクトに即時反映
- プロジェクトを git に入れるとき含まれるのは config と testcase YAML だけ

## クイックスタート

```bash
SKILL_DIR=.claude/skills/playwright-scenario-test

# --- Skill 側の初回セットアップ (1 回のみ) ---
cd $SKILL_DIR
uv sync                                           # 依存解決 + venv 作成
uv run playwright install chromium                # Chromium バイナリ取得

# --- 新規プロジェクト作成 (config と testcase YAML だけ) ---
cd /your/repo
mkdir -p my-e2e/testcases
cp $SKILL_DIR/templates/config.example.yaml my-e2e/config.yaml
cp $SKILL_DIR/templates/testcase-*.yaml.template my-e2e/testcases/
# my-e2e/config.yaml と my-e2e/testcases/*.yaml を実環境に合わせて編集

# --- 実行 ---
cd my-e2e
uv run --project $SKILL_DIR scenario-test --config ./config.yaml --workers 4
# レポートは ./reports/<timestamp>/ に生成される

# --- ケース絞り込み実行 ---
uv run --project $SKILL_DIR scenario-test --config ./config.yaml --filter "phase:50,51 role:user"
uv run --project $SKILL_DIR scenario-test --config ./config.yaml --list   # 一覧のみ

# --- Drive アップロード ---
uv run --project $SKILL_DIR python $SKILL_DIR/scripts/gdrive_upload_dir.py \
  --local ./reports/ --parent <DRIVE_FOLDER_ID>

# --- Markdown → Google Docs (Drive リンク自動書き換え) ---
uv run --project $SKILL_DIR python $SKILL_DIR/scripts/build_gdoc_with_drive_links.py \
  --md ./reports/<run-id>/report.md \
  --folder <DRIVE_FOLDER_ID> \
  --run-id <run-id> \
  --name "テスト報告書"
```

> プロジェクト固有のロジック (フェーズラベル、ログイン送信セレクタ、本文エラーパターン、スラッグ正規化、レポートタイトル等) はすべて `config.yaml` 側で吸収する設計のため、Skill のコードは編集不要。

## アーキテクチャ要点

### YAML テストケースの設計原則

**1 シナリオで複数の機能を網羅する** — ログイン単独 / ログアウト単独 のような最小ケースは作らない。1 ロール = 1 シナリオで「ログイン → 主要画面 → 重要機能 → ログアウト」を一連で踏む。

**理由**: 1 シナリオ = 1 動画 = 1 ストーリー。レビュアやステークホルダーは動画 1 本で全体感を把握できる。並列ワーカ間でログイン処理が独立するので、合計時間も最適。

```yaml
# testcases/admin-scenario.yaml
id: TC-10
title: 管理者 - 全機能シナリオ
phase: 10
type: playwright
role: admin
post_login:
  url_must_not_contain: ["TwoFactorAuth"]   # 2FA スキップ確認等を post_login アサーションで埋め込む
steps:
  - name: 主要画面1
    path: /admin/top.php
  - name: 詳細表示 (POST + 抽出)
    path: /admin/items.php
    method: POST
    data: {Cmd: EditView, ItemID: "{item_id}"}
    extract:
      detail_id: "GetImage\\([^,]+,\\s*(\\d+)\\)"
  - name: 画像取得
    path: /admin/items.php
    method: POST
    data: {Cmd: ImageView, DetailID: "{detail_id}"}
    expect_content_type: "image/"
```

### 並列実行

`ProcessPoolExecutor` で各 YAML を独立プロセス・独立 Playwright で実行する。動画ファイルが衝突しない。`--workers 4` 推奨 (アプリ側に過負荷を掛けないバランス)。

### GET vs POST ナビゲーション

GET は `page.goto()` で良いが、POST は Playwright の API では難しい。`page.set_content()` に hidden form を inject して auto-submit する `navigate_post()` ヘルパを使う (`scripts/scenario_test/nav_helpers.py`)。

**重要**: `page.set_content(html, wait_until="commit")` で開く。既定の `"load"` だと送信先 navigation で中断されてタイムアウトする。

## 動画 Know-How

### HUD オーバーレイ (カーソル + 字幕)

ブラウザ標準のカーソルは動画録画に焼き付かないので、JS で `<div>` を 2 つ inject する (`scripts/scenario_test/hud.py`):

1. **赤丸カーソル** (`<div id="__hud_cursor">`)
   - `position:fixed; z-index:2147483647; pointer-events:none;`
   - `mousemove` イベントで `left/top` を追従
   - `mousedown` で拡大＋シアンに変色 + 黄色リップル発火
2. **2 行字幕** (`<div id="__hud_caption">`)
   - 画面 **最上部** (top:0) に固定
   - `padding-top` を `<body>` に追加して本文と重ならないようにする
   - フォント: `"Noto Sans CJK JP", "Noto Sans JP", sans-serif`

**字幕は 2 種類のテキスト**を表示:
- `直前 │ {今やったこと → HTTP 200 OK}`
- `次へ │ {次にやること}`

### 重要: 字幕を navigation 越しに引き継ぐ

`window.__pendingCaption` だけだと navigation で消える。**`sessionStorage` にも保存** することで新ページの init script が読み戻せる。実装は `scripts/scenario_test/hud.py` を参照。

```javascript
let stored = sessionStorage.getItem('__hudCaption') || '';
cap.textContent = window.__pendingCaption || stored || '';
```

### スクロールデモ

ページが viewport より長い場合、ナビゲーション直前に「下までスクロール → クリック対象 (なければ最上部) に戻る」アニメーションを入れる。動画でページ全体像を見せる。

```python
def scroll_demo(page, return_to_y, pause_ms=500):
    page.evaluate("() => window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'smooth'})")
    page.wait_for_timeout(900 + pause_ms)
    page.evaluate("(y) => window.scrollTo({top: y, behavior: 'smooth'})", return_to_y)
    page.wait_for_timeout(900)
```

### クリック対象の自動検出 + リップル発火

各ステップ navigation 直前に、現ページから target に遷移する `<a href>` または `<form action+hidden inputs>` を JS evaluate で探し、その絶対座標 (`y = clientY + scrollY`) を取得。スクロールで viewport に入れてから `page.mouse.move()` + JS リップル発火。

実装: `scripts/scenario_test/nav_helpers.py` の `find_click_target()`。

**対象が見つからなかった場合はカーソルを非表示** (`window.__hudHideCursor()`) — 適当な位置に出すと逆に分かりにくくなるため。

### 各ステップ間の待機

`step_delay_ms: 1800` (1.8 秒) を推奨。動画でじっくり字幕を読める時間を確保。CI で速度優先なら `0`。

### PHP 警告等の自動 FAIL 判定

ページ本文の先頭 300 文字に PHP の `Fatal error` / `Uncaught` / `Parse error` / `STRICT:` / `Warning:` / `Notice:` / `Deprecated:` が出ていれば FAIL とする。HTTP 200 でも本文が壊れていることを検出できる。

```python
fatal_error = (
    "Fatal error" in body_text or "Uncaught" in body_text or "Parse error" in body_text
)
file_not_found = "File not found" in body_text
php_warning = ""
for pat in ("STRICT:", "Warning:", "Notice:", "Deprecated:"):
    if pat in body_text[:300]:
        php_warning = pat
        break
```

PHP 以外のフレームワークでも、エラー出力の特徴文字列をリストに加えれば同様に検出可能。

## Google Drive 向き動画フォーマット

Drive はアップロード動画を HLS にトランスコードしてストリーム再生する。**ソースが Drive の preferred spec に近いほど transcoding が早く完了** し「処理中」エラーが出にくい。

### Drive 推奨スペック (実証済み)

| 項目 | 値 | 理由 |
|---|---|---|
| Container | mp4 (`isom`) | 標準 |
| Video codec | **H.264 High profile / Level 4.0** | Drive のテンプレに一致 |
| Resolution | **1280×720 (HD 720p、16:9)** | Drive のプレイヤは 16:9 を仮定 |
| Frame rate | **30 fps CFR** (`-fps_mode cfr`) | VFR は再エンコード対象 |
| Pixel format | `yuv420p` | 必須 |
| Color | **bt709** (primaries/trc/colorspace) | Drive 既定 |
| Keyframe | 60 (`-g 60`)、`-sc_threshold 0` | シーク・ストリーム最適 |
| Audio | **AAC LC stereo / 48kHz / 128kbps** (無音可) | 音声トラック必須 |
| moov atom | **`+faststart`** で先頭配置 | プログレッシブ再生 |

### Playwright は webm のみ生成 → ffmpeg 変換

`imageio-ffmpeg` (静的バイナリ同梱の Python pkg) を依存に追加して、`uv run` 環境内で完結。実装は `scripts/scenario_test/video.py` を直接 import すれば 1 行で変換可能:

```python
from convert_webm_to_drive_mp4 import convert_webm_to_drive_mp4
convert_webm_to_drive_mp4(Path("input.webm"), Path("output.mp4"))
```

### ファイル名規則

- Video: `{TC-id}.mp4` (例: `TC-10.mp4`) ← scenario 番号でユニーク化
- Trace: `{TC-id}.trace.zip`
- Screenshot: `{NN}-{path-slug}.png` (NN は step 番号)

## Google Drive アップロード Know-How

### よくある失敗: 階層が二重になる

`gdrive_upload_dir.py --local reports/ --parent <ID>` は `reports/<run-id>/...` を `<parent>/<run-id>/...` で展開する。**親フォルダ ID を、ユーザが手動作成した「run-id 名のフォルダ」にすると入れ子重複** する。

正しい手順:
- ✅ `--parent` には **トップフォルダ ID** を指定する
- ✅ `--local` には **reports/ (run-id を含む親)** を指定する
- ❌ `--parent` に「run-id 名で手動作成したフォルダ」を指定しない (二重になる)

```text
e2e-tests/                    ← --parent にこのフォルダ ID
└── 20260101-120000/          ← reports/ 配下にあった単一の run-id がそのまま展開
    ├── TC-XX/
    └── report.md
```

### Markdown → Google Docs (Drive リンク化)

レポート `report.md` の相対リンク (`./TC-10/video.mp4` 等) を **Drive 上の URL に書き換えてから** `application/vnd.google-apps.document` でアップロード:

- `.webm` / `.mp4` / `.zip` → `https://drive.google.com/file/d/<id>/view`
- `.png` → `https://drive.google.com/uc?id=<id>` (画像直接表示)

スクリプト: `scripts/build_gdoc_with_drive_links.py`

事前に Drive にツリーをアップロードしてから run-id フォルダ内のファイル一覧を取得して mapping を作るので、必ず **Drive アップロード → md→Docs 変換** の順で実行する。

### Google API 認証

OAuth2 クライアントが必要。スコープは `drive.file` (アプリ作成ファイルのみ) または `drive.readonly` (一覧用)。本スキルの `scripts/*.py` は `google_auth.get_credentials()` を import するため、リポジトリで Google OAuth2 クライアントを別途用意する必要がある (詳細は `google-auth` 系スキルを参照)。

## Skill ディレクトリ構成

```
.claude/skills/playwright-scenario-test/
├── SKILL.md                        ← この Know-How ドキュメント
├── pyproject.toml                  ← Skill 自体の uv プロジェクト定義
├── uv.lock                         ← 依存ロックファイル (共有可)
├── .gitignore                      ← .venv / __pycache__ 除外
├── scenario_test/                  ← フレームワーク本体 (Python パッケージ)
│   ├── cli.py / config.py / testcase.py
│   ├── curl_executor.py / playwright_executor.py
│   ├── hud.py / nav_helpers.py / video.py
│   ├── runner.py / report.py
│   └── __init__.py / __main__.py
├── scripts/                        ← Drive 連携の単独スクリプト
│   ├── _drive_auth.py
│   ├── gdrive_upload_dir.py
│   ├── build_gdoc_with_drive_links.py
│   └── upload_md_as_gdoc.py
└── templates/                      ← ユーザがコピーして編集する種ファイル
    ├── config.example.yaml
    ├── testcase-playwright.yaml.template
    └── testcase-curl.yaml.template
```

## ユーザプロジェクトの構成 (最小)

```
my-e2e/
├── config.yaml                     ← templates/config.example.yaml をコピーして編集
├── testcases/                      ← 1 YAML = 1 シナリオ = 1 動画
│   ├── TC-10-admin.yaml
│   └── TC-20-user.yaml
└── reports/                        ← 実行時に自動生成 (.gitignore 対象推奨)
    └── 20260101-120000/...
```

**ユーザのプロジェクト側に Python コードや pyproject.toml は置かない**。フレームワークは Skill 側に常駐し、`uv run --project $SKILL_DIR scenario-test --config ./config.yaml` で呼び出す。

## フレームワークモジュール (`scenario_test/`)

| モジュール | 役割 |
|---|---|
| `cli.py` | argparse + main エントリポイント |
| `config.py` | config.yaml ローダ + dataclass (`BodyCheckConfig` / `SlugConfig` / `ReportConfig` 等) |
| `testcase.py` | テストケース YAML ローダ + フィルタ |
| `curl_executor.py` | curl タイプの実行器 |
| `playwright_executor.py` | Playwright タイプの実行オーケストレータ |
| `hud.py` | HUD オーバーレイ (カーソル + 字幕) の JS と制御 API |
| `nav_helpers.py` | クリック対象検出・スクロールデモ・POST ナビ・本文エラー検出 |
| `video.py` | webm → Drive 互換 mp4 変換 |
| `runner.py` | `ProcessPoolExecutor` 並列オーケストレータ |
| `report.py` | Markdown レポート生成 |

すべてプロジェクト固有値を持たない汎用実装。プロジェクト個別の値は `config.yaml` 経由で注入される。

## 関連スキル (前提)

- `google-auth` — Drive API 用 OAuth2 認証 (本スキルの Drive 系スクリプトが依存)
- `google-drive` — Drive ファイル取得・アップロードの基礎

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| 動画に字幕が映らない | `add_init_script` 注入前に screenshot を撮っている | `wait_until="domcontentloaded"` で待機、screenshot は step_delay 後 |
| 字幕がページ遷移で消える | `window.__pendingCaption` のみで保存 | `sessionStorage` にも保存し init script で復元 |
| カーソル位置がページを跨いで残らない | mousemove ハンドラで保存していない | mousemove で sessionStorage に座標保存、init で復元 |
| Drive で「再生処理中」が長引く | viewport 1280×800 等の非標準アスペクト | 1280×720 (16:9) に変更 |
| Drive で「処理に時間がかかっています」 | bt709 未指定 / VFR / 音声トラック無 | mp4 変換時に bt709 / CFR / AAC stereo を強制 |
| Drive 階層が二重になる | `--local` と `--parent` の組み合わせ誤り | `--local reports/ --parent <topfolder>` パターン厳守 |
| 動画ファイル名が衝突する | `video.webm` 固定名 | `{TC-id}.mp4` でユニーク化 |
| クリック位置が画面上部だけ | 固定座標で flash | `<a href>` / `<form>` を JS で探して実座標を取得 |
| ログイン後の URL 検査だけだとログアウトテストが落ちる | `still_on_login` チェック | `expect_url_contains` 指定時は still_on_login を無視するロジック |
| HTTP 200 なのに本文が壊れている | PHP STRICT / Warning がページ先頭に漏れている | body_text 先頭 300 文字を `STRICT:` / `Warning:` 等で検査して FAIL |
