# NDF Plugin

Claude Code開発環境を**オールインワン**で強化する統合プラグインです。

## 概要

このプラグイン1つで、以下の**すべて**の機能を利用できます：

1. **MCP統合**: 9つの強力なMCPサーバー（GitHub、Serena、BigQuery、Notion、DBHub、Chrome DevTools、AWS Docs、Codex CLI、Context7）
2. **開発ワークフロー**: PR作成、レビュー、マージ、ブランチクリーンアップコマンド
3. **専門エージェント**: 6つの特化型AIエージェント（データ分析、コーディング、調査、ファイル読み取り、Slack通知、作業記録）
4. **自動フック**: Serenaメモリー保存とSlack通知

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
# Incoming Webhook URL取得: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=

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

DBHub MCPは複数のデータベースに対応しています。データベースごとに接続文字列（DSN）の形式が異なります。

**PostgreSQL:**
```bash
DATABASE_DSN="postgres://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=disable"
```

例：
```bash
DATABASE_DSN="postgres://myuser:mypassword@localhost:5432/mydb?sslmode=disable"
```

**MySQL:**
```bash
DATABASE_DSN="mysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```

例：
```bash
DATABASE_DSN="mysql://root:password@localhost:3306/testdb"
```

**SQLite:**
```bash
DATABASE_DSN="sqlite:///PATH/TO/DATABASE.db"
```

例：
```bash
DATABASE_DSN="sqlite:///./data/local.db"
```

**SQL Server:**
```bash
DATABASE_DSN="sqlserver://USERNAME:PASSWORD@HOST:PORT?database=DATABASE"
```

**MariaDB:**
```bash
DATABASE_DSN="mysql://USERNAME:PASSWORD@HOST:PORT/DATABASE"
```
（MySQL と同じ形式）

**注意事項:**
- パスワードに特殊文字が含まれる場合は、URLエンコードが必要
- ローカルデータベースの場合は `localhost` を使用
- SSLが不要な場合は `?sslmode=disable` を追加（PostgreSQL）

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

### 1. MCP統合 (9サーバー)

#### GitHub MCP (Local)
- PR作成・レビュー・マージ
- イシュー管理
- コード検索
- ブランチ・タグ操作

#### Serena MCP (Local)
- セマンティックコード分析
- シンボルベース編集
- リファレンス検索
- コードメモリー管理

#### Notion MCP (HTTP)
- ページ検索・作成
- データベース操作
- コンテンツ更新

#### AWS Documentation MCP (Local)
- AWS公式ドキュメント検索
- コンテンツ読み込み
- 関連ページ推奨

#### BigQuery MCP (Local)
- SQLクエリ実行
- テーブル・データセット管理
- スキーマ操作

#### DBHub MCP (Local)
- PostgreSQL、MySQL、SQL Server、MariaDB、SQLite対応
- スキーマ探索
- SQL実行とトランザクションサポート

#### Chrome DevTools MCP (Local)
- ブラウザ自動化
- パフォーマンス分析
- ネットワーク監視
- デバッグ

#### Codex CLI MCP (Local)
- コード品質・アーキテクチャ分析
- セキュリティ脆弱性検出
- AIコードレビュー

#### Context7 MCP (HTTP)
- 最新のコード例とドキュメント取得
- フレームワーク・ライブラリの最新情報
- コミュニティのベストプラクティス参照

### 2. 開発ワークフローコマンド

#### `/serena`
Serena MCPを使った開発記憶の記録

**使用例:**
```
/serena
```

#### `/pr`
現在のブランチからPRを作成

**使用例:**
```
/pr
```

#### `/fix`
PR修正を効率化

**使用例:**
```
/fix
```

#### `/review`
指定されたPRをレビュー

**使用例:**
```
/review
/review 123
/review https://github.com/owner/repo/pull/456
```

#### `/merge`
PRマージ後のクリーンアップ

**使用例:**
```
/merge
```

#### `/clean`
マージ済みブランチをクリーンアップ

**使用例:**
```
/clean
```

### 3. 専門エージェント (6種類)

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

#### `slack-notifier` エージェント
**専門領域:** Slack通知の送信と作業要約生成

**機能:**
- Git変更内容の分析
- 40文字以内の簡潔な日本語要約作成
- `slack-notify.sh`スクリプトの実行
- エラーハンドリング

**使用場面:**
- Stopフックから自動的に呼び出される（手動呼び出しは不要）
- 作業セッション終了時にSlack通知を自動送信

**注意:**
- このエージェントは主にフック内で使用されるため、手動で呼び出す必要はありません
- SLACK_BOT_TOKENが設定されていない場合は自動的にスキップされます

#### `memory-recorder` エージェント
**専門領域:** Serenaメモリーへの作業記録保存

**使用MCPツール:**
- Serena MCP（メモリー管理）

**機能:**
- Git変更の分析と重要度判定
- 日次ファイル形式でのメモリー保存（`plugin-ndf-<YYYYMMDD>.md`）
- 同日の複数セッションの追記
- 最新2ファイルのみ保持（古いファイルの自動削除）
- 構造化された記録フォーマット

**使用場面:**
- Stopフックから自動的に呼び出される（手動呼び出しは不要）
- 作業セッション終了時に自動記録

**記録される情報:**
- 変更ファイル一覧
- Git統計（diff --stat）
- 最近のコミット履歴
- 作業サマリー
- タイムスタンプ

**注意:**
- このエージェントは主にフック内で使用されるため、手動で呼び出す必要はありません
- 重要でない変更の場合は自動的にスキップされます

### 4. 自動フック

Claude Code終了時に自動実行される統合フック：

**実装方式:** 1つのPrompt型フック（順次実行を保証）

Claude Codeのフックは並列実行されるため、処理順序を保証するために1つのpromptで2つのタスクを順次実行します。

**動作確認:**
- フック実行開始時に「## Stop処理を開始します」というメッセージが表示されます
- これにより、自動処理が開始されたことを確認できます

#### タスク1: Serenaメモリー自動保存

`@memory-recorder`エージェントを使用して、重要な変更があった場合にSerena MCPメモリーに作業記録を保存します。

**保存対象:**
- プラグイン関連ファイル (`plugins/`, `.claude-plugin/`)
- 設定ファイル (`.mcp.json`, `plugin.json`)
- ドキュメント (`README.md`, `CLAUDE.md`)
- パッケージ設定 (`package.json`)

**memory-recorderエージェントの処理:**
1. Git変更を確認（`git status`, `git diff`）
2. 重要なファイルパターンに変更があるか判定
3. 重要な変更がある場合のみメモリーを作成/追記
4. 古いメモリーファイルを自動削除（最新2ファイルのみ保持）
5. 変更がない、または重要でない場合は自動スキップ

**保存内容:**
- 変更されたファイル一覧
- Git diff統計
- 最近のコミット履歴
- 作業セッションのサマリー
- タイムスタンプ

**メモリー保存方式:**
- **ファイル名形式**: `plugin-ndf-<YYYYMMDD>.md`（日次ファイル）
  - 例: `plugin-ndf-20250115.md`
- **同日の複数セッション**: 同一ファイルに追記
- **ファイル保持**: 最新2ファイルのみ保持（古いファイルは自動削除）
  - 例: 2025-01-15と2025-01-14を保持し、2025-01-13以前を削除

**メモリー保存先:**
`.serena/memories/plugin-ndf-<YYYYMMDD>.md`

#### タスク2: Slack通知送信

`@slack-notifier`エージェントを使用してSlack通知を送信します（SLACK_BOT_TOKENが設定されている場合のみ）。

**処理フロー:**
1. `@slack-notifier`エージェントを起動
2. エージェントがGit diffと会話履歴から作業内容を分析
3. 40文字以内の簡潔な日本語要約を作成
4. `slack-notify.sh`スクリプトを実行し、要約を引数として渡す

**要約例:**
- 「NDFプラグインにContext7追加」
- 「4つの専門エージェント実装」
- 「詳細な設定ガイド追加」

**通知内容:**
- AI生成の40文字要約
- リポジトリ名
- タイムスタンプ

**通知メカニズム:**
1. Slackにメンション付きで投稿（通知音が鳴る）
2. メッセージを即座に削除
3. メンションなしで詳細メッセージを再投稿（クリーンな履歴）

**設定方法:**
1. Slack Appを作成（Bot Token Scopesが必要）
2. `.env`に以下を設定:
   - `SLACK_BOT_TOKEN`
   - `SLACK_CHANNEL_ID`
   - `SLACK_USER_MENTION`（オプション）
3. Claude Codeを再起動

詳細は [SLACK_BOT_TOKENとSLACK_CHANNEL_IDの設定方法](#各認証情報の詳細設定) を参照。

**設定:** プラグインインストール後、自動的に有効になります

**注意:**
- フックはClaude Code再起動後に有効化されます
- `/plugin update ndf`でプラグインを更新した場合も再起動が必要です

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

## トラブルシューティング

### MCPサーバーが起動しない

1. `.env` ファイルがプロジェクトルートに存在するか確認
2. 環境変数が正しく設定されているか確認
3. Claude Codeを完全に再起動
4. ログを確認（Claude Codeの設定から）

### 認証エラー

**GitHub:**
- トークンが有効か確認
- 必要なスコープ（`repo`、`read:org`等）があるか確認

**Notion:**
- 統合トークンが正しいか確認
- 統合がページ/データベースに接続されているか確認

**BigQuery:**
- サービスアカウントキーのパスが正しいか確認
- プロジェクトでBigQuery APIが有効か確認

**DBHub:**
- データベース接続文字列（DSN）が正しいか確認
- データベースサーバーが起動しているか確認

**Codex CLI:**
- Codex CLIがインストールされているか確認（`codex --version`）
- 認証済みか確認（`codex login`）

### Slack通知が送信されない

1. `SLACK_WEBHOOK_URL`が正しく設定されているか確認
2. Webhook URLが有効か確認（curl等でテスト）
3. Claude Codeのログでエラーを確認

### コマンドが表示されない

1. Claude Codeを再起動
2. プラグインが正しくインストールされているか確認: `/plugin list`
3. コマンドファイルが正しく配置されているか確認

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
