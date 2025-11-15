# NDF Plugin メモリー

## 概要

NDFプラグインは、3つの既存プラグインを統合したオールインワンプラグインです。

**統合元プラグイン:**
1. `mcp-integration` (v2.0.0) - MCP servers
2. `install-slack-hook` (v2.0.0) - Slack notifications
3. `workflow-commands` (v1.0.0) - Development workflow commands

**バージョン:** 1.0.0

## ディレクトリ構造

```
plugins/ndf/
├── .claude-plugin/
│   └── plugin.json          # プラグインメタデータ（commands、agents含む）
├── .mcp.json                # 9つのMCPサーバー定義
├── hooks/
│   └── hooks.json           # Serenaメモリー保存＋Slack通知フック
├── scripts/
│   └── slack-notify.sh      # Slack通知スクリプト
├── commands/
│   ├── serena.md           # /serena コマンド
│   ├── pr.md               # /pr コマンド
│   ├── fix.md              # /fix コマンド
│   ├── review.md           # /review コマンド
│   ├── merge.md            # /merge コマンド
│   └── clean.md            # /clean コマンド
├── agents/
│   ├── data-analyst.md     # データアナリストエージェント
│   ├── corder.md           # コーディングエージェント
│   ├── researcher.md       # リサーチャーエージェント
│   └── scanner.md          # スキャナーエージェント
├── CLAUDE.md                # メインエージェント向け指示（サブエージェント活用促進）
└── README.md                # 統合ドキュメント
```

## 機能

### 1. MCP統合 (9サーバー)

`.mcp.json`で定義されたMCPサーバー：

1. **github** (HTTP) - GitHub API統合
2. **notion** (HTTP) - Notion統合
3. **serena** (stdio) - セマンティックコード分析
4. **awslabs.aws-documentation-mcp-server** (stdio) - AWS公式ドキュメント
5. **mcp-server-bigquery** (stdio) - BigQuery統合
6. **dbhub** (stdio) - ユニバーサルデータベースゲートウェイ
7. **chrome-devtools-mcp** (stdio) - Chromeブラウザ自動化
8. **codex** (stdio) - AIコードレビュー
9. **context7** (HTTP) - 最新のコード例とドキュメント取得

### 2. 開発ワークフローコマンド (6コマンド)

`plugin.json`の`commands`フィールドで定義：

- `/serena` - 開発記憶の記録
- `/pr` - PR作成
- `/fix` - PR修正対応
- `/review` - PRレビュー
- `/merge` - マージ後クリーンアップ
- `/clean` - ブランチクリーンアップ

### 3. 専門エージェント (4種類)

`plugin.json`の`agents`フィールドで定義：

**data-analyst** - データ分析とSQL操作
- BigQuery MCP、DBHub MCPを活用
- SQL生成、実行、結果解釈
- データ出力（CSV/JSON/Excel）

**corder** - 高品質コード生成
- Codex MCP（コードレビュー）、Serena MCP（コード理解）、Context7 MCP（最新情報）を活用
- クリーンなコード作成
- セキュリティチェック、リファクタリング提案

**researcher** - 情報収集と分析
- Codex MCP、AWS Docs MCP、Chrome DevTools MCPを活用
- 技術ドキュメント調査、Webスクレイピング
- コードベース分析、調査結果レポート

**scanner** - ファイル読み取り
- Codex MCPを活用
- PDF、画像、PowerPoint、Excelファイルの読み取り
- OCR、データ抽出、構造化

### 4. 自動フック

`hooks/hooks.json`で定義された統合Stopフック：

**実装方式:** 1つのPrompt型フック（順次実行を保証）

重要: Claude Codeのフックは並列実行されるため、処理順序を保証するために1つのpromptで2つのタスクを順次実行する設計。

**タスク1: Serenaメモリー自動保存**
- AIがgit変更を確認し、重要なファイルパターンを判定
- 重要な変更がある場合に作業セッション記録を`.serena/memories/`に保存

保存対象パターン：
- `plugins/`, `.claude-plugin/`, `.mcp.json`
- `CLAUDE.md`, `README.md`, `plugin.json`, `package.json`

保存内容：
- 変更ファイル一覧、Git diff統計、最近のコミット
- 作業セッションのサマリー、タイムスタンプ

メモリー名: `work-session-YYYYMMDD-HHMMSS.md`

**タスク2: Slack通知送信**
- AIが作業内容を40文字以内の日本語で要約
- Bashツールで`scripts/slack-notify.sh complete "<要約>"`を実行
- SLACK_BOT_TOKENが設定されている場合のみ実行

通知内容：
- AI生成40文字要約
- リポジトリ名
- タイムスタンプ

通知メカニズム：
1. メンション付き投稿（通知音）
2. メッセージ削除
3. メンションなし再投稿（クリーンな履歴）

## 環境変数

`.env`ファイルで以下を設定：

**必須:**
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub MCP用

**オプション:**
- `NOTION_API_KEY` - Notion MCP用
- `GOOGLE_APPLICATION_CREDENTIALS` - BigQuery MCP用
- `DATABASE_DSN` - DBHub MCP用
- `SLACK_WEBHOOK_URL` - Slack通知用
- `CONTEXT7_API_KEY` - Context7 MCP用

**認証不要:**
- Serena MCP
- AWS Documentation MCP
- Chrome DevTools MCP
- Codex CLI MCP（別途`codex login`必要）

## インストール方法

```bash
# Claude Codeで実行
/plugin marketplace add https://github.com/takemi-ohama/ai-agent-marketplace
/plugin install ndf@ai-agent-marketplace
```

その後、`.env`ファイルを作成してClaude Codeを再起動。

## 設計の利点

1. **シンプル**: 1つのプラグインで全機能を提供
2. **一貫性**: 統合された環境変数管理
3. **メンテナンス性**: 重複コードなし
4. **ユーザビリティ**: インストール・管理が容易

## 既存プラグインとの関係

NDFプラグインは、以下の3プラグインの機能をすべて含みます：

- `mcp-integration` - `.mcp.json`を統合
- `install-slack-hook` - `hooks/`と`scripts/`を統合
- `workflow-commands` - `commands/`を統合

既存プラグインは引き続き個別に利用可能ですが、オールインワン体験を望むユーザーはNDFプラグインを選択できます。

## トラブルシューティング

詳細は`plugins/ndf/README.md`を参照。

共通の問題：
1. MCPサーバー起動エラー → `.env`確認、Claude Code再起動
2. 認証エラー → トークン/認証情報の確認
3. コマンド表示されない → プラグインインストール確認
4. Slack通知が来ない → `SLACK_WEBHOOK_URL`確認

## メインエージェント向け指示

`CLAUDE.md`ファイルで、メインエージェント（親エージェント）に対して以下を指示：

**サブエージェント活用の基本方針:**
- 複雑なタスクや専門性の高いタスクは、適切なサブエージェントに委譲
- メインエージェントは全体の調整役、タスク分類、結果統合を担当
- 各サブエージェント（@data-analyst, @corder, @researcher, @scanner）の役割を明確化

**主な指示内容:**
- タスク分類のフローチャート
- 各サブエージェントを活用すべき場面とNGパターン
- 複数エージェントの連携パターン
- ベストプラクティス（DO/DON'T）

## 今後の拡張

将来的に追加できる機能：
- より多くのMCPサーバー
- 追加の開発ワークフローコマンド
- カスタマイズ可能なフック設定
- 他の通知サービス統合（Discord、Teams等）
- 追加の専門エージェント
