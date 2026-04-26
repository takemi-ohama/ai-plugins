---
name: playwright-scenario-test
description: "Playwright + curl による Web シナリオ E2E テストの理論ベース実施フレームワーク。HTSM / ISTQB / FEW HICCUPPS に基づき page role 別の checklist + 必須技法マッピングを内蔵し、字幕・カーソル付き動画レポート + a11y / Core Web Vitals 計測 + Playwright trace を自動収集する。"
when_to_use: "E2E テスト計画立案 / 不具合エビデンス収集 / 動画レポート / Google Drive 共有が必要なとき。LP / 一覧 / 詳細 / 編集 / 申込フォーム / 検索 / ダッシュボード / 認証 / カート / チェックアウト / モーダル / ウィザード / 設定 / エラーページ など page role 別の理論ベースチェックを行う。Triggers: 'E2E テスト', 'シナリオテスト', '動画エビデンス', 'Playwright', 'リリース前確認', '回帰テスト', 'a11y テスト', 'Core Web Vitals', 'LP テスト', '一覧ページ', '詳細ページ', '編集フォーム', '申込フォーム', '検索ページ', 'ダッシュボード', 'login テスト', 'カート / 決済', 'モーダル', 'ウィザード', 'page role'"
allowed-tools:
  - Read
  - Bash(uv *)
  - Bash(python *)
  - Bash(playwright *)
---

# Playwright シナリオテスト Skill

Web アプリの E2E シナリオを **理論ベース** で計画 → 並列実行 → 動画 + Markdown レポート生成 → Google Drive 共有 する一式の Skill。

「経験で書く」を排除し、**page role 別 checklist + テスト技法マトリクス** に従って機械的に計画を立てる。

## 提供物

```
playwright-scenario-test/
├── SKILL.md                    ← このファイル (実行手順とナビゲーション)
├── pyproject.toml              ← uv プロジェクト定義
├── docs/                       ← テスト方法論 (HTSM / ISTQB / FEW HICCUPPS)
│   ├── README.md               — ドキュメント目次
│   ├── 01-methodology.md       — 総論
│   ├── 02-page-roles.md        — page role 分類 (lp/list/item/edit/form/...)
│   ├── 03-test-techniques.md   — テスト技法ライブラリ (EP/BVA/Decision Table/...)
│   ├── 04-playwright-mapping.md — Playwright API → role / 観点 マッピング
│   ├── 05-bug-report.md        — bug report 仕様 (ISO 29119-3 + FEW HICCUPPS)
│   └── checklists/             — 役割別チェックリスト (12 ファイル)
├── scenario_test/              ← 並列ランナー (Python パッケージ)
├── scripts/                    ← 補助スクリプト (codegen / a11y / CWV / drive)
│   ├── classify_page_role.py   — URL から page role を自動判定
│   ├── generate_test_plan.py   — page_role + URL → testcase YAML 雛形
│   ├── record_scenario.py      — Playwright codegen ラッパー
│   ├── run_a11y_scan.py        — axe-core で a11y 違反検出
│   ├── check_cwv.py            — Core Web Vitals (LCP/CLS/TTFB) 計測
│   ├── trace_link.py           — trace.zip → playwright.dev URL
│   └── (drive 連携: gdrive_upload_dir / build_gdoc_with_drive_links / ...)
└── templates/                  ← config / testcase YAML テンプレート (役割別 4 件 + 汎用 2 件)
```

## 標準ワークフロー (理論ベース計画)

```
[A] 対象 URL を渡される
       │
[B] page role を判定                       scripts/classify_page_role.py --url <URL>
       │     a11y tree + URL pattern + role 集計から自動推定
       ▼
[C] 該当 checklist を開く                   docs/checklists/checklist-{role}.md
       │     全項目を「適用」or「不適用 (理由付き)」で判定
       ▼
[D] 必須技法を確定                          docs/03-test-techniques.md § 11
       │     例: form なら Decision Table 必須 + Pairwise
       ▼
[E] testcase YAML 生成                      scripts/generate_test_plan.py
       │     --role X --url Y --factors "..." で雛形 + Pairwise を自動展開
       ▼
[F] 必要なら codegen で操作録画              scripts/record_scenario.py <URL>
       │     "経験で書く" を "録画 → コード生成" に置換
       ▼
[G] 実行                                   uv run scenario-test --config ./config.yaml
       │     trace.zip / video / screenshot / HAR / console を自動収集
       ▼
[H] 不具合発見 → bug report                docs/05-bug-report.md
             FEW HICCUPPS の oracle 軸を必ず付与
             trace は scripts/trace_link.py で playwright.dev URL 化
```

各 step に対応するスクリプトが用意されており、AI が経験で実装する余地を構造的に排除している。

## クイックスタート (初回)

```bash
SKILL_DIR=.claude/skills/playwright-scenario-test  # or 絶対パス
cd $SKILL_DIR

# 依存解決 + Chromium インストール (1 回のみ)
uv sync
uv run playwright install chromium

# 任意: a11y スキャンを使うなら
uv sync --extra a11y

# 任意: Drive 連携を使うなら
uv sync --extra drive
```

## クイックスタート (テスト計画作成 → 実行)

```bash
SKILL=/work/ai-plugins/plugins/ndf/skills/playwright-scenario-test

# 1. 対象 URL の page role を判定
uv run --project $SKILL python $SKILL/scripts/classify_page_role.py \
  --url https://staging.example.com/items
# → primary_role: list (score: 2.5)

# 2. checklist を開いて全項目チェック
$EDITOR $SKILL/docs/checklists/checklist-list.md

# 3. testcase YAML 雛形を生成
mkdir -p my-e2e/testcases
uv run --project $SKILL python $SKILL/scripts/generate_test_plan.py \
  --role list --url https://staging.example.com/items \
  --output my-e2e/testcases/TC-LST-items.yaml

# 4. config.yaml を作成
cp $SKILL/templates/config.example.yaml my-e2e/config.yaml
$EDITOR my-e2e/config.yaml

# 5. 実行
cd my-e2e
uv run --project $SKILL scenario-test --config ./config.yaml --workers 4

# 6. a11y / CWV を補足計測
uv run --project $SKILL python $SKILL/scripts/run_a11y_scan.py \
  --url https://staging.example.com/items --output a11y.json
uv run --project $SKILL python $SKILL/scripts/check_cwv.py \
  --url https://staging.example.com/items --output cwv.json
```

## ケース絞り込み実行

```bash
# 特定の id / phase / role / type に絞る
uv run --project $SKILL scenario-test --config ./config.yaml --filter "phase:50,51 role:user"
uv run --project $SKILL scenario-test --config ./config.yaml --filter "id:TC-50-01"
# page_role で絞る (docs/02-page-roles.md の役割名: lp / list / item / edit / form / search / dashboard / auth / cart / checkout / modal / wizard / error / settings)
uv run --project $SKILL scenario-test --config ./config.yaml --filter "page_role:edit,form"
uv run --project $SKILL scenario-test --config ./config.yaml --filter "page_role:cart,checkout phase:50"
uv run --project $SKILL scenario-test --config ./config.yaml --list   # 一覧のみ
```

## Drive アップロード + Google Docs 化

```bash
# 1. レポートツリーを Drive にアップ (run-id ごとにフォルダ展開)
uv run --project $SKILL python $SKILL/scripts/gdrive_upload_dir.py \
  --local ./reports/ --parent <DRIVE_FOLDER_ID>

# 2. Markdown → Google Docs (Drive リンク自動書き換え)
uv run --project $SKILL python $SKILL/scripts/build_gdoc_with_drive_links.py \
  --md ./reports/<run-id>/report.md --folder <DRIVE_FOLDER_ID> \
  --run-id <run-id> --name "テスト報告書"

# 3. trace.zip を bug report 用 URL 化
uv run --project $SKILL python $SKILL/scripts/trace_link.py \
  ./reports/<run-id>/TC-XX/<id>.trace.zip
# → https://trace.playwright.dev/?trace=https://drive.google.com/...
```

## docs/ への入り口

| やりたいこと | 参照ドキュメント |
|---|---|
| テスト方法論の全体像 | [docs/01-methodology.md](docs/01-methodology.md) |
| URL の役割を判定したい | [docs/02-page-roles.md](docs/02-page-roles.md) |
| 役割ごとに何をテストするか | [docs/checklists/checklist-{role}.md](docs/checklists/) |
| EP / BVA / Decision Table とは | [docs/03-test-techniques.md](docs/03-test-techniques.md) |
| Playwright API の使い分け | [docs/04-playwright-mapping.md](docs/04-playwright-mapping.md) |
| bug 起票テンプレート | [docs/05-bug-report.md](docs/05-bug-report.md) |
| 全 role 共通の a11y / perf / sec | [docs/checklists/checklist-common.md](docs/checklists/checklist-common.md) |

## 設計方針

### ユーザのプロジェクトは設定ファイルしか持たない

Skill 自体が `pyproject.toml` を持つ独立した uv プロジェクトとして完結。
ユーザのリポジトリには `config.yaml` + `testcases/*.yaml` だけ置く。
これにより:
- ユーザ側に Python コードが入らない → AI による drift / 改変リスクなし
- Skill のバージョンアップが全プロジェクトに即時反映
- プロジェクトを git に入れるとき含まれるのは config と testcase YAML だけ

### 経験則の追放

| 種類 | 配置 |
|---|---|
| 業界標準 (ISO / WCAG / OWASP / ISTQB) | `docs/` |
| ヒューリスティクス (HTSM / FEW HICCUPPS / Hendrickson) | `docs/` |
| 個別プロジェクト慣習 (PHP / Rails 等) | `config.yaml` の `body_check.*_patterns` |
| 動画/HUD の細かい数値 (字幕高さ・カーソル色) | `scenario_test/hud.py` のコード内定数 |

「経験」を docs に書くのではなく、**理論を docs に書き、慣習は config に逃がす** のが規律。

## scenario_test ランナーの基本動作

各テストケースを `ProcessPoolExecutor` の独立プロセスで実行。それぞれが独自の Playwright インスタンスと動画ファイルを生成する (`--workers 4` 推奨)。

各ステップ間に `step_delay_ms: 1800` (1.8 秒) の待機を入れ、動画でじっくり字幕を読める時間を確保する。CI で速度優先なら `0` に。

詳細な動画 Know-How (HUD オーバーレイ / mp4 変換 / Drive 推奨スペック) は [docs/04-playwright-mapping.md](docs/04-playwright-mapping.md) と既存の `scenario_test/video.py` のコメントを参照。

## YAML テストケースの設計原則

**1 シナリオで複数の機能を網羅する** — ログイン単独 / ログアウト単独 のような最小ケースは作らない。1 ロール = 1 シナリオで「ログイン → 主要画面 → 重要機能 → ログアウト」を一連で踏む。

**理由**: 1 シナリオ = 1 動画 = 1 ストーリー。レビュアやステークホルダーは動画 1 本で全体感を把握できる。並列ワーカ間でログイン処理が独立するので、合計時間も最適。

```yaml
# testcases/admin-scenario.yaml の例
id: TC-10
title: 管理者 - 全機能シナリオ
phase: 10
type: playwright
role: admin
page_role: dashboard               # ← v0.2.0 で追加
post_login:
  url_must_not_contain: ["TwoFactorAuth"]
steps:
  - name: ダッシュボード表示
    path: /admin/dashboard
  ...
```

`page_role` フィールドはランナー側で必須化されないが、計画書に**必ず**記載する (どの checklist を適用したか追跡可能にするため)。

## 関連スキル (前提)

- `google-auth` — Drive API 用 OAuth2 認証 (本スキルの Drive 系スクリプトが依存)
- `google-drive` — Drive ファイル取得・アップロードの基礎

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| 動画に字幕が映らない | `add_init_script` 注入前に screenshot を撮っている | `wait_until="domcontentloaded"` で待機、screenshot は step_delay 後 |
| 字幕がページ遷移で消える | `window.__pendingCaption` のみで保存 | `sessionStorage` にも保存し init script で復元 (実装済) |
| Drive で「再生処理中」が長引く | viewport 1280×800 等の非標準アスペクト | 1280×720 (16:9) に変更 (config.example.yaml 既定) |
| Drive 階層が二重になる | `--local` と `--parent` の組み合わせ誤り | `--local reports/ --parent <topfolder>` パターン厳守 |
| 動画ファイル名が衝突する | `video.webm` 固定名 | `{TC-id}.mp4` でユニーク化 (実装済) |
| クリック位置が画面上部だけ | 固定座標で flash | `<a href>` / `<form>` を JS で探して実座標を取得 |
| HTTP 200 なのに本文が壊れている | エラー出力がページ先頭に漏れている | `body_check.warning_patterns` で先頭 300 文字を検査 |
| `playwright codegen` が起動しない | Chromium 未インストール | `uv run playwright install chromium` |

## 参考文献の最上位

- James Bach, "Heuristic Test Strategy Model" v6.3 (HTSM)
- ISTQB CTFL Syllabus 4.2 (Black-box Test Techniques)
- ISO/IEC/IEEE 29119-3:2021 (Test documentation)
- W3C "WCAG 2.2"
- OWASP Top 10:2025 + ASVS + WSTG
- Playwright Python Docs (v1.50+)

詳細・他文献は各 docs ファイルの「参考文献」節を参照。
