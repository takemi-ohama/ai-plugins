# NDF Plugin - 開発者向けガイドライン

## 概要

**NDFプラグインの開発・メンテナンス**を行うAIエージェント向けガイドライン。

## プラグイン情報

- **名前**: ndf
- **現在バージョン**: 4.1.0
- **種類**: 統合プラグイン（Skills + Agents + Hooks / v4.0.0 で Codex MCP 廃止）
- **リポジトリ**: https://github.com/takemi-ohama/ai-plugins

> **Note (v3.0.0)**: Serena MCPは`mcp-serena`プラグインに分離。memory系スキルは廃止。CLAUDE.ndf.md注入は廃止。

## 開発ルール

- ドキュメント・コミットメッセージ・PR説明は**日本語**
- **mainブランチへの直接コミット禁止**（featureブランチ+PR）
- **セマンティックバージョニング**: MAJOR（破壊的変更）、MINOR（新機能）、PATCH（バグ修正）

## ディレクトリ構造

```
plugins/ndf/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ
├── .mcp.json                    # MCPサーバー定義（Codex CLI）
├── hooks/
│   └── hooks.json               # プロジェクトフック定義
├── scripts/
│   └── slack-notify.js          # Slack通知スクリプト
├── agents/                      # サブエージェント（8個、モデル階層化）
│   ├── director.md              # opus: 計画・統括
│   ├── corder.md                # sonnet: Codex第二意見レビュー
│   ├── data-analyst.md          # sonnet: BigQuery/SQL
│   ├── researcher.md            # sonnet: AWS Docs/Chrome DevTools
│   ├── qa.md                    # sonnet: セキュリティ/品質
│   ├── debugger.md              # sonnet: 根本原因分析
│   ├── devops-engineer.md       # sonnet: Docker/CI/K8s
│   └── code-reviewer.md         # sonnet: diff/PRレビュー
├── skills/                      # スキル（36個）
│   # PRワークフロー系
│   ├── pr/                      # commit+push+PR作成/更新
│   ├── pr-tests/                # Test Plan自動実行
│   ├── fix/                     # PRコメント修正対応
│   ├── review/                  # PR単位レビュー（Approve/RC判定）
│   ├── review-branch/           # ローカル差分レビュー（PR前）
│   ├── review-pr-comments/      # PRコメント分類（READ-ONLY）
│   ├── resolve-pr-comments/     # 対応済みコメント返信+Resolve
│   ├── cherry-pick-pr/          # 環境ブランチへのcherry-pick PR
│   ├── deploy/                  # 環境ブランチへのデプロイPR
│   ├── sync-main/               # main取り込み
│   ├── merged/                  # マージ後クリーンアップ
│   ├── clean/                   # マージ済みブランチ一括削除
│   # 原則・ガイドライン系
│   ├── ndf-policies/            # ポリシー常時注入
│   ├── branch-fix-strategy/     # ブランチ修正適用戦略
│   ├── implementation-plan/     # 実装プラン管理(issues/)
│   ├── investigation-rules/     # 調査時のエビデンス主義
│   ├── problem-solving/         # 根本原因分析・多層防御
│   ├── logging-guidelines/      # ログ運用ガイドライン(言語非依存)
│   # データ分析・品質
│   ├── data-analyst-sql-optimization/
│   ├── data-analyst-export/
│   ├── qa-security-scan/
│   # ドキュメント・環境
│   ├── markdown-writing/
│   ├── python-execution/
│   ├── docker-container-access/
│   ├── deepwiki-transfer/
│   ├── knowledge-reorg/
│   ├── git-gh-operations/
│   ├── google-auth/
│   ├── browser-test/            # ブラウザ動作確認(Playwright/Chrome DevTools)
│   ├── codex/                   # Codex CLI直接実行（MCP版との使い分け）
│   ├── playwright-scenario-test/ # Playwright+curl Web シナリオE2E並列ランナー
│   ├── google-drive/            # Google Drive エクスポート/DL/UP（google-auth依存）
│   ├── google-chat/             # Google Chat メッセージ取得（google-auth依存）
│   # Anthropic公式連携
│   ├── mcp-builder/             # Anthropic公式（Apache-2.0）
│   └── official-skills-autoloader/  # 公式Skill自動ロード
├── CLAUDE.md                    # このファイル（開発者向け）
└── README.md                    # プラグイン説明書
```

## 一般的な開発タスク

### 新しいスキルの追加

1. `skills/{skill-name}/SKILL.md` を作成（YAMLフロントマター必須）
2. `plugin.json` の `skills` 配列に `"./skills/{skill-name}"` を追加
3. `plugin.json` のバージョンをMINOR上げ
4. テスト・コミット

### 新しいサブエージェントの追加

1. `agents/{agent-name}.md` を作成（YAMLフロントマター必須）
2. `plugin.json` の `agents` 配列に追加
3. バージョンMINOR上げ → テスト・コミット

### MCPサーバーの追加・更新

1. `.mcp.json` の `mcpServers` に追加
2. README.mdに説明追加
3. バージョン更新 → テスト・コミット

## 検証チェックリスト

- [ ] plugin.jsonが有効なJSON
- [ ] バージョン番号が適切にインクリメント
- [ ] すべてのスキル/エージェントファイルが存在
- [ ] YAMLフロントマターが正しい
- [ ] .mcp.jsonが有効なJSON
- [ ] README.md が最新

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| エージェントが認識されない | plugin.jsonのagents配列、ファイルパス、YAMLフロントマターを確認 |
| スキルが表示されない | plugin.jsonのskills配列、SKILL.mdのフロントマターを確認、`/plugin reload ndf` |
| MCPサーバーが起動しない | .mcp.jsonの構文、コマンドパス、環境変数を確認 |
| フックが動作しない | hooks.jsonの構文、スクリプト実行権限を確認 |

## 開発履歴

### v4.2.0 (BREAKING: playwright-scenario-test v0.3.0 OSS 品質化)
- **`playwright-scenario-test` v0.3.0** (locator-first / web-first 全面刷新):
  - **testcase YAML スキーマを刷新**: 旧 `path/method/data/extract` 構造を廃止。明示的 `kind` (`goto/click/fill/select/check/press/hover/extract/wait_for/wait_ms/expect_visible/expect_hidden/expect_text/expect_no_text/expect_url/expect_count/expect_aria_snapshot`) に統一
  - **Locator 表現**: `{role: button, name: 保存}` / `{label: メールアドレス}` / `{testid: ...}` / `{css: ...}` 等の dict で記述。Playwright 公式の `get_by_*` 系 API に 1 対 1 対応
  - **assertion は `expect()` のみ**: 自前 `body_check` と HTML 文字列 match を全廃。`expect_no_text` step で代替
  - **新モジュール**:
    - `scenario_test/locator_steps.py` — YAML step kind → Locator/expect API dispatcher (テーブル駆動)
    - `scenario_test/evidence.py` — 1 testcase 分の HAR/trace/console/pageerror/axe/CWV を集中管理
    - `scenario_test/a11y.py` — axe-core ランナー内蔵モジュール (page_role に応じて自動実行)
    - `scenario_test/cwv.py` — Core Web Vitals ランナー内蔵モジュール (page_role に応じて自動実行)
  - **削除**:
    - `scenario_test/nav_helpers.py` (全関数を locator-first で置換)
    - `scripts/trace_link.py` (`upload_evidence.py` に統合)
    - 古い `path` ベース step / `body_check` / `slug` config / `enable_scroll_demo` config
  - **新規 scripts**:
    - `scripts/upload_evidence.py` — trace/HAR/video の Drive アップ統合 (拡張子から自動判定)
    - `scripts/record_to_yaml.py` — Playwright codegen Python 出力 → 新スキーマ YAML 変換
  - **Min-2 (slug 衝突)**: `_default_test_id(role, url)` で URL 全 path + sha1[:6] suffix を付与し衝突回避
  - **Maj-7 (責務分離)**: `playwright_executor.py` 678 → 約 380 行へ縮小 (evidence は `EvidenceCollectors` へ完全分離)
  - **report.md** に axe-core 違反 / Core Web Vitals metrics を表示
  - templates/ を 6 ファイル全部新スキーマで書き直し
  - docs/ から「v0.3.0 以降で検討」記述を解消、`navigate_post` / `find_click_target` / `detect_body_errors` 等の旧 helper 言及を削除
- Skills: 36個 (変化なし)

### v4.1.0
- **`playwright-scenario-test` v0.2.0** (理論ベース化):
  - `docs/` 配下に方法論を 6 ファイル (総論 / page role / 技法 / Playwright API / bug report) + checklists 11 ファイル (lp/list/item/edit/form/search/dashboard/auth/cart-checkout/modal-wizard/common) として整備
  - 出典: HTSM v6.3 (James Bach), ISTQB CTFL 4.2, ISO/IEC/IEEE 29119-3:2021, WCAG 2.2, OWASP Top 10:2025, FEW HICCUPPS, Hendrickson Cheat Sheet
  - 新規スクリプト: `classify_page_role.py` (a11y tree から自動 role 判定), `generate_test_plan.py` (Pairwise 込み YAML 自動生成), `run_a11y_scan.py` (axe-core), `check_cwv.py` (LCP/CLS/TTFB), `record_scenario.py` (Playwright codegen ラッパー), `trace_link.py` (trace.zip → playwright.dev URL)
  - 役割別 testcase YAML テンプレート 4 件 (list/edit/form/auth) を追加
  - SKILL.md は実行手順とナビゲーションに集中 (332 → 245 行)
  - pyproject.toml に optional-dependencies `a11y` (axe-playwright-python) を追加
- **公式 Agent Skill 仕様準拠**: 14 skill の frontmatter を Pattern A (description 単体に Triggers 埋め込み) から Pattern B (description + 公式 `when_to_use` フィールド分離) へ移行。対象 skill: codex / data-analyst-export / data-analyst-sql-optimization / deepwiki-transfer / docker-container-access / git-gh-operations / google-auth / google-chat / google-drive / markdown-writing / official-skills-autoloader / playwright-scenario-test / python-execution / qa-security-scan / skill-stats。`description` は概要に集中、`when_to_use` に Trigger phrase を分離して auto-invoke 精度向上 (公式 1,536 字上限内)。`mcp-builder` は Anthropic 公式 (Apache-2.0) のため改変せず。
- **コード品質改善**:
  - `google-chat/scripts/gchat_read.py`: `DEFAULT_SPACE_ID` のハードコード (`AAQA6AWG1iE`) を撤去。env `GCHAT_DEFAULT_SPACE` で指定するか `--space` を required にする運用に変更
  - `google-auth/SKILL.md`: `allowed-tools` から不要な `Bash(pip *)` を削除 (uv で完結)
  - `google-drive/scripts/gdrive_fetch.py`: `upload_file` 内の dead な再 `import os` を削除
  - `playwright-scenario-test/SKILL.md`: 不足していた `allowed-tools` (Read / Bash(uv *) / Bash(python *)) を追加
- **新規 Skill `playwright-scenario-test`** (self-contained uv project):
  - Playwright + curl で Web シナリオ E2E テストを並列実行
  - HUD オーバーレイ (カーソル + 字幕) 焼き込み済み動画 + Markdown レポート生成
  - Drive アップロード自動化までサポート
  - 外部プロジェクトは `config.yaml` + `testcases/*.yaml` のみで利用可能
- **新規 Skill `google-drive`**:
  - Google Drive / Docs のファイルエクスポート / ダウンロード / アップロード (公開共有リンク付与)
  - 認証は `ndf:google-auth` の `get_credentials()` に委譲
- **新規 Skill `google-chat`**:
  - Google Chat スペースのメッセージ・スペース一覧取得 (Chat API)
  - 認証は `ndf:google-auth` の `get_credentials()` に委譲
  - 旧 uttarov 版のハードコードパス (`/work/uttarov2-doc/...`) を撤廃し、
    sibling-skill discovery (`GOOGLE_AUTH_SCRIPTS` env / `~/.claude/skills/google-auth/scripts` /
    隣接スキル) でフォールバック
- **`google-auth` v0.2.0 (互換性破壊)**:
  - Python ライブラリ用法 (`from google_auth import get_credentials`) を追加
  - `--manual` 手動 copy-paste フロー (ローカルサーバ不要、コンテナ環境対応)
  - トークン自動リフレッシュ + スコープ不足検出 / 自動マージ
  - `--show` / `--clear` サブコマンド
  - **トークン保存先を `/tmp/google_token.json` → `~/.config/gcloud/google_token.json` に変更**
    (env `GOOGLE_TOKEN_FILE` で上書き可)
  - `client_secret` パスは `--client-secret` → env `GOOGLE_CLIENT_SECRET` →
    `${CLAUDE_SKILL_DIR}/client_secret.json` → CWD の順
- Skills: 33個 → **36個**

### v4.0.0 (BREAKING: Codex MCP廃止 + レガシー救済機構削除)
- **Codex MCP サーバを削除** (`.mcp.json` から `codex` エントリを削除)
  - 理由: `/ndf:codex` skill (CLI直接実行) で十分であり、MCP 経由の制約 (ホスト側ファイル読み取り制限等) よりも CLI 直接実行の方が有用
  - 影響: `mcp__codex__codex` / `mcp__codex__codex-reply` は利用不可
  - 代替: `/ndf:codex` skill の手順で `codex exec` をバックグラウンド実行、または `corder` エージェント経由で呼び出し
- **corder エージェントを CLI ベースに書き換え**
  - MCP 呼び出しを `/ndf:codex` skill 参照に変更
  - Serena / Context7 MCP は引き続き利用
- 他エージェント (researcher, qa, devops-engineer, debugger, code-reviewer, director) の description から Codex MCP 言及を削除 / CLI ベースに更新
- `skills/codex` の MCP 版との使い分け節を corder エージェントとの使い分けに書き換え
- `skills/qa-security-scan/03-report-template.md` の JS 疑似コードを `codex exec` bash 例に置換
- **レガシー CLAUDE.ndf.md 救済機構を削除** (v3.0.0 で本体廃止、以降の救済装置を除去)
  - `hooks/hooks.json` の CLAUDE.ndf.md 検出 hook を削除
  - `skills/cleanup/` を削除 (`plugin.json` の参照も削除)
  - まだ残っているユーザーは今後手動で `CLAUDE.ndf.md` を削除してください
- Skills: 34個 → **33個** (`cleanup` 削除)

### v3.7.0
- **Transcript保持期間の自動管理**:
  - `SessionStart` hook (matcher: `startup`) + `scripts/ensure-retention.sh` を追加
  - `~/.claude/settings.json` の `cleanupPeriodDays` を最低 90 日に保つ (既に 90 以上ならそのまま)
  - 7 日タイムスタンプガード (`~/.claude/.ndf-retention-checked`) で多重実行防止
  - Claude Code 本体の公開 API/ドキュメントには「プラグインインストール時」hook が存在しないため、`SessionStart + startup` matcher が事実上の最適解
- **`/ndf:skill-stats` skillを追加**:
  - `~/.claude/projects/**/*.jsonl` transcript から NDF skill 利用統計を集計
  - 項目: 呼び出し数 / 関連話題数 / ヒット数 / ヒット率
  - 関連話題判定は SKILL.md frontmatter の `Triggers: '..', '..'` 行を使用 (明示されていない skill は計算対象外)
  - Python 実装、標準ライブラリのみ
  - skill description の網羅性を評価するツールとして機能
- Skills: 33個 → **34個**

### v3.6.0
- carmo-system-consoleから汎用skill/commandを抽出してNDFに統合
- **新規Skills（13個）**:
  - 原則系（5個）: `branch-fix-strategy`, `implementation-plan`, `investigation-rules`, `problem-solving`, `logging-guidelines`
  - ワークフロー系（7個）: `sync-main`, `cherry-pick-pr`, `deploy`, `review-branch`, `review-pr-comments`, `resolve-pr-comments`, `browser-test`
  - 外部AI委譲（1個）: `codex`（CLI直接実行、MCP版corderとの使い分け）
- **既存Skill改修**:
  - `pr`: `--draft`フラグ対応、既存PR説明の自動更新、base非mainの場合`cherry-pick-pr`誘導、`.github/pull_request_template.md`サポート
- Skills: 20個 → **33個**
- PR/コードレビュー系の責務分担を明確化:
  - `review` = PR単位レビュー（Approve/Request Changes判定）
  - `review-branch` = ローカル差分レビュー（PR前のセルフレビュー）
  - `review-pr-comments` = 既存PRコメントの分類（READ-ONLY）
  - `fix` = コメント対応の修正実施
  - `resolve-pr-comments` = 修正完了後の返信+Resolve（クロージング）

### v3.5.0 (破壊的変更: scanner削除)
- Claude Code Read toolのmultimodal/PDF native対応、および v3.4.0で追加された `official-skills-autoloader` により冗長になったAgent/Skillを整理
- **削除Agent**:
  - `scanner` (Office抽出) → autoloader + 公式docx/pptx/xlsx Skillで代替
- **削除Skills**:
  - `scanner-pdf-analysis` → Read tool の PDF native対応で代替
  - `scanner-excel-extraction` → autoloader + 公式xlsx Skillで代替（plugin.jsonのdangling ref整理）
  - `skill-development` → 公式 `skill-creator` Skillで代替（autoloader取得可能）
  - `corder-code-templates`, `corder-test-generation` → Claude本体のコード生成能力で代替
  - `researcher-report-templates` → researcher agent description／Claude本体で代替
- Agents: 9個 → **8個**
- Skills: 25個 → **20個**
- 移行ガイド: `/ndf:scanner` を呼んでいた処理は、autoloaderまたはRead toolへ切替

### v3.4.0
- Anthropic公式の定番Skill `mcp-builder` を取込（Apache-2.0、LICENSE.txt同梱）
- 公式Skillインストーラ `plugins/ndf/scripts/install-official-skills.sh` を追加
  - `--list`: 利用可能Skill一覧（ライセンス分類付き）
  - `--scope user/project`: インストール先選択
  - `--all` / 個別指定: 選択的インストール
  - `--update`: 公式リポジトリの最新化
  - シンボリックリンク方式で軽量
- プロプライエタリSkill（docx/pptx/xlsx/pdf）は再配布せず、上記インストーラで個人利用者環境に配置
- インストール手順・ライセンス方針を `docs/official-skills-installation.md` にまとめ
- `official-skills-autoloader` Skillを追加: Word/Excel/PowerPoint/PDF等の要求時に必要な公式Skillを自動ダウンロード→読込して即使用可能（利用者はインストール作業不要）
- Skills: 23個 → 25個

### v3.3.0
- 定番サブエージェント3個を追加（いずれも `model: sonnet`）
  - **debugger**: エラー・バグの根本原因分析
  - **devops-engineer**: Dockerfile/CI/CD/Kubernetes
  - **code-reviewer**: git diff / PR一般レビュー（corderと差別化: Codex非使用）
- Agents: 6個 → 9個

### v3.2.0
- サブエージェントに `model:` 指定を追加し、コスト最適化
  - director: `opus`（計画・設計判断）
  - corder, data-analyst, researcher, qa: `sonnet`
  - scanner: `haiku`
- scannerエージェントをOffice専用に縮小
  - 画像・PDFはClaude Code built-inのRead tool（multimodal, pages）で処理する方針に変更
- corderのdescriptionを「Codex第二意見レビュー／大規模調査」用途に明確化
- researcherのdescriptionをAWS Docs / Chrome DevTools専用に縮小

### v3.1.0
- Kiro CLI対応（`.kiro/` 配下のインストーラ、プロンプト、スキルリンク）
- `google-auth` スキル追加

### v3.0.0 (破壊的変更)
- Serena MCPを`mcp-serena`プラグインに分離
- memory系スキル5個を廃止（serena, memory-handling, serena-memory-strategy, mem-capture, mem-review）
- CLAUDE.ndf.md注入仕組みを廃止（inject-plugin-guide.js削除）
- `ndf-policies`スキル追加（ポリシー常時注入）
- `/ndf:cleanup`スキル追加（CLAUDE.ndf.md後始末）
- SessionStartフックをCLAUDE.ndf.md検出警告に変更
- Skills: 25個→23個

### v2.8.0
- `deepwiki-transfer`スキル追加
- Skills: 23個→25個（knowledge-reorg含む）

### v2.7.0
- commandsをskillsに統合（Claude Code 2.1.3対応）

### v2.6.0
- NDFプラグインのMCP構成を最適化し個別プラグイン化

### v2.0.0
- GitHub MCP, Serena MCP, Context7 MCPを公式プラグインに移行
