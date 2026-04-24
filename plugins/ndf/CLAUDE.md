# NDF Plugin - 開発者向けガイドライン

## 概要

**NDFプラグインの開発・メンテナンス**を行うAIエージェント向けガイドライン。

## プラグイン情報

- **名前**: ndf
- **現在バージョン**: 3.6.0
- **種類**: 統合プラグイン（Codex MCP + Skills + Agents + Hooks）
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
├── skills/                      # スキル（33個）
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
│   ├── cleanup/                 # CLAUDE.ndf.md後始末
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
