# NDF Plugin

Claude Code開発環境を**オールインワン**で強化する統合プラグインです。

## 概要

このプラグイン1つで、以下の**すべて**の機能を利用できます：

1. **MCP統合**: 10個の強力なMCPサーバー（GitHub、Serena、BigQuery、Notion、DBHub、Chrome DevTools、AWS Docs、Codex CLI、Context7、Claude Code）
2. **開発ワークフロー**: PR作成、レビュー、マージ、ブランチクリーンアップコマンド
3. **専門エージェント**: 5つの特化型AIエージェント（データ分析、コーディング、調査、ファイル読み取り、品質管理）
4. **自動フック**: Slack通知

## インストール

### 前提条件

- Claude Code がインストール済み
- Python 3.10以上（Serena、BigQuery MCP用）
- `uvx` がインストール済み（`pip install uv`）
- Node.js（DBHub、Chrome DevTools MCP用）
- Codex CLI（Codex CLI MCP用）- オプション

### ステップ1: マーケットプレイスの追加

```bash
# Claude Codeで実行
/plugin marketplace add https://github.com/takemi-ohama/ai-agent-marketplace
```

### ステップ2: プラグインのインストール

```bash
# Claude Codeで実行
/plugin install ndf@ai-agent-marketplace
```

### ステップ3: .envファイルの作成

プロジェクトルートに `.env` ファイルを作成し、必要な認証情報を設定します。

```bash
# GitHub MCP (必須 - 基本機能用)
# トークン取得: https://github.com/settings/tokens
# 必要なスコープ: repo, read:org, workflow
GITHUB_PERSONAL_ACCESS_TOKEN=

# Notion MCP (オプション - Notion使用時のみ)
# トークン取得: https://www.notion.so/my-integrations
NOTION_API_KEY=

# BigQuery MCP (オプション - BigQuery使用時のみ)
# サービスアカウント作成: https://console.cloud.google.com/iam-admin/serviceaccounts
GOOGLE_APPLICATION_CREDENTIALS=

# DBHub MCP (オプション - データベース操作用)
# データベース接続文字列 (DSN)
DATABASE_DSN=

# Slack通知 (オプション)
# Slack Appセットアップ手順は下記の詳細設定を参照
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
SLACK_USER_MENTION=  # 例: <@U0123456789>

# Context7 MCP (オプション - 最新コード例とドキュメント取得用)
# API Key取得: https://context7.com
CONTEXT7_API_KEY=

# 注意: Serena MCP、AWS Documentation MCP、Chrome DevTools MCP、Codex CLI MCPは認証不要
# Codex CLI MCPはインストール必要: https://github.com/openai/codex/releases
# インストール後、'codex login'を実行
```

#### .envファイルの保護

`.env` ファイルには機密情報が含まれるため、必ず `.gitignore` に追加してください：

```bash
echo ".env" >> .gitignore
```

#### 各認証情報の詳細設定

<details>
<summary><strong>DATABASE_DSN の設定方法（DBHub MCP用）</strong></summary>

DBHub MCPは複数のデータベースに対応しています。

**PostgreSQL:**
```bash
DATABASE_DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=disable"
```

SSL接続が必要な場合：
```bash
DATABASE_DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
```

**MySQL / MariaDB:**（同じDSN形式）
```bash
DATABASE_DSN="mysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```

SSH踏み台サーバー経由で接続する場合：
1. SSHトンネルを作成（ローカルポート転送）
   ```bash
   ssh -L 3307:DB_HOST:3306 USER@BASTION_HOST -N
   ```
2. ローカルポート経由で接続
   ```bash
   DATABASE_DSN="mysql://USERNAME:PASSWORD@localhost:3307/DATABASE"
   ```

**SQLite:**
```bash
DATABASE_DSN="sqlite:///PATH/TO/DATABASE.db"
```

**SQL Server:**
```bash
DATABASE_DSN="sqlserver://USERNAME:PASSWORD@HOST:PORT?database=DATABASE"
```

**注意事項:**
- パスワードに特殊文字が含まれる場合は、URLエンコードが必要
- ローカルデータベースの場合は `localhost` を使用

</details>

<details>
<summary><strong>SLACK_BOT_TOKEN と SLACK_CHANNEL_ID の設定方法</strong></summary>

Slack通知を有効にするには、Slack Appを作成してBot Tokenとチャンネル IDを取得する必要があります。

**ステップ1: Slack Appの作成**

1. https://api.slack.com/apps にアクセス
2. "Create New App" をクリック
3. "From scratch" を選択
4. App名を入力（例: "Claude Code Notifier"）
5. Workspaceを選択

**ステップ2: Bot Token Scopesの追加**

1. 左メニューから "OAuth & Permissions" を選択
2. "Scopes" セクションまでスクロール
3. "Bot Token Scopes" で以下を追加：
   - `chat:write` （必須 - メッセージ投稿用）
   - `chat:write.public` （推奨 - 公開チャンネル投稿用）
   - `channels:read` （オプション - チャンネル情報取得用）

**ステップ3: Workspaceへのインストール**

1. ページ上部の "Install to Workspace" をクリック
2. 権限を確認して "Allow" をクリック
3. **Bot User OAuth Token** をコピー（`xoxb-`で始まる）
   → これを `.env` の `SLACK_BOT_TOKEN` に設定

**ステップ4: Botをチャンネルに追加**

1. Slackで通知先チャンネルを開く
2. チャンネル名をクリック → "Integrations" タブ
3. "Add apps" をクリック
4. 作成したアプリを選択して追加

**ステップ5: チャンネルIDの取得**

1. 通知先チャンネルを開く
2. チャンネル名をクリック
3. 下部の「その他」→ チャンネルIDをコピー（`C`で始まる）
   → これを `.env` の `SLACK_CHANNEL_ID` に設定

**ステップ6: ユーザーIDの取得（オプション - 通知音用）**

1. Slackでプロフィールを開く
2. "その他" → "メンバーIDをコピー"（`U`で始まる）
3. メンション形式で設定：
   ```bash
   SLACK_USER_MENTION="<@U0123456789>"
   ```

**最終的な.env設定例:**
```bash
SLACK_BOT_TOKEN="xoxb-YOUR-BOT-TOKEN-HERE"
SLACK_CHANNEL_ID="C0123456789"
SLACK_USER_MENTION="<@U0123456789>"  # オプション
```

**⚠️ セキュリティ注意:**
- Bot Tokenは絶対にGitにコミットしない
- トークンが漏洩した場合は即座に無効化（Revoke）
- 最小限の権限（Scope）のみを付与

</details>

<details>
<summary><strong>Context7 API Keyの取得方法</strong></summary>

Context7 MCPは最新のコード例とドキュメントを取得します。API Keyは任意ですが、設定すると高速化されます。

**ステップ1: アカウント作成**

1. https://context7.com にアクセス
2. アカウントを作成またはログイン

**ステップ2: API Keyの取得**

1. ダッシュボードまたは設定ページにアクセス
2. API Keyセクションを探す
3. 新しいKeyを生成
4. Keyをコピーして `.env` に設定

```bash
CONTEXT7_API_KEY="your-api-key-here"
```

**注意:**
- Context7 MCPはAPI Key無しでも動作しますが、レート制限があります
- プライベートリポジトリへのアクセスにはAPI Keyが必要

</details>

### ステップ4: Claude Codeを再起動

`.env` ファイルに値を入力したら、Claude Codeを再起動してMCPサーバーとフックをロードします。

## 機能詳細

### 1. 開発ワークフローコマンド

開発の各段階で使用するコマンド群です。効率的なワークフローを実現します。

#### `/serena`
**用途:** Serena MCPを使用した開発記憶（メモリー）の記録  
**使用タイミング:** 重要な実装内容や設計判断を記録したいとき

#### `/pr`
**用途:** 現在のブランチから自動的にプルリクエストを作成  
**使用タイミング:** 機能実装やバグ修正が完了し、レビューを依頼したいとき  
コミット履歴とdiffを分析し、適切なPR説明を自動生成します。

#### `/review`
**用途:** 指定されたPRの内容をレビュー  
**使用タイミング:** 他の開発者のPRをレビューする必要があるとき  
コード品質、セキュリティ、ベストプラクティスの観点から包括的にレビューします。

#### `/fix`
**用途:** PRのレビューコメントを確認し、指摘事項に対応  
**使用タイミング:** PRにレビューコメントが付いたとき  
レビュー内容を分析し、必要な修正を実施してコミット・プッシュします。

#### `/merged`
**用途:** PRマージ後のローカルブランチクリーンアップ  
**使用タイミング:** 自分が作成したPRがマージされた直後  
mainブランチを更新し、マージ済みのfeatureブランチを安全に削除します。

#### `/clean`
**用途:** マージ済みの古いブランチを一括クリーンアップ  
**使用タイミング:** ローカルに不要なブランチが溜まってきたとき  
リモートで削除済みのブランチをローカルからも削除します。

### 3. 専門エージェント (5種類)

**重要**: このプラグインには`CLAUDE.md`が含まれており、メインエージェント（Claude）に対してサブエージェントの積極的な活用を促す指示が記載されています。

**サブエージェントの活用方針:**
- 複雑なタスクや専門性の高いタスクは、適切なサブエージェントに委譲
- メインエージェントは全体の調整役として機能
- 各サブエージェントは専門MCPツールを効果的に活用

詳細は `plugins/ndf/CLAUDE.md` を参照してください。

#### `data-analyst` エージェント
**専門領域:** データ分析とSQL操作

**使用MCPツール:**
- BigQuery MCP
- DBHub MCP

**機能:**
- SQL生成と実行
- クエリ結果の分析と解釈
- データの傾向とパターン発見
- CSV/JSON/Excel形式でのデータ出力
- レポート生成とデータ可視化の準備

**使用例:**
```
@data-analyst BigQueryで過去1ヶ月の売上データを分析してください
```

#### `corder` エージェント
**専門領域:** 高品質コード生成

**使用MCPツール:**
- Codex CLI MCP（コードレビュー）
- Serena MCP（コード構造理解）
- Context7 MCP（最新ベストプラクティス）

**機能:**
- クリーンで読みやすいコードの作成
- 設計パターンとアーキテクチャの適用
- AIによるコードレビューと品質保証
- セキュリティ脆弱性のチェック
- リファクタリング提案

**使用例:**
```
@corder ユーザー認証機能を実装してください。セキュリティとテストも考慮して
```

#### `researcher` エージェント
**専門領域:** 情報収集と分析

**使用MCPツール:**
- Codex CLI MCP（コードベース分析）
- AWS Documentation MCP（AWS公式ドキュメント）
- Chrome DevTools MCP（Webスクレイピング）

**機能:**
- 技術ドキュメントの調査と要約
- Webサイトからの情報収集
- コードベースのアーキテクチャ分析
- 複数ソースからの情報統合
- スクリーンショットとPDF取得

**使用例:**
```
@researcher AWS Lambda関数のベストプラクティスを調査してください
```

#### `scanner` エージェント
**専門領域:** ファイル読み取りとOCR

**使用MCPツール:**
- Codex CLI MCP（ファイル読み取り）

**機能:**
- PDFドキュメントのテキスト抽出
- 画像内のテキスト認識（OCR）
- PowerPoint/Excelファイルの読み取り
- 読み取った内容の構造化
- Markdown/CSV/JSON形式への変換

**使用例:**
```
@scanner document.pdfの内容を読み取って要約してください
```

#### `qa` エージェント
**専門領域:** 品質管理とテスト

**使用MCPツール:**
- Codex CLI MCP（コードレビュー、セキュリティチェック）
- Serena MCP（コードベース分析）
- Chrome DevTools MCP（パフォーマンステスト）
- Claude Code MCP（プラグイン品質検証）

**機能:**
- コード品質レビューとリファクタリング提案
- セキュリティ脆弱性検出（OWASP Top 10対応）
- パフォーマンステスト（Core Web Vitals評価）
- テストカバレッジとエッジケース検証
- ドキュメント品質チェック
- Claude Codeプラグイン仕様準拠確認

**使用例:**
```
@qa このコードの品質とセキュリティをレビューしてください
@qa Webアプリケーションのパフォーマンスを測定してください
@qa プラグインがClaude Code仕様に準拠しているか確認してください
```

### 2. MCP統合 (10サーバー)

このプラグインは10個の強力なMCPサーバーを統合しています。各MCPの詳細な使用方法やベストプラクティスは、エージェント向けガイド `plugins/ndf/CLAUDE.md` を参照してください。

**GitHub、Serena、Notion** などの基本MCP、**BigQuery、DBHub** などのデータベースMCP、**Chrome DevTools、AWS Docs、Codex CLI、Context7、Claude Code** など専門MCPを含みます。

#### 使用しないMCPの無効化（推奨）

パフォーマンス向上のため、使用しないMCPは無効化することを推奨します。

**手順:**

Claude Codeで以下のコマンドを実行します：

```
/mcp
```

表示されるMCPサーバー一覧から、使用しないMCPを選択して無効化できます。

**補足:**
- MCPの有効化/無効化は各プロジェクトごとに設定されます
- 設定はClaude Codeの設定ファイル（`.claude/settings.json`等）に保存されます
- 変更後、Claude Codeを再起動すると設定が反映されます

### 3. 自動フック

Claude Code終了時に自動的に以下が実行されます：

#### Slack通知

作業終了時にSlackへ要約通知を送信します（`SLACK_BOT_TOKEN`設定時のみ）。

**機能:**
- Claude Codeとのやり取りをAIが自動要約（40文字）
- 会話履歴、transcript、git diffから最適な情報源を自動選択
- リポジトリ名とタイムスタンプも含めて通知

**設定:**
- `.env`に`SLACK_BOT_TOKEN`、`SLACK_CHANNEL_ID`、`SLACK_USER_MENTION`を設定
- 詳細な設定手順は上記の[SLACK_BOT_TOKENとSLACK_CHANNEL_IDの設定方法](#各認証情報の詳細設定)を参照
- 設定後、Claude Codeを再起動で有効化

**注意:**
- プラグイン更新後も再起動が必要です
## 利用方法

セットアップが完了したら、Claude Codeで自然言語でリクエストするだけです：

```
このリポジトリのオープンなPRを確認して
```

Claude Codeが自動的に適切なMCPツールを選択・利用します。

また、スラッシュコマンドも利用可能：

```
/pr
/review 123
/merge
```

## セキュリティのベストプラクティス

- ✅ 環境変数でトークンを管理
- ✅ `.env` ファイルを `.gitignore` に追加
- ✅ 最小限のスコープ/権限を使用
- ✅ トークンを定期的にローテーション
- ❌ トークンをコードやドキュメントにコミットしない

## サポート

問題が発生した場合：
1. 上記のトラブルシューティングセクションを確認
2. GitHubリポジトリでイシューを作成: https://github.com/takemi-ohama/ai-agent-marketplace/issues

## ライセンス

MIT License

## 作者

takemi-ohama - https://github.com/takemi-ohama

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずイシューを開いて変更内容を議論してください。
