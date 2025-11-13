# MCP Integration Plugin

Claude CodeプロジェクトでMCP（Model Context Protocol）サーバーを**自動的に**セットアップし、開発ワークフローを効率化するためのプラグインです。

## 概要

このプラグインは、プロジェクトスキルとして動作し、**「MCPサーバーをセットアップして」と言うだけで**、複数の強力なMCPサーバーを一括でセットアップします。手動での`.mcp.json`作成は不要です。

さらに、**6つの開発ワークフローコマンド**（`/pr`, `/fix`, `/review`, `/merge`, `/clean`, `/serena`）が含まれており、GitHub開発フローを効率化します。

**スマートマージ機能搭載**: 既に`.mcp.json`や`.env`が存在する場合でも安心。既存の設定やトークンは保持したまま、不足している設定だけを追加します。

**提供されるMCPサーバー：**

- **GitHub MCP**: リポジトリ管理、PR/イシュー操作、コード検索
- **Serena MCP**: セマンティックコード分析、シンボルベース編集
- **Notion MCP**: ドキュメント管理、データベース操作
- **AWS Documentation MCP**: AWS公式ドキュメントへのアクセス
- **BigQuery MCP**: データベースクエリとスキーマ管理
- **DBHub MCP**: ユニバーサルデータベースゲートウェイ（PostgreSQL、MySQL...）
- **Chrome DevTools MCP**: Chromeブラウザの自動化・デバッグ・パフォーマンス分析

## インストール

### 前提条件

- Claude Code がインストール済み
- Python 3.10以上（Serena、BigQuery MCP用）
- `uvx` がインストール済み（`pip install uv`）
- Node.js（DBHub、Chrome DevTools MCP用）

### ステップ1: プラグインのインストール

```bash
# Claude Codeで実行
/plugin install mcp-integration@ai-agent-marketplace
```

### ステップ2: スキルを起動してセットアップ

プラグインをインストールしたら、スキルを起動して自動セットアップを実行します。

```
@mcp-integration MCPをセットアップして
```

スキルが自動的に：
1. `.mcp.json` ファイルを作成または更新（`envFile`設定済み）
   - 新規作成：すべてのMCPサーバー設定を追加
   - 既存の場合：不足しているMCPサーバーのみを追加（既存設定は保持）
2. `.env` テンプレートファイルを作成または更新（変数名のみ、値は空）
   - 新規作成：すべての環境変数を追加
   - 既存の場合：不足している変数のみを追加（既存の値は保持）
3. `.env` を `.gitignore` に追加（まだの場合）
4. 前提条件（Python、uvx）の確認
5. 次のステップの案内

**スマートマージ機能:**
- ✅ 既存の設定やトークンは上書きされません
- ✅ 不足している設定だけを追加します
- ✅ カスタムMCPサーバーや環境変数も保持されます

### ステップ3: 必要なツールのインストール（まだの場合）

スキルが確認しますが、手動でもインストール可能：

```bash
# uvx（Serena、BigQuery用）
pip install uv

# 確認
uvx --version
```

### ステップ4: .envファイルに値を入力

スキルが作成した `.env` テンプレートファイルを開き、必要な値を入力します。

#### 作成された.envファイル

スキルが以下の内容で `.env` ファイルを作成済みです：

```bash
# GitHub MCP (Required - basic functionality)
# Get token from: https://github.com/settings/tokens
# Required scopes: repo, read:org, workflow
GITHUB_PERSONAL_ACCESS_TOKEN=

# Notion MCP (Optional - only if using Notion)
# Get token from: https://www.notion.so/my-integrations
NOTION_API_KEY=

# BigQuery MCP (Optional - only if using BigQuery)
# Create service account at: https://console.cloud.google.com/iam-admin/serviceaccounts
# Required roles: BigQuery Data Editor, BigQuery Job User
GOOGLE_APPLICATION_CREDENTIALS=

# DBHub MCP (Optional - only if using database operations)
# Database connection string (DSN) - examples:
# PostgreSQL: postgres://user:password@localhost:5432/dbname?sslmode=disable
# MySQL: mysql://user:password@localhost:3306/dbname
# SQLite: sqlite:///path/to/database.db
DATABASE_DSN=

# Note: Serena MCP, AWS Documentation MCP, and Chrome DevTools MCP do not require authentication
```

このファイルの `=` の後に、取得したトークンや認証情報を入力してください。

#### 各トークンの取得方法

**GitHub Personal Access Token（必須）:**
1. https://github.com/settings/tokens にアクセス
2. "Generate new token (classic)" をクリック
3. 以下のスコープを選択:
   - `repo`: リポジトリへのフルアクセス
   - `read:org`: 組織情報の読み取り
   - `workflow`: GitHub Actions ワークフロー更新
4. トークンをコピーして `.env` ファイルに貼り付け

**Notion API Key（オプション）:**
1. https://www.notion.so/my-integrations にアクセス
2. "New integration" をクリック
3. 統合を作成してトークンをコピー
4. Notionでページ/データベースに統合を接続
5. トークンを `.env` ファイルに貼り付け

**BigQuery認証情報（オプション）:**
1. https://console.cloud.google.com/iam-admin/serviceaccounts にアクセス
2. サービスアカウントを作成
3. 以下のロールを付与:
   - `BigQuery Data Editor`
   - `BigQuery Job User`
4. JSONキーをダウンロード
5. キーファイルのパスを `.env` ファイルに記載

**DBHub認証情報（オプション）:**
1. 使用するデータベースの接続情報を取得
2. データベース接続文字列（DSN）を作成：
   - PostgreSQL: `postgres://user:password@localhost:5432/dbname?sslmode=disable`
   - MySQL: `mysql://user:password@localhost:3306/dbname`
   - SQLite: `sqlite:///path/to/database.db`
3. DSNを `.env` ファイルに記載

#### 入力例

値を入力した後の `.env` ファイルの例：

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_abc123xyz789def456...
NOTION_API_KEY=secret_abc123xyz789...
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourname/Downloads/my-project-key.json
DATABASE_DSN=postgres://myuser:mypassword@localhost:5432/mydb?sslmode=disable
```

#### セキュリティ確認

✅ **スキルが自動的に実施済み:**
- `.env` を `.gitignore` に追加済み（機密情報のコミット防止）

この設定により、`.env` ファイルは誤ってGitにコミットされません。

### ステップ5: Claude Codeを再起動

`.env` ファイルに値を入力したら、Claude Codeを再起動してMCPサーバーをロードします。

### ステップ6: 動作確認

以下を確認してください：

1. **MCPツールの確認**
   - Claude Codeで以下のツールプレフィックスが利用可能か確認:
     - `mcp__github__*`
     - `mcp__serena__*`
     - `mcp__notion__*` (Notion設定時)
     - `mcp__awslabs_aws-documentation-mcp-server__*`
     - `mcp__mcp-server-bigquery__*` (BigQuery設定時)
     - `mcp__dbhub__*` (DBHub設定時)
     - `mcp__chrome-devtools-mcp__*` (Chrome DevTools設定時)

2. **Serena MCPの初期化（初回のみ）**
   ```
   Serenaプロジェクトをアクティベートして
   ```
   または:
   ```
   mcp__serena__activate_project(".")
   ```

これでセットアップ完了です！

## 特徴

- ✅ **自動セットアップ**: スキルが`.mcp.json`と`.env`テンプレートを自動作成
- ✅ **スマートマージ**: 既存の設定がある場合、不足分のみを追加（上書きなし）
- ✅ **セキュリティ保護**: `.env`を自動的に`.gitignore`に追加
- ✅ **対話的な案内**: 環境変数の設定を分かりやすく説明
- ✅ **前提条件の確認**: Python、uvxの有無を自動チェック
- ✅ **カスタマイズ可能**: 不要なMCPサーバーを無効化可能
- ✅ **詳細ドキュメント**: 各MCPの使い方と認証方法を完備
- ✅ **開発ワークフローコマンド**: 6つのスラッシュコマンドでPR作成・レビュー・マージを効率化

## 含まれるMCPサーバー

### 1. GitHub MCP (HTTP)
GitHub APIを通じてリポジトリ操作を実行します。

**主な機能:**
- PR作成・レビュー・マージ
- イシュー管理（作成、更新、検索）
- コード検索
- ブランチ・タグ操作
- リリース管理

**認証:** GitHub Personal Access Token

**公式ドキュメント:** https://github.com/github/github-mcp-server

### 2. Notion MCP (HTTP)
Notionワークスペースとの統合。

**主な機能:**
- ページ検索
- ページ・ブロック作成
- データベース操作
- コンテンツ更新

**認証:** Notion統合トークン

**公式ドキュメント:** https://mcp.notion.com

### 3. Serena MCP (Local)
ローカルコードベースのセマンティック理解と編集。

**主な機能:**
- シンボル検索（クラス、関数、変数等）
- リファレンス検索
- シンボルベース編集（安全なリファクタリング）
- コードメモリー管理
- パターン検索

**認証:** 不要（ローカル実行）

**公式ドキュメント:** https://github.com/oraios/serena

### 4. AWS Documentation MCP (Local)
AWS公式ドキュメントへの高速アクセス。

**主な機能:**
- ドキュメント検索
- コンテンツ読み込み
- 関連ページ推奨

**認証:** 不要（公開ドキュメント）

**公式ドキュメント:** https://github.com/awslabs/aws-documentation-mcp-server

### 5. BigQuery MCP (Local)
Google BigQueryとの統合。

**主な機能:**
- SQLクエリ実行
- テーブル・データセット管理
- スキーマ操作

**認証:** Google Cloud認証情報

**公式ドキュメント:** https://github.com/ergut/mcp-server-bigquery

### 6. DBHub MCP (Local)
ユニバーサルデータベースゲートウェイ。複数のデータベースシステムに対応。

**主な機能:**
- スキーマ探索（テーブル、インデックス、プロシージャ等）
- SQL実行とトランザクションサポート
- AI支援SQL生成
- データベース説明

**対応データベース:**
- PostgreSQL
- MySQL
- SQL Server
- MariaDB
- SQLite

**認証:** データベース接続文字列（DSN）

**公式ドキュメント:** https://github.com/bytebase/dbhub

### 7. Chrome DevTools MCP (Local)
ChromeブラウザをAIエージェントが制御・検査。

**主な機能:**
- 入力自動化（クリック、フォーム入力、ドラッグ等）
- ナビゲーション（ページ管理、遷移）
- エミュレーション（デバイス、ビューポート）
- パフォーマンス分析とトレーシング
- ネットワーク監視
- デバッグ（スクリプト実行、コンソールログ、スクリーンショット）

**認証:** 不要（ローカル実行）

**公式ドキュメント:** https://github.com/ChromeDevTools/chrome-devtools-mcp

## 利用方法

セットアップが完了したら（[インストール手順](#インストール)を参照）、以下のようにMCPサーバーを利用できます。

### 基本的な使い方

1. **Claude Codeで自然言語でリクエスト**
   ```
   このリポジトリのオープンなPRを確認して
   ```

2. **MCPツールが自動的に利用される**
   - Claude Codeが適切なMCPツールを選択
   - GitHub MCP、Serena MCP等が裏側で動作

### 手動でMCPツールを呼び出す

特定のMCPツールを直接呼び出すこともできます（[使用例](#使用例)を参照）。

## スラッシュコマンド

このプラグインには、開発ワークフローを効率化するための6つのスラッシュコマンドが含まれています：

### /serena - 開発の記憶と知見の記録

開発の履歴や得られた知見をSerena MCPに記録します。特にAI Agentの操作失敗や指示の誤解を記録することで、再発を防止します。

**実行内容：**
1. AI Agentの履歴から操作内容を収集
2. git logやファイル変更内容から知見を収集
3. Serena MCPに知見を記憶
4. 既存の記憶を確認・更新

### /pr - PR作成

現在の変更をコミット、プッシュし、GitHub上でPull Requestを作成します。ブランチ管理も自動化されています。

**実行内容：**
- 既存PRの確認
- ブランチの確認・切り替え
- 変更のコミット（日本語メッセージ）
- リモートへプッシュ
- PR作成（日本語、Summary + Test plan）

**注意：** デフォルトブランチ（main、master等）での直接コミットは禁止です。

### /fix - PR修正対応

直前のPRに対するレビューコメントを確認し、指摘事項に対応します。修正後は自動的にコミット・プッシュを行います。

**実行内容：**
1. レビューコメント確認
2. 問題点修正
3. コミット・プッシュ
4. Copilotにレビュー再依頼

**方針：** 指摘がすべて正しいとは限りません。修正前に仕様を調査し、実施の可否を判断します。

### /review - PRレビュー

直前のPRを専門家の観点からレビューし、問題点・改善点を指摘します。

**レビュー観点：**
- コード品質
- セキュリティ
- 可読性
- 保守性
- テストカバレッジ

**結果：** 問題があれば「Request Changes」、なければ「Approve」

### /merge - マージ後クリーンアップ

PRマージ後のクリーンアップを実行します。メインブランチを更新し、マージされたフィーチャーブランチを削除します。

**実行手順：**
1. PRがmainにマージ済みか確認
2. 変更があればstash
3. mainブランチに切り替えて更新
4. フィーチャーブランチをローカル・リモートから削除
5. stashを復元

### /clean - ブランチクリーンアップ

mainにマージ済みのブランチをローカルおよびリモートから削除します。

**実行内容：**
1. `git branch --merged main` で確認
2. main・現在ブランチを除外
3. マージ済みブランチを削除（ローカル・リモート）

**注意：** 削除前に確認を行います。

## 使用例

### GitHub MCP

```python
# オープンなPRをリスト
mcp__github__list_pull_requests(
    owner="username",
    repo="repository",
    state="open"
)

# イシューを作成
mcp__github__issue_write(
    method="create",
    owner="username",
    repo="repository",
    title="新機能リクエスト",
    body="説明をここに記載"
)

# コード検索
mcp__github__search_code(
    query="function calculateScore language:python"
)
```

### Serena MCP

```python
# プロジェクト概要を取得
mcp__serena__get_symbols_overview(
    relative_path="src/main.py"
)

# シンボルを検索
mcp__serena__find_symbol(
    name_path="MyClass/my_method",
    relative_path="src/main.py",
    include_body=True
)

# シンボル本体を置き換え
mcp__serena__replace_symbol_body(
    name_path="MyClass/my_method",
    relative_path="src/main.py",
    body="def my_method(self):\n    return 'new implementation'"
)

# リファレンスを検索
mcp__serena__find_referencing_symbols(
    name_path="my_function",
    relative_path="src/utils.py"
)
```

### Notion MCP

```python
# ページを検索
mcp__notion__search_pages(
    query="プロジェクト仕様"
)

# ページを作成
mcp__notion__create_page(
    parent_id="database_id",
    title="新しいタスク",
    properties={...}
)
```

### BigQuery MCP

```python
# クエリを実行
mcp__mcp-server-bigquery__query(
    sql="SELECT * FROM `project.dataset.table` LIMIT 10"
)

# テーブル情報を取得
mcp__mcp-server-bigquery__get_table(
    project_id="my-project",
    dataset_id="my-dataset",
    table_id="my-table"
)
```

### AWS Documentation MCP

```python
# ドキュメントを検索
mcp__awslabs_aws-documentation-mcp-server__search_documentation(
    search_phrase="S3 bucket policy"
)

# ドキュメントを読む
mcp__awslabs_aws-documentation-mcp-server__read_documentation(
    url="https://docs.aws.amazon.com/..."
)
```

### DBHub MCP

```python
# スキーマを探索
mcp__dbhub__get_schemas()

# テーブル一覧を取得
mcp__dbhub__get_tables(schema="public")

# SQLクエリを実行
mcp__dbhub__execute_query(
    query="SELECT * FROM users WHERE id = 1"
)

# AI支援SQL生成
mcp__dbhub__generate_sql(
    prompt="最近1週間のアクティブユーザーを取得"
)
```

### Chrome DevTools MCP

```python
# 新しいページを開く
mcp__chrome-devtools-mcp__navigate_page(
    url="https://example.com"
)

# 要素をクリック
mcp__chrome-devtools-mcp__click(
    selector="#submit-button"
)

# フォームに入力
mcp__chrome-devtools-mcp__fill_form(
    selector="#search-input",
    value="検索キーワード"
)

# スクリーンショットを撮る
mcp__chrome-devtools-mcp__take_screenshot()

# パフォーマンス分析を開始
mcp__chrome-devtools-mcp__performance_start_trace()

# パフォーマンス分析を停止して結果取得
mcp__chrome-devtools-mcp__performance_stop_trace()
```

## トラブルシューティング

### MCPサーバーが起動しない

1. `.mcp.json` のJSON構文を確認
2. 環境変数が正しく設定されているか確認: `echo $GITHUB_PERSONAL_ACCESS_TOKEN`
3. Claude Codeを完全に再起動
4. ログを確認（Claude Codeの設定から）

### 認証エラー

**GitHub:**
- トークンが有効か確認
- 必要なスコープ（`repo`、`read:org`等）があるか確認
- トークンが`ghp_`で始まるか確認

**Notion:**
- 統合トークンが正しいか確認
- 統合がページ/データベースに接続されているか確認

**BigQuery:**
- サービスアカウントキーのパスが正しいか確認
- サービスアカウントに必要なロールがあるか確認
- プロジェクトでBigQuery APIが有効か確認

**DBHub:**
- データベース接続文字列（DSN）が正しいか確認
- データベースサーバーが起動しているか確認
- ユーザー名とパスワードが正しいか確認
- ネットワーク接続を確認（ファイアウォール等）

**Chrome DevTools:**
- Chromeブラウザがインストールされているか確認
- Node.jsがインストールされているか確認
- ヘッドレスモードで問題がある場合は通常モードを試す

### Serena MCPが動作しない

```bash
# Python バージョンを確認
python --version  # 3.10以上である必要あり

# uvx を確認
uvx --version

# uvx を再インストール
pip install --upgrade uv
```

### ツールが表示されない

1. Claude Codeを再起動
2. `.mcp.json` がプロジェクトルートにあるか確認
3. JSONファイルの構文エラーがないか確認
4. MCP設定が正しくロードされているか、Claude Codeのログで確認

## セキュリティのベストプラクティス

- ✅ 環境変数でトークンを管理
- ✅ `.env` ファイルを `.gitignore` に追加
- ✅ 最小限のスコープ/権限を使用
- ✅ トークンを定期的にローテーション
- ❌ トークンをコードやドキュメントにコミットしない
- ❌ 本物に見えるトークン例を使用しない

## 詳細ドキュメント

- [SKILL.md](./skills/mcp-integration/SKILL.md) - スキル概要
- [mcp-setup-guide.md](./skills/mcp-integration/mcp-setup-guide.md) - 詳細セットアップ手順
- [mcp-config-template.md](./skills/mcp-integration/mcp-config-template.md) - 完全な `.mcp.json` テンプレート
- [mcp-authentication-guide.md](./skills/mcp-integration/mcp-authentication-guide.md) - 認証情報取得ガイド

## サポート

問題が発生した場合：
1. 上記のトラブルシューティングセクションを確認
2. 各MCPサーバーの公式ドキュメントを参照
3. GitHubリポジトリでイシューを作成

## ライセンス

MIT License

## 作者

takemi-ohama - https://github.com/takemi-ohama

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずイシューを開いて変更内容を議論してください。
