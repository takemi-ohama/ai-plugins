# AI Agent Marketplace

Claude Codeプラグイン、プロジェクトスキル、MCP（Model Context Protocol）設定を共有するための内部マーケットプレイスです。

## 概要

このマーケットプレイスは、チーム全体でClaude Codeの導入を加速するための事前設定されたプラグインを提供します：

- **MCPインテグレーションスキル**: GitHub、Serena、BigQuery、Notion MCPの自動セットアップ
- **カスタムコマンド**: 共通タスク用の再利用可能なスラッシュコマンド
- **サブエージェント**: 異なるドメイン向けの専門AIエージェント
- **フック**: イベントによってトリガーされる自動ワークフロー

## 利用可能なプラグイン

### MCP Integration (`mcp-integration`)

Claude CodeプロジェクトでMCPサーバーをセットアップするためのプロジェクトスキル。

**機能:**
- 5つのMCPサーバーを含む完全な `.mcp.json` テンプレート
- 認証セットアップガイド
- 使用例とベストプラクティス
- トラブルシューティングドキュメント

**含まれるMCP:**
1. **GitHub MCP**: リポジトリ操作、PR管理、イシュートラッキング
2. **Notion MCP**: ドキュメント管理、データベース操作
3. **Serena MCP**: セマンティックコード理解と編集
4. **AWS Documentation MCP**: AWSサービスドキュメントアクセス
5. **BigQuery MCP**: データベースクエリとスキーマ管理

**ドキュメント:**
- [SKILL.md](./plugins/mcp-integration/skills/mcp-integration/SKILL.md) - 概要
- [セットアップガイド](./plugins/mcp-integration/skills/mcp-integration/mcp-setup-guide.md) - インストール手順
- [設定テンプレート](./plugins/mcp-integration/skills/mcp-integration/mcp-config-template.md) - `.mcp.json` テンプレート
- [認証ガイド](./plugins/mcp-integration/skills/mcp-integration/mcp-authentication-guide.md) - トークンセットアップ

### Slack Notification (`slack-notification`)

Claude Codeの作業完了時に自動的にSlack通知を送信するプラグイン。

**機能:**
- 🔔 **スマート通知**: メンション付き投稿→削除→メンションなし再投稿で通知音を鳴らしながらチャンネルをクリーンに保つ
- 📝 **日本語要約**: git変更から日本語で作業要約を自動生成
- 🏷️ **リポジトリコンテキスト**: 通知にリポジトリ名を含める
- ⚙️ **ポータブル設定**: プロジェクト内のどのサブディレクトリからでも動作

**通知メッセージ例:**
```
[carmo-ai] Claude Codeの作業が完了しました (2025-11-12 00:17:58)
作業内容: slack-notify.shを更新
```

**必要な環境変数:**
- `SLACK_BOT_TOKEN`: Slackボットトークン（必須）
- `SLACK_CHANNEL_ID`: 通知先チャンネルID（必須）
- `SLACK_USER_MENTION`: メンションするユーザー（オプション、例: `<@USER_ID>`）

**ドキュメント:**
- [インストールガイド](https://github.com/volareinc/carmo-ai/blob/main/predict_contract/plugins/slack-notification/README.md)
- [詳細ドキュメント](https://github.com/volareinc/carmo-ai/blob/main/predict_contract/plugins/slack-notification/skills/slack-notification/SKILL.md)

## インストール

### マーケットプレイスをClaude Codeに追加

1. Claude Codeを開く
2. コマンドを実行: `/plugin marketplace add`
3. このリポジトリURLを入力: `https://github.com/takemi-ohama/ai-agent-marketplace`

### プラグインのインストール

```bash
/plugin install mcp-integration@ai-agent-marketplace
```

Claude Codeが自動的に：
1. プラグインをダウンロード
2. ファイルをプロジェクトの `.claude/` ディレクトリにコピー
3. スキルを自動起動可能にする

### インストールの確認

スキルがプロジェクトに表示されることを確認：
```bash
ls -la .claude/skills/mcp-integration/
```

## 使い方

### MCP Integrationスキル

以下のキーワードを言及すると自動的に起動：
- "MCPサーバーをセットアップ"
- "GitHub/BigQuery/Notionをインテグレート"
- "コード分析を有効化"
- "Serenaを設定"

または手動で起動：
```
@mcp-integration-skill MCPのセットアップを手伝って
```

## プラグイン開発

### ディレクトリ構造

```
ai-agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイスメタデータ
├── plugins/
│   └── {plugin-name}/
│       ├── .claude-plugin/
│       │   └── plugin.json       # プラグインメタデータ
│       ├── commands/             # スラッシュコマンド (*.md)
│       ├── agents/               # サブエージェント (*.md)
│       └── skills/               # プロジェクトスキル (SKILL.md)
└── README.md
```

### 新しいプラグインの作成

1. プラグインディレクトリを作成:
   ```bash
   mkdir -p plugins/my-plugin/{.claude-plugin,commands,agents,skills}
   ```

2. `plugin.json` を作成:
   ```json
   {
     "name": "my-plugin",
     "version": "1.0.0",
     "description": "プラグインの説明",
     "author": {
       "name": "あなたの名前",
       "url": "https://github.com/username"
     }
   }
   ```

3. スキル、コマンド、またはエージェントを追加

4. `marketplace.json` に登録:
   ```json
   {
     "plugins": [
       {
         "name": "my-plugin",
         "path": "plugins/my-plugin",
         "description": "簡単な説明"
       }
     ]
   }
   ```

### プロジェクトスキル

スキルは関連性がある時にClaude Codeによって自動的に起動されます。詳細は[Claude Codeスキルドキュメント](https://docs.claude.com/en/docs/claude-code/skills)を参照してください。

**重要な要件:**
- エントリポイントは `SKILL.md` という名前でなければならない
- `name` と `description` を含むYAML frontmatterを含める
- 自動起動のためのキーワードをdescriptionに含める

## コントリビューション

1. このリポジトリをフォーク
2. 新しいプラグインを作成または既存のものを改善
3. プルリクエストを送信
4. 新しいプラグインを追加する場合は marketplace.json を更新

## マーケットプレイス管理

### プラグインの更新

プラグインはバージョン管理されています。更新するには：

1. プラグインファイルを修正
2. `plugin.json` のバージョンをインクリメント
3. 変更をコミットしてプッシュ
4. ユーザーはClaude Code UIから更新

### プラグインの削除

1. `marketplace.json` から削除
2. オプションでプラグインディレクトリを削除
3. 変更をコミット

## リファレンス

- [Claude Codeドキュメント](https://docs.claude.com/en/docs/claude-code)
- [MCP仕様](https://modelcontextprotocol.io)
- [GitHub MCPサーバー](https://github.com/github/github-mcp-server)
- [Serena MCP](https://github.com/oraios/serena)
- [BigQuery MCP](https://github.com/ergut/mcp-server-bigquery)
- [Notion MCP](https://mcp.notion.com)

## ライセンス

MITライセンス - 詳細はLICENSEファイルを参照

## サポート

問題や質問がある場合:
- このリポジトリにイシューを開く
- プラグイン作者に連絡（plugin.jsonを参照）
