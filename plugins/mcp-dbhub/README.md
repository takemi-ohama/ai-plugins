# DBHub MCP

データベース操作とSQLクエリを実行するためのMCPサーバープラグインです。

## 概要

このプラグインは、MySQL、PostgreSQL、SQLiteなどの各種データベースへのアクセスを提供します。

## 機能

- データベース接続管理
- SQLクエリの実行
- テーブルスキーマの取得
- データベース一覧の取得
- トランザクション管理

## インストール

```bash
/plugin install mcp-dbhub@ai-plugins
```

## 使用方法

### 基本的な使用例

```bash
# データベースに接続（環境変数から読み込み推奨）
mcp__plugin_dbhub-mcp__dbhub__connect "${DATABASE_URL}"

# SQLクエリを実行
mcp__plugin_dbhub-mcp__dbhub__execute_query "SELECT * FROM users LIMIT 10"
```

## 推奨される使用シーン

- ローカルデータベースの操作
- データ分析
- スキーマ確認
- データマイグレーション

## ndf:data-analystエージェントとの連携

DBHub MCPは、NDFプラグインの`ndf:data-analyst`エージェントと連携して使用することを推奨します。

```bash
# data-analystエージェントにデータベースクエリを依頼
Task(
  subagent_type="ndf:data-analyst",
  prompt="Analyze user activity in the local database",
  description="Analyze user activity"
)
```

## 注意事項

- デフォルトではHTTPトランスポートでポート8080を使用します
- データベース接続情報は環境変数または`.env`ファイルで管理してください

## 参考リンク

- [@bytebase/dbhub](https://www.npmjs.com/package/@bytebase/dbhub)
- [Bytebase](https://www.bytebase.com/)
