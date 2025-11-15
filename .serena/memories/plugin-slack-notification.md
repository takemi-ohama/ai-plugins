# Slack Notification プラグイン詳細

## プラグイン情報

- **名前**: slack-notification
- **バージョン**: 2.0.0 (Bot Token方式、Node.js実装)
- **作者**: takemi-ohama
- **タイプ**: プロジェクトスキル + フック
- **パス**: `plugins/slack-notification`

## 概要

Claude Code作業完了時に自動的にSlack通知を送信するプラグイン。日本語で作業要約を生成し、リポジトリ名を含めた通知をチームに送信。

## 主要機能

### 🔔 スマート通知
- **メンション付き投稿**: 通知音を鳴らす
- **即座に削除**: メンション付きメッセージを削除
- **メンションなし再投稿**: チャンネル履歴をクリーンに保つ

### 📝 日本語要約生成
- Git差分から作業内容を自動要約
- 単一ファイル: `filename.shを更新`
- 複数ファイル: `filename.sh等3件のファイルを更新`
- 最大40文字に切り詰め

### 🏷️ リポジトリコンテキスト
- 通知にリポジトリ名を自動的に含める
- プロジェクト識別を容易に

### ⚙️ ポータブル設定
- プロジェクト内のどのサブディレクトリからでも動作
- `.claude`ディレクトリを上方向に検索

## ファイル構造

```
plugins/slack-notification/
├── .claude-plugin/
│   └── plugin.json                      # プラグインメタデータ
├── .claude/
│   ├── settings.json                    # フック設定
│   └── slack-notify.sh                  # 通知スクリプト（実行可能）
├── skills/
│   └── slack-notification/
│       └── SKILL.md                     # スキルドキュメント
└── README.md                            # セットアップガイド
```

## 通知メッセージ例

```
[carmo-ai] Claude Codeの作業が完了しました (2025-11-12 00:17:58)
作業内容: slack-notify.shを更新
```

## 必要な環境変数

### 必須
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_CHANNEL_ID="C05MS4DBF9V"
export SLACK_USER_MENTION="U05MS4DBF9V"  # ユーザーID（<@...>形式ではない）
```

### 非推奨（v1.x互換性のため残存）
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

**注意**: v2.xではBot Token方式を推奨。Webhook方式は削除・更新ができないため、メンション機能が完全に動作しない。

## Slackアプリの設定

### 1. Slackアプリの作成
1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. アプリ名とワークスペースを選択

### 2. Bot Token Scopesの追加
必須スコープ:
- `chat:write`: メッセージ投稿・削除

オプショナル:
- `channels:read`: チャンネル一覧取得

### 3. インストールと設定
1. ワークスペースにアプリをインストール
2. Bot User OAuth Tokenをコピー
3. `SLACK_BOT_TOKEN`環境変数に設定
4. ボットをチャンネルに招待: `/invite @your-bot-name`

### 4. チャンネルIDの取得
チャンネルのURLから取得:
```
https://app.slack.com/client/T1234567/C05MS4DBF9V
                                      ^^^^^^^^^^^^
                                      チャンネルID
```

### 5. ユーザーIDの取得
ユーザープロフィールから:
1. プロフィールを開く
2. "その他" → "メンバーIDをコピー"
3. `<@USER_ID>`形式で使用

## セットアップ手順

### 1. プラグインファイルのコピー
```bash
# .claude/ディレクトリにファイルをコピー
cp plugins/slack-notification/.claude/settings.json .claude/
cp plugins/slack-notification/.claude/slack-notify.sh .claude/
chmod +x .claude/slack-notify.sh
```

### 2. 環境変数の設定
`.env`ファイルまたはシェルプロファイルに追加:
```bash
export SLACK_BOT_TOKEN="xoxb-xxxxxxxxxxxx"
export SLACK_CHANNEL_ID="C05MS4DBF9V"
export SLACK_USER_MENTION="<@U05MS4DBF9V>"
```

### 3. テスト実行
```bash
.claude/slack-notify.sh complete
```

### 4. Claude Codeを再起動
フック設定をロードするために再起動

## 動作フロー

### 通知シーケンス

1. **Claude Code終了** → Stopフックがトリガー
2. **スクリプト起動** → `.claude`ディレクトリを上方向に検索
3. **メンション付き投稿** → `<@USER> Claude Codeの作業が完了しました`
4. **メッセージ削除** → 投稿したメッセージを即座に削除
5. **クリーンな再投稿** → リポジトリ名、タイムスタンプ、作業要約を含む

### 作業要約の生成

Git差分から自動生成:
```bash
# 単一ファイル変更
slack-notify.shを更新

# 複数ファイル変更
slack-notify.sh等3件のファイルを更新

# 長い場合は切り詰め
very-long-filename-that-exceeds-fo...
```

## フック設定

`.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "command": "claude_dir=\"$PWD\"; while [ \"$claude_dir\" != \"/\" ] && [ ! -d \"$claude_dir/.claude\" ]; do claude_dir=$(dirname \"$claude_dir\"); done; if [ -d \"$claude_dir/.claude\" ]; then \"$claude_dir/.claude/slack-notify.sh\" complete; fi",
        "background": true
      }
    ]
  }
}
```

### フックの種類
- **Stop**: 通常終了時（デフォルト）
- **SessionEnd**: すべてのセッション終了時
- **PostToolUse**: ツール実行後

## サイレントモード

`SLACK_CHANNEL_ID`が設定されていない場合:
- スクリプトは静かに終了（status 0）
- エラーメッセージなし
- Slack未設定環境でもシームレスに動作

## トラブルシューティング

### 通知音が鳴らない
- チャンネルの通知設定を確認
- `SLACK_USER_MENTION`が正しく設定されているか確認
- ボットに`chat:write`スコープがあるか確認

### スクリプトが見つからない
- `.claude/slack-notify.sh`が存在するか確認
- 実行権限があるか確認: `chmod +x .claude/slack-notify.sh`
- gitリポジトリ内で実行しているか確認

### メッセージが削除されない
- ボットに`chat:write`スコープが必要
- ボットトークンの権限を確認

### 日本語要約が生成されない
- gitリポジトリで実行しているか確認
- git差分が存在するか確認: `git diff`

## カスタマイズ

### メッセージ内容の変更
`.claude/slack-notify.sh`の`MESSAGE`変数を編集:
```bash
MESSAGE="Custom message here (${TIMESTAMP})"
```

### ユーザーメンションの無効化
`SLACK_USER_MENTION`環境変数を未設定または空にする

### 通知トリガーの変更
`.claude/settings.json`で異なるフックを使用:
- `Stop`: 通常終了時
- `SessionEnd`: すべてのセッション終了
- `PostToolUse`: ツール実行後

## セキュリティ注意事項

- `SLACK_BOT_TOKEN`をgitにコミットしない
- `.env`を`.gitignore`に追加
- 環境変数で機密情報を管理
- ボットトークンは`xoxb-`で始まる

## 技術詳細

### スクリプト言語
- Bash（POSIX互換）

### 依存関係
- `curl`: Slack API呼び出し
- `git`: 作業要約生成
- `jq`: JSON解析（オプション）

### ポータビリティ
- ハードコードパスなし
- 上方向に`.claude`ディレクトリを検索
- サブディレクトリから実行可能

## 参考リンク

- [Slack API Documentation](https://api.slack.com/docs)
- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [Slack Bot Token Scopes](https://api.slack.com/scopes)
