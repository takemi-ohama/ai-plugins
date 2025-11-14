# Development Workflow Commands Plugin

GitHub開発ワークフローを効率化する6つのスラッシュコマンドを提供するClaude Codeプラグインです。

## 概要

このプラグインは、PR作成、レビュー対応、マージ、ブランチクリーンアップなど、GitHub開発フローの典型的な作業を自動化するコマンドを提供します。

## インストール

### 前提条件

- Claude Code がインストール済み
- GitHub Personal Access Tokenが設定済み（GitHub MCP必須）

### ステップ1: マーケットプレイスの追加

```bash
# Claude Codeで実行
/plugin marketplace add https://github.com/takemi-ohama/ai-agent-marketplace
```

### ステップ2: プラグインのインストール

```bash
# Claude Codeで実行
/plugin install development-workflow-commands@ai-agent-marketplace
```

## 含まれるコマンド

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

### 典型的なワークフロー

```bash
# 1. フィーチャーブランチで作業完了後、PRを作成
/pr

# 2. レビューコメントを受けたら修正対応
/fix

# 3. 自分でコードレビュー実施
/review

# 4. PRがマージされたらクリーンアップ
/merge

# 5. 定期的にマージ済みブランチを削除
/clean

# 6. 知見や教訓を記録
/serena
```

## 特徴

- ✅ **自動化**: 手動で実行していた作業を1コマンドで完結
- ✅ **エラー処理**: 各ステップでエラーチェック・安全確認を実施
- ✅ **日本語対応**: コミットメッセージやPR本文は日本語
- ✅ **GitHub MCP統合**: GitHub APIを活用した高度な操作
- ✅ **Serena MCP統合**: コードベースの知見を蓄積

## 必要な依存関係

このプラグインを最大限活用するには、以下のMCPサーバーが必要です：

- **GitHub MCP** (必須): PR作成、レビュー、マージ操作に使用
- **Serena MCP** (オプション): `/serena`コマンドで知見記録に使用

これらのMCPサーバーは[mcp-integration](../mcp-integration)プラグインで簡単にセットアップできます。

## トラブルシューティング

### コマンドが認識されない

1. Claude Codeを再起動
2. プラグインが正しくインストールされているか確認
   ```bash
   /plugin list
   ```

### PRの作成・操作に失敗する

1. GitHub Personal Access Tokenが設定されているか確認
2. 必要なスコープ（`repo`, `workflow`）が付与されているか確認
3. GitHub MCPが正常に動作しているか確認

### /serenaコマンドが動作しない

1. Serena MCPがインストールされているか確認
2. プロジェクトがアクティベートされているか確認
   ```
   mcp__serena__activate_project(".")
   ```

## 関連プラグイン

- [mcp-integration](../mcp-integration): GitHub MCP、Serena MCPなどの統合セットアップ
- [slack-notification](../slack-notification): 作業完了時のSlack通知

## サポート

問題が発生した場合：
1. 上記のトラブルシューティングセクションを確認
2. GitHubリポジトリでイシューを作成

## ライセンス

MIT License

## 作者

takemi-ohama - https://github.com/takemi-ohama

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずイシューを開いて変更内容を議論してください。
