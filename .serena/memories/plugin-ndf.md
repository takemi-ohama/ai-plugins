# NDF Plugin メモリー

## 概要

NDFプラグインは、3つの既存プラグインを統合したオールインワンプラグインです。

**統合元プラグイン:**
1. `mcp-integration` (v2.0.0) - MCP servers
2. `install-slack-hook` (v2.0.0) - Slack notifications
3. `workflow-commands` (v1.0.0) - Development workflow commands

**バージョン:** 1.0.6

**重要な変更 (v1.0.1):**
- MCP-integration、install-slack-hook、workflow-commandsの3プラグインを削除
- すべての機能をNDFプラグインに統合
- マーケットプレイスをNDF単一プラグインに整理
- MCPサーバー数を9→10に更新（Claude Code MCP追加）
- コマンド形式を`/ndf:pr`等、プレフィックス付きに統一

**重要な変更 (v1.0.6):**
- **directorサブエージェントを追加** - タスク統括と調整の専門エージェント
- Main Agentの責務をdirectorに移譲（調査、計画、取りまとめ）
- Main Agentは指示出しのみに徹し、複雑なタスクはdirectorに委譲
- 専門エージェント数: 5→6に更新

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
│   ├── director.md         # ディレクターエージェント（統括）
│   ├── data-analyst.md     # データアナリストエージェント
│   ├── corder.md           # コーディングエージェント
│   ├── researcher.md       # リサーチャーエージェント
│   ├── scanner.md          # スキャナーエージェント
│   └── qa.md               # 品質管理エージェント
├── CLAUDE.md                # メインエージェント向け指示（サブエージェント活用促進）
└── README.md                # 統合ドキュメント
```

## 機能

### 1. MCP統合 (10サーバー)

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
10. **claude-code** (stdio) - Claude Codeプラグイン開発支援

### 2. 開発ワークフローコマンド (6コマンド)

`plugin.json`の`commands`フィールドで定義：

- `/ndf:serena` - 開発記憶の記録
- `/ndf:pr` - PR作成
- `/ndf:fix` - PR修正対応
- `/ndf:review` - PRレビュー
- `/ndf:merge` - マージ後クリーンアップ
- `/ndf:clean` - ブランチクリーンアップ

### 3. 専門エージェント (6種類)

`plugin.json`の`agents`フィールドで定義：

**director** - タスク統括と調整（NEW v1.0.6）
- Serena MCP、GitHub MCP、基本ツールを活用
- タスク全体の理解と分解
- 情報収集と調査
- 計画立案と実行戦略
- 他のサブエージェントへの指示出し
- 結果の統合と取りまとめ
- ユーザーへの詳細報告
- **Main Agentが担っていた責務をすべて引き継ぎ、Main Agentは指示出しのみに徹する**

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

**qa** - 品質管理とテスト
- Codex MCP（コードレビュー、セキュリティチェック）、Serena MCP（コードベース分析）、Chrome DevTools MCP（パフォーマンステスト）、Claude Code MCP（プラグイン品質検証）を活用
- コード品質レビュー、セキュリティ脆弱性検出（OWASP Top 10対応）
- パフォーマンステスト（Core Web Vitals評価）、テストカバレッジ確認
- ドキュメント品質検証、Claude Codeプラグイン仕様準拠確認

### 4. 自動フック

`hooks/hooks.json`で定義された統合Stopフック：

**実装方式:** 1つのPrompt型フック

**Slack通知送信**
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

## Stop Hook実装の重要な知見

### Stop Hook無限ループ問題と解決策

**問題:**
Stop hookスクリプト内でClaude CLIを呼び出すと、サブプロセスが終了時に再度Stop hookをトリガーし、無限ループが発生。

**試行錯誤の履歴:**

1. **失敗: `CLAUDE_DISABLE_HOOKS`環境変数**
   ```bash
   export CLAUDE_DISABLE_HOOKS=1
   claude -p "prompt"
   ```
   → 動作せず。この環境変数は存在しない。

2. **失敗: `stop_hook_active`フィールドチェック**
   ```bash
   STOP_HOOK_ACTIVE=$(echo "$HOOK_INPUT" | grep -o '"stop_hook_active":[^,}]*')
   ```
   → ドキュメントには記載されているが、実際のhook入力には含まれない。

3. **成功: `--settings`フラグでhooksとplugins無効化**
   ```bash
   claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' --output-format text
   ```
   → 確実に無限ループを防止可能。

**最終推奨実装（Node.js）:**
```javascript
const { spawn } = require('child_process');

const claude = spawn('claude', [
  '-p',
  '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}',
  '--output-format', 'text'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});
```

**重要ポイント:**
- `--settings`フラグは`claude --help`で確認可能
- hooksだけでなくpluginsも無効化することが重要
- transcript処理フラグによるチェックも併用すると更に安全

### Slack通知の実装詳細

**要約生成の3段階フォールバック:**

1. **Claude CLI（優先）** - AIによる高品質な要約
   ```bash
   claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' \
     --output-format text <<EOF
   以下の会話から実施した作業を40文字以内で要約してください。
   ...
   EOF
   ```

2. **transcript解析（フォールバック1）** - セッションログから抽出
   ```javascript
   const transcript = fs.readFileSync(transcriptPath, 'utf-8');
   // 最終的なAssistantメッセージから要約を抽出
   ```

3. **git diff（フォールバック2）** - ファイル変更から推測
   ```bash
   git diff HEAD~1 --stat | head -1
   ```

**文字長制限:**
- 最終的に40文字に統一（試行錯誤の結果）
- プロンプトで明示的に指示：「40文字以内で要約してください」

**通知メカニズム:**
1. メンション付き投稿（`chat.postMessage` with mention） → 通知音
2. メッセージ削除（`chat.delete`） → 1秒後
3. メンションなし再投稿 → クリーンな履歴

**設定変更履歴:**
- v1.x: `SLACK_WEBHOOK_URL`方式
- v2.x: `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID` + `SLACK_USER_MENTION`方式

## 環境変数

`.env`ファイルで以下を設定：

**必須:**
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub MCP用

**オプション:**
- `NOTION_API_KEY` - Notion MCP用
- `GOOGLE_APPLICATION_CREDENTIALS` - BigQuery MCP用
- `DATABASE_DSN` - DBHub MCP用
- `SLACK_BOT_TOKEN` - Slack通知用（Bot User OAuth Token）
- `SLACK_CHANNEL_ID` - Slack通知送信先チャンネルID
- `SLACK_USER_MENTION` - Slackメンション対象ユーザーID（例: U123456789）
- `CONTEXT7_API_KEY` - Context7 MCP用

**非推奨（v1.x互換性のため残存）:**
- `SLACK_WEBHOOK_URL` - v2.xではBot Token方式を推奨

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

## プラグイン統合の完了 (v1.0.1)

**PR #37 (2025-11-15):**
- mcp-integration、install-slack-hook、workflow-commandsの3プラグインを削除
- すべての機能をNDFプラグインに統合完了
- マーケットプレイスはNDF単一プラグインに整理

**統合の利点:**
- **シンプルな導線**: ユーザーは1つのプラグインをインストールするだけ
- **バージョン管理の統一**: 個別プラグインの非同期更新問題を解消
- **設定の簡素化**: 単一の.mcp.json、単一のhooks設定
- **ドキュメント保守の容易さ**: 1つのREADME.mdに全情報を集約

**削除されたプラグイン:**
- `plugins/mcp-integration/` (17ファイル)
- `plugins/install-slack-hook/` (4ファイル)
- `plugins/workflow-commands/` (7ファイル)

**現在のマーケットプレイス構成:**
- NDFプラグインのみ（10 MCP servers、6 commands、5 agents、Slack notifications）

## トラブルシューティング

詳細は`plugins/ndf/README.md`を参照。

共通の問題：
1. MCPサーバー起動エラー → `.env`確認、Claude Code再起動
2. 認証エラー → トークン/認証情報の確認
3. コマンド表示されない → プラグインインストール確認
4. Slack通知が来ない → `SLACK_WEBHOOK_URL`確認

## メインエージェント向け指示

`CLAUDE.ndf.md`ファイルで、メインエージェント（親エージェント）に対して以下を指示：

**サブエージェント活用の基本方針:**
- **ほとんどの複雑なタスクはdirectorエージェントに最初に委譲する（推奨）**
- Directorがタスクの調査、計画、他のサブエージェントへの指示出しを担当
- Main Agentは最小限の調整のみに徹する
- 各サブエージェント（@director, @data-analyst, @corder, @researcher, @scanner, @qa）の役割を明確化

**主な指示内容:**
- タスク分類のフローチャート（directorを最優先）
- Directorエージェントの活用方法と責務
- 各専門サブエージェントを活用すべき場面
- 複数エージェントの連携パターン
- ベストプラクティス（DO/DON'T）
- Main AgentとDirector Agentの役割分担

## 今後の拡張

将来的に追加できる機能：
- より多くのMCPサーバー
- 追加の開発ワークフローコマンド
- カスタマイズ可能なフック設定
- 他の通知サービス統合（Discord、Teams等）
- 追加の専門エージェント
