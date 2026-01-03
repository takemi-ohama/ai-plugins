# NDF Plugin

Claude Code開発環境を**オールインワン**で強化する統合プラグインです。

## 概要

このプラグイン1つで、以下の**すべて**の機能を利用できます：

1. **MCP統合**: 7個のMCPサーバー（Notion、BigQuery、DBHub、Chrome DevTools、AWS Docs、Codex CLI、Claude Code）
2. **開発ワークフロー**: PR作成、レビュー、マージ、ブランチクリーンアップコマンド
3. **専門エージェント**: 5つの特化型AIエージェント（データ分析、コーディング、調査、ファイル読み取り、品質管理）
4. **Skills**: 8個のモデル起動型機能モジュール（SQL最適化、コードテンプレート、テスト生成、PDF解析等）
5. **自動フック**: Slack通知

> **Note (v2.0.0)**: GitHub MCP、Serena MCP、Context7 MCPは公式プラグイン（`anthropics/claude-plugins-official`）に移行しました。必要に応じて個別にインストールしてください。

## インストール

### 前提条件

- Claude Code がインストール済み
- Python 3.10以上（BigQuery MCP用）
- `uvx` がインストール済み（`pip install uv`）
- Node.js（DBHub、Chrome DevTools MCP用）
- Codex CLI（Codex CLI MCP用）- オプション

### 公式プラグインのインストール（推奨）

GitHub、Serena、Context7 MCPは公式プラグインとして提供されています：

```bash
# Claude Codeで実行
/plugin install github@anthropics/claude-plugins-official
/plugin install serena@anthropics/claude-plugins-official
/plugin install context7@anthropics/claude-plugins-official
```

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
# Notion MCP (オプション - Notion使用時のみ)
# Integration Token取得: https://www.notion.so/my-integrations
NOTION_TOKEN=

# BigQuery MCP (オプション - BigQuery使用時のみ)
# GCPプロジェクトID、ロケーション、サービスアカウントキーファイル
BIGQUERY_PROJECT=
BIGQUERY_LOCATION=US
BIGQUERY_KEY_FILE=

# DBHub MCP (オプション - データベース操作用)
# データベース接続文字列 (DSN)
DSN=

# Slack通知 (オプション)
# Slack Appセットアップ手順は下記の詳細設定を参照
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
SLACK_USER_MENTION=  # 例: <@U0123456789>

# 注意:
# - AWS Docs MCP、Chrome DevTools MCPは認証不要
# - Codex CLI MCPはインストール必要: https://github.com/openai/codex/releases
#   インストール後、'codex login'を実行
# - GitHub MCP、Serena MCP、Context7 MCPは公式プラグインを使用してください
```

#### .envファイルの保護

`.env` ファイルには機密情報が含まれるため、必ず `.gitignore` に追加してください：

```bash
echo ".env" >> .gitignore
```

#### 各認証情報の詳細設定

<details>
<summary><strong>DSN（DATABASE_DSN）の設定方法（DBHub MCP用）</strong></summary>

DBHub MCPは複数のデータベースに対応しています。環境変数名は`DSN`または`DATABASE_DSN`のどちらでも使用可能です。

**PostgreSQL:**
```bash
DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=disable"
```

SSL接続が必要な場合：
```bash
DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
```

**MySQL / MariaDB:**
```bash
DSN="mysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```

SSH踏み台サーバー経由で接続する場合：
1. SSHトンネルを作成（ローカルポート転送）
   ```bash
   ssh -L 3307:DB_HOST:3306 USER@BASTION_HOST -N
   ```
2. ローカルポート経由で接続
   ```bash
   DSN="mysql://USERNAME:PASSWORD@localhost:3307/DATABASE"
   ```

**SQLite:**
```bash
DSN="sqlite:///PATH/TO/DATABASE.db"
```

**SQL Server:**
```bash
DSN="sqlserver://USERNAME:PASSWORD@HOST:PORT?database=DATABASE"
```

**注意事項:**
- パスワードに特殊文字が含まれる場合は、URLエンコードが必要（例: `@` → `%40`, `#` → `%23`）
- ローカルデータベースの場合は `localhost` を使用
- `DSN`と`DATABASE_DSN`は同じ意味（どちらを使用してもOK）

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

### ステップ4: Claude Codeを再起動

`.env` ファイルに値を入力したら、Claude Codeを再起動してMCPサーバーとフックをロードします。

## 環境変数リファレンス

各MCPサーバーが使用する環境変数の完全な一覧です。太字は必須、通常テキストはオプションです。

### 📋 環境変数テンプレート

プロジェクトルートに以下の`.env`ファイルを作成してください：

```bash
# ============================================
# Chrome DevTools MCP - Web調査
# ============================================
# 専用環境変数なし - envFileのみ

# ============================================
# Codex CLI MCP - コードレビュー
# ============================================
# すべてオプション - ローカルインストール推奨
# CODEX_HOME=/path/to/codex/home
# OPENAI_API_KEY=your-openai-api-key
# OPENAI_BASE_URL=https://api.openai.com/v1
# AZURE_OPENAI_API_KEY=your-azure-openai-key
# MISTRAL_API_KEY=your-mistral-api-key

# ============================================
# Notion MCP - Notionドキュメント管理
# ============================================
NOTION_TOKEN=your-notion-token-here

# オプション設定
# OPENAPI_MCP_HEADERS={"Authorization": "Bearer token"}
# AUTH_TOKEN=your-auth-token

# ============================================
# AWS Docs MCP - AWS公式ドキュメント
# ============================================
# FASTMCP_LOG_LEVEL=ERROR
# AWS_DOCUMENTATION_PARTITION=aws
# MCP_USER_AGENT=custom-user-agent

# ============================================
# BigQuery MCP - BigQueryデータ分析
# ============================================
BIGQUERY_PROJECT=your-gcp-project-id
BIGQUERY_LOCATION=US

# オプション設定
# BIGQUERY_DATASETS=dataset1,dataset2
# BIGQUERY_KEY_FILE=/path/to/service-account-key.json

# ============================================
# DBHub MCP - データベース操作
# ============================================
# Method 1: DSN（推奨）
DSN=mysql://user:password@host:3306/database

# Method 2: 個別指定
# DB_TYPE=mysql
# DB_HOST=localhost
# DB_USER=username
# DB_PASSWORD=password
# DB_NAME=database
# DB_PORT=3306

# オプション設定
# TRANSPORT=http
# PORT=8080
# READONLY=false

# SSH踏み台サーバー経由接続（オプション）
# SSH_HOST=bastion.example.com
# SSH_PORT=22
# SSH_USER=ssh-user
# SSH_PRIVATE_KEY_PATH=/path/to/ssh/key
# SSH_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...
# SSH_PASSWORD=ssh-password

# ============================================
# Claude Code MCP - Claude Code機能拡張
# ============================================
# すべてオプション
# MCP_TIMEOUT=30000
# MAX_MCP_OUTPUT_TOKENS=10000

# ============================================
# Slack通知 - 自動フック
# ============================================
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C0123456789
SLACK_USER_MENTION=<@U0123456789>
```

### 📊 MCPサーバー別環境変数詳細

> **Note (v2.0.0)**: GitHub MCP、Serena MCP、Context7 MCPは公式プラグイン（`anthropics/claude-plugins-official`）に移行しました。環境変数設定は各公式プラグインのドキュメントを参照してください。

#### 1. Chrome DevTools MCP

**専用環境変数なし** - `.env`ファイルの`envFile`設定のみ使用。

#### 2. Codex CLI MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| CODEX_HOME | オプション | `~/.codex` | Codex CLIのホームディレクトリ |
| OPENAI_API_KEY | オプション | - | OpenAI APIキー |
| OPENAI_BASE_URL | オプション | `https://api.openai.com/v1` | OpenAI APIのベースURL |
| AZURE_OPENAI_API_KEY | オプション | - | Azure OpenAI APIキー |
| MISTRAL_API_KEY | オプション | - | Mistral AIのAPIキー |

**注意:** Codex CLI MCPを使用するには、Codex CLIを事前にインストールし、`codex login`を実行してください。

インストール: https://github.com/openai/codex/releases

#### 3. Notion MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| **NOTION_TOKEN** | **必須** | - | Notion Internal Integration Token<br>取得: https://www.notion.so/my-integrations |
| OPENAPI_MCP_HEADERS | オプション | - | カスタムHTTPヘッダー（JSON形式） |
| AUTH_TOKEN | オプション | - | 追加の認証トークン |

#### 4. AWS Docs MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| FASTMCP_LOG_LEVEL | オプション | `ERROR` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`） |
| AWS_DOCUMENTATION_PARTITION | オプション | `aws` | AWSパーティション（`aws`, `aws-cn`, `aws-us-gov`） |
| MCP_USER_AGENT | オプション | - | カスタムUser-Agent |

**注意:** 認証不要でAWS公式ドキュメントにアクセスできます。

#### 5. BigQuery MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| **BIGQUERY_PROJECT** | **必須** | - | GCPプロジェクトID |
| BIGQUERY_LOCATION | オプション | `US` | BigQueryデータセットのロケーション |
| BIGQUERY_DATASETS | オプション | - | アクセス許可するデータセット（カンマ区切り） |
| BIGQUERY_KEY_FILE | オプション | - | サービスアカウントキーファイルのパス<br>（未指定の場合はApplication Default Credentials使用） |

**認証方法:**
1. **サービスアカウントキーファイル（推奨）**: `BIGQUERY_KEY_FILE`にJSON keyファイルのパスを指定
2. **Application Default Credentials（ADC）**: `BIGQUERY_KEY_FILE`を設定せず、以下のいずれかを使用
   - 環境変数`GOOGLE_APPLICATION_CREDENTIALS`でキーファイルのパスを指定
   - `gcloud auth application-default login`を実行してユーザー認証情報を使用

**注意:** NDFプラグインでは`BIGQUERY_KEY_FILE`を推奨します。ADCを使う場合は`BIGQUERY_KEY_FILE`を設定しないでください。

サービスアカウント作成: https://console.cloud.google.com/iam-admin/serviceaccounts

#### 6. DBHub MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| **DSN** または **DATABASE_DSN** | **必須（Method 1）** | - | データベース接続文字列<br>例: `mysql://user:pass@host:3306/db`<br>（両変数名をサポート） |
| **DB_TYPE** | **必須（Method 2）** | - | データベースタイプ（`mysql`, `postgres`, `sqlite`, `sqlserver`） |
| **DB_HOST** | **必須（Method 2）** | - | データベースホスト |
| **DB_USER** | **必須（Method 2）** | - | データベースユーザー名 |
| **DB_PASSWORD** | **必須（Method 2）** | - | データベースパスワード |
| **DB_NAME** | **必須（Method 2）** | - | データベース名 |
| DB_PORT | オプション | DB依存 | データベースポート（MySQL: 3306, PostgreSQL: 5432） |
| TRANSPORT | オプション | `http` | トランスポートプロトコル（`http`または`tcp`） |
| PORT | オプション | `8080` | MCPサーバーのポート |
| SSH_HOST | オプション | - | SSH踏み台サーバーのホスト |
| SSH_PORT | オプション | `22` | SSHポート |
| SSH_USER | オプション | - | SSHユーザー名 |
| SSH_PRIVATE_KEY_PATH | オプション | - | SSH秘密鍵のパス |
| SSH_PRIVATE_KEY | オプション | - | SSH秘密鍵の内容（直接指定） |
| SSH_PASSWORD | オプション | - | SSHパスワード（鍵認証推奨） |
| READONLY | オプション | `false` | 読み取り専用モード |

**接続方法の選択:**
- **Method 1（推奨）**: `DSN`または`DATABASE_DSN`のみ指定
- **Method 2**: `DB_TYPE`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`を個別指定

#### 7. Claude Code MCP

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| MCP_TIMEOUT | オプション | `30000` | MCPリクエストのタイムアウト（ミリ秒） |
| MAX_MCP_OUTPUT_TOKENS | オプション | `10000` | MCPレスポンスの最大トークン数 |

### 🔧 データベース接続文字列（DSN）の形式

#### PostgreSQL
```bash
DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=disable"
```

SSL接続が必要な場合：
```bash
DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require"
```

#### MySQL / MariaDB
```bash
DSN="mysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```

#### SQLite
```bash
DSN="sqlite:///PATH/TO/DATABASE.db"
```

#### SQL Server
```bash
DSN="sqlserver://USERNAME:PASSWORD@HOST:PORT?database=DATABASE"
```

**注意事項:**
- パスワードに特殊文字が含まれる場合は、URLエンコードが必要（例: `@` → `%40`, `#` → `%23`）
- ローカルデータベースの場合は `localhost` を使用

### 🔐 Slack通知の環境変数

| 環境変数 | 必須/オプション | デフォルト値 | 説明 |
|---------|--------------|------------|------|
| SLACK_BOT_TOKEN | 必須（Slack通知用） | - | Slack Bot User OAuth Token（`xoxb-`で始まる） |
| SLACK_CHANNEL_ID | 必須（Slack通知用） | - | 通知先チャンネルID（`C`で始まる） |
| SLACK_USER_MENTION | オプション | - | メンション対象ユーザーID（`<@U0123456789>`形式） |

詳細な設定手順は[SLACK_BOT_TOKENとSLACK_CHANNEL_IDの設定方法](#各認証情報の詳細設定)を参照してください。

### 🛡️ セキュリティのベストプラクティス

- ✅ `.env` ファイルを `.gitignore` に追加
- ✅ 最小限のスコープ/権限を使用
- ✅ トークンを定期的にローテーション
- ✅ チーム内で環境変数を安全に共有（1Password、AWS Secrets Manager等）
- ❌ トークンをコードやドキュメントにコミットしない
- ❌ トークンをSlack/メール等で平文送信しない

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

**重要**: このプラグインには`CLAUDE.ndf.md`が含まれており、メインエージェント（Claude）に対してサブエージェントの積極的な活用を促す指示が記載されています。

**サブエージェントの活用方針:**
- **タスクの種類に応じて適切なサブエージェントに委譲**
- Claude Code組み込み機能（Plan Mode、Explore Agent）と連携
- 各サブエージェントは専門MCPツールを効果的に活用

詳細は `plugins/ndf/CLAUDE.ndf.md` を参照してください。

> **Note (v2.0.0)**: directorエージェントはClaude Code組み込み機能（Plan Mode、Explore Agent）と重複するため削除されました。タスク統括にはClaude CodeのPlan Modeを使用してください。

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

> **Note (v2.0.0)**: Serena MCP、Context7 MCPは公式プラグインに移行しました。これらは引き続きcorderエージェントで使用可能ですが、別途インストールが必要です。

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

### 4. Skills (8種類) 🎯

**Claude Code Skills**は、Claudeが自律的に判断して起動する**モデル起動型**の機能モジュールです。各サブエージェントは、タスク内容に応じて適切なSkillsを自動的に活用します。

> **Note (v2.0.0)**: `director-project-planning`と`qa-code-review-checklist`は重複機能のため削除されました。プロジェクト計画にはClaude CodeのPlan Modeを、コードレビューチェックには公式プラグイン（`pr-review-toolkit`等）を使用してください。

#### Skills一覧

**Data Analyst Skills (2個):**
- ⚡ **data-analyst-sql-optimization** - SQL最適化パターンとベストプラクティス
  - N+1クエリ削減、インデックス活用、JOIN最適化
  - Before/After実例集（8パターン）
- 💾 **data-analyst-export** - クエリ結果を様々な形式でエクスポート
  - CSV（UTF-8 BOM、Excel互換）、JSON、Excel（複数シート）、Markdownテーブル

**Corder Skills (2個):**
- 📝 **corder-code-templates** - コード生成テンプレート集
  - REST APIエンドポイント（Express.js、FastAPI）
  - Reactコンポーネント（Hooks、状態管理）
  - データベースモデル（Sequelize、TypeORM、Mongoose）
  - 認証ミドルウェア（JWT、OAuth）
- 🧪 **corder-test-generation** - テストコード自動生成
  - ユニットテスト（Jest、Mocha、pytest）
  - AAA（Arrange-Act-Assert）パターン
  - テストフィクスチャ・モック生成

**Researcher Skills (1個):**
- 📊 **researcher-report-templates** - 調査レポートテンプレート集
  - 構造化された調査レポート
  - 技術比較テーブル
  - ベストプラクティスまとめ
  - エグゼクティブサマリー

**Scanner Skills (2個):**
- 📄 **scanner-pdf-analysis** - PDF解析とデータ抽出
  - テキスト抽出、テーブル検出とCSV変換
  - セクション・見出し識別、重要ポイント要約
- 📊 **scanner-excel-extraction** - Excelデータ抽出と構造化
  - 複数シート読み込み、JSON/CSV形式変換
  - 数式評価、大容量ファイル対応

**QA Skills (1個):**
- 🔒 **qa-security-scan** - セキュリティスキャンと脆弱性評価
  - OWASP Top 10チェックリスト（詳細な修正方法付き）
  - 認証・認可テスト、データ保護確認

#### Skillsの使い方

**自動起動（推奨）:**
Claudeは自然言語リクエストから適切なSkillsを自動判断して起動します。

```
このSQLクエリを最適化してください
→ data-analyst-sql-optimizationが自動起動

REST APIのテンプレートを使ってエンドポイントを作成してください
→ corder-code-templatesが自動起動

セキュリティスキャンを実行してください
→ qa-security-scanが自動起動
```

**トリガーキーワード例:**
- "optimize SQL", "slow query", "SQL最適化"
- "export data", "save results", "データ出力"
- "create API", "new component", "コードテンプレート"
- "generate tests", "create unit test", "テスト生成"
- "analyze PDF", "extract tables", "PDF解析"
- "security scan", "OWASP", "セキュリティスキャン"

#### Skillsの特徴

- **Model-invoked**: Claudeが自律的に判断して呼び出す
- **Progressive Disclosure**: メインドキュメント≤500行、詳細はテンプレート/スクリプトに分離
- **Sub-agent specialization**: 各サブエージェントの既存機能を補完
- **Templates & Scripts**: 実用的なテンプレートとスクリプトを提供

詳細は各Skillの`SKILL.md`を参照してください。

### 2. MCP統合 (7サーバー)

このプラグインは7個の強力なMCPサーバーを統合しています。各MCPの詳細な使用方法やベストプラクティスは、エージェント向けガイド `plugins/ndf/CLAUDE.md` を参照してください。

> **Note (v2.0.0)**: GitHub MCP、Serena MCP、Context7 MCPは公式プラグイン（`anthropics/claude-plugins-official`）に移行しました。

**Notion** などの基本MCP、**BigQuery、DBHub** などのデータベースMCP、**Chrome DevTools、AWS Docs、Codex CLI、Claude Code** など専門MCPを含みます。

#### MCPのデフォルト状態

コンテキスト使用量を最適化するため、よく使うMCPのみがデフォルトで有効化されています。

**デフォルトで有効（2つ）:**
- ✅ **Chrome DevTools MCP** - Web調査、パフォーマンステスト
- ✅ **Codex CLI MCP** - コードレビュー、ファイル読み取り

**デフォルトで無効（5つ）:**
- ⏸️ **Notion MCP** - コンテキストが大きいため無効
- ⏸️ **AWS Documentation MCP** - エラーが発生するため無効
- ⏸️ **BigQuery MCP** - 利用するプロジェクトが限られるため無効
- ⏸️ **DBHub MCP** - 利用するプロジェクトが限られるため無効
- ⏸️ **Claude Code MCP** - コンテキストが大きいため無効

> **Tip**: GitHub MCP、Serena MCP、Context7 MCPは公式プラグインからインストールして使用してください：
> ```bash
> /plugin install github@anthropics/claude-plugins-official
> /plugin install serena@anthropics/claude-plugins-official
> /plugin install context7@anthropics/claude-plugins-official
> ```

#### 無効化されているMCPを有効にする方法

特定のプロジェクトで無効化されているMCPを使いたい場合、`/mcp`コマンドで簡単に有効化できます：

**手順:**

1. **Claude Codeで`/mcp`コマンドを実行**

   チャット入力欄に以下を入力してEnter：
   ```
   /mcp
   ```

2. **MCP一覧から有効化したいMCPを選択**

   表示されるMCP一覧で：
   - 🟢 緑色のドット = 有効
   - ⚫ グレーのドット = 無効

   有効化したいMCP（例: `plugin:ndf:notion`）をクリックして選択します。

3. **Enable（有効化）を選択**

   選択したMCPの詳細画面で「Enable」ボタンをクリックします。

   または、一覧画面でMCP名の右側にあるトグルスイッチをクリックして有効化できます。

4. **（必要に応じて）認証情報を設定**

   BigQuery、DBHub、Notionなどを有効化した場合は、`.env`ファイルに対応する認証情報も設定してください：
   ```bash
   # .envファイルに追加
   NOTION_TOKEN=your_notion_integration_token_here
   DSN=mysql://user:pass@host:3306/db
   BIGQUERY_PROJECT=your-gcp-project-id
   BIGQUERY_KEY_FILE=/path/to/service-account-key.json
   ```

5. **Claude Codeを再起動**

   変更を反映するために、Claude Codeを終了して再起動します。

   ```bash
   # ターミナルから再起動する場合
   # Ctrl+C で終了後、再度起動
   claude
   ```

6. **有効化を確認**

   再度 `/mcp` コマンドを実行して、該当のMCPが🟢緑色になっていることを確認します。

**有効化の具体例:**

| MCP | 必要な認証情報 | 用途 |
|-----|-------------|------|
| **Notion MCP** | `NOTION_TOKEN` | Notionドキュメント管理 |
| **BigQuery MCP** | `BIGQUERY_PROJECT`, `BIGQUERY_KEY_FILE`（オプション） | BigQueryデータ分析 |
| **DBHub MCP** | `DSN`（または`DATABASE_DSN`） | データベース操作（MySQL/PostgreSQL等） |
| **AWS Docs MCP** | 不要 | AWS公式ドキュメント検索 |
| **Claude Code MCP** | 不要 | Claude Code機能拡張 |

**注意事項:**
- MCPを有効化すると、コンテキスト使用量が増加します（1MCPあたり約5k～30k tokens）
- 認証が必要なMCPは、対応する`.env`設定を忘れずに行ってください
- 使わないMCPは無効のままにしておくことを推奨します（パフォーマンス向上）

#### 現在有効なMCPをさらに無効化する

デフォルトで有効になっている5つのMCPのうち、使用しないものがあればさらに無効化できます。

**無効化の手順:**

1. **Claude Codeで`/mcp`コマンドを実行**

   チャット入力欄に以下を入力してEnter：
   ```
   /mcp
   ```

2. **MCP一覧から無効化したいMCPを選択**

   表示されるMCP一覧で：
   - 🟢 緑色のドット = 有効
   - ⚫ グレーのドット = 無効

   無効化したいMCP（例: `plugin:ndf:context7`）をクリックして選択します。

3. **Disable（無効化）を選択**

   選択したMCPの詳細画面で「Disable」ボタンをクリックします。

   または、一覧画面でMCP名の右側にあるトグルスイッチをクリックして無効化できます。

4. **Claude Codeを再起動**

   変更を反映するために、Claude Codeを終了して再起動します。

5. **無効化を確認**

   再度 `/mcp` コマンドを実行して、該当のMCPが⚫グレーになっていることを確認します。

**無効化の具体例:**

| MCP | 無効化を検討すべきケース |
|-----|---------------------|
| **Chrome DevTools** | Webスクレイピングやパフォーマンステストが不要な場合（約10k tokens削減） |
| **Codex CLI** | AIコードレビュー機能が不要な場合（約3k tokens削減） |

**補足:**
- MCPの有効化/無効化は各プロジェクトごとに設定されます
- 設定は`.claude/settings.json`または`.mcp.json`に保存されます
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
