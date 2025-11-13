# Slack Notification Plugin

Claude Codeの作業完了時に、**自動的に**Slackへ日本語要約付きの通知を送信するプラグインです。

## 概要

このプラグインは、プロジェクトフックとして動作し、Claude Codeの終了時に自動的にSlack通知を送信します。git履歴から作業内容を分析し、**日本語で要約**した通知を送ります。

**スマート通知機能搭載**: メンション→削除→再投稿のパターンで、通知音を鳴らしつつチャンネルをクリーンに保ちます。

**提供される機能：**

- **自動通知**: Claude Code作業終了時に自動でSlack通知
- **日本語要約**: git変更履歴から作業内容を日本語で自動生成
- **リポジトリ識別**: 通知にリポジトリ名を含めて複数プロジェクトを識別
- **通知音対応**: メンションパターンで確実に通知音を鳴らす
- **クリーン履歴**: 最終メッセージにメンションを残さない

## インストール

### 前提条件

- Claude Code がインストール済み
- Slack Workspace へのアクセス権限
- Slack Appの作成権限

### ステップ1: プラグインのインストール

```bash
# Claude Codeで実行
/plugin install slack-notification@ai-agent-marketplace
```

### ステップ2: Slack Appのセットアップ

#### 2a. Slack Appの作成

1. https://api.slack.com/apps にアクセス
2. "Create New App" をクリック
3. "From scratch" を選択
4. App名を入力（例: "Claude Code Notifier"）
5. Workspaceを選択

#### 2b. Bot Token Scopesの追加

1. 左メニューから "OAuth & Permissions" を選択
2. "Scopes" セクションまでスクロール
3. "Bot Token Scopes" に以下を追加：
   - `chat:write` （必須 - メッセージ送信用）
   - `channels:read` （オプション - チャンネル情報取得用）

#### 2c. Workspaceへのインストール

1. ページ上部の "Install to Workspace" をクリック
2. 権限を確認して "Allow" をクリック
3. **Bot User OAuth Token** をコピー（`xoxb-`で始まる）

#### 2d. Botをチャンネルに追加

1. Slackで通知先チャンネルを開く
2. チャンネル名をクリック → "Integrations" タブ
3. "Add apps" をクリック
4. 作成したアプリを選択して追加

#### 2e. チャンネルIDの取得

1. 通知先チャンネルを開く
2. チャンネル名をクリック
3. 下部の「その他」→ チャンネルIDをコピー（`C`で始まる）

#### 2f. ユーザーIDの取得（オプション - 通知音用）

1. Slackでプロフィールを開く
2. "その他" → "メンバーIDをコピー"（`U`で始まる）

### ステップ3: 環境変数の設定

プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を記載します：

```bash
# Slack Bot Token（必須）
# 取得方法: https://api.slack.com/apps → OAuth & Permissions → Bot User OAuth Token
SLACK_BOT_TOKEN=<your-bot-token-here>

# 通知先チャンネルID（必須）
# 取得方法: Slackでチャンネルを開く → チャンネル名をクリック → チャンネルIDをコピー
SLACK_CHANNEL_ID=<your-channel-id>

# メンション用ユーザーID（オプション - 通知音を鳴らす場合）
# 取得方法: Slackでプロフィールを開く → その他 → メンバーIDをコピー
SLACK_USER_MENTION=<@your-user-id>
```

**セキュリティ確保:**

`.env` ファイルを `.gitignore` に追加して、トークンが誤ってコミットされないようにします：

```bash
# .gitignoreに追加（まだの場合）
echo ".env" >> .gitignore
```

確認：
```bash
# .envが.gitignoreに含まれているか確認
grep "^\.env$" .gitignore
```

**注意事項:**
- ✅ `.env`ファイルはプロジェクトルートに配置
- ✅ トークンの値は`=`の後に直接記載（`export`は不要）
- ✅ `.env`を必ず`.gitignore`に追加
- ❌ `.env`ファイルをGitにコミットしない

### ステップ4: 動作確認

テスト通知を送信して、設定が正しいか確認します：

```bash
# プロジェクトルートで実行
.claude/slack-notify.sh complete
```

成功すると、Slackチャンネルに以下のような通知が届きます：

```
[リポジトリ名] Claude Codeの作業が完了しました (2025-11-13 15:30:00)
作業内容: READMEファイルの更新
```

## 特徴

- ✅ **インテリジェント要約**: AIがセッション内容を分析し、意味のある日本語要約を自動生成
- ✅ **自動実行**: Claude Code終了時に自動でフック起動
- ✅ **コンテキスト理解**: 会話履歴とgit変更を統合して具体的な要約を作成
- ✅ **スマート通知**: メンション→削除→再投稿で通知音とクリーン履歴を両立
- ✅ **リポジトリ識別**: 複数プロジェクトで作業時も識別可能
- ✅ **ポータブル**: プロジェクトのサブディレクトリからも動作
- ✅ **柔軟な設定**: .envファイルまたは環境変数で設定可能
- ✅ **後方互換性**: スキルなしでも従来のgit diff方式で動作

## 通知の仕組み

### 通知フロー

1. **Claude Code終了** → Stopフックがトリガー
2. **スキルの起動** → `slack-notification`スキルが自動実行
3. **作業内容の分析**
   - セッションの会話履歴を確認
   - 実行されたツール呼び出しを分析
   - git変更履歴を確認（`git log`, `git diff`, `git status`）
   - 主要な達成事項を特定
4. **日本語要約の生成**
   - 具体的で意味のある要約を作成（最大100文字）
   - ファイル名や重要なアクションを含める
   - 自然な日本語表現を使用
5. **スクリプトの実行**
   - スキルが`.claude/slack-notify.sh complete "生成した要約"`を実行
   - 引数として要約を渡す
6. **通知の送信（3段階）**
   - **ステップ1**: メンション付きで投稿 → 通知音が鳴る
   - **ステップ2**: メッセージを即座に削除
   - **ステップ3**: メンションなしで詳細メッセージを再投稿 → 履歴はクリーン

### インテリジェント要約

スキルは以下の情報を統合して要約を生成：

- **会話コンテキスト**: ユーザーが何を依頼したか
- **ツール使用履歴**: PR作成、コミット、ファイル編集等
- **Git変更**: 変更されたファイルとコミットメッセージ
- **成果**: 最終的に達成されたこと

これにより、単なる「ファイル更新」ではなく、「PRレビュー対応でセキュリティ脆弱性3件修正」のような具体的な要約が生成されます。

### 通知メッセージの形式

```
[リポジトリ名] Claude Codeの作業が完了しました (日時)
作業内容: [git変更から生成された日本語要約]
```

**例：**
```
[ai-agent-marketplace] Claude Codeの作業が完了しました (2025-11-13 15:30:45)
作業内容: Slack通知プラグインのREADMEを更新
```

## 使用例

### 基本的な使い方

プラグインをインストールして環境変数を設定すれば、あとは自動です。Claude Codeで作業して終了すると、スキルが自動的に：

1. セッション内容を分析
2. 適切な日本語要約を生成
3. Slack通知を送信

### 自動生成される要約の例

スキルは作業内容を理解して、以下のような具体的な要約を生成します：

- **PR作成時**: `"PRを作成: スラッシュコマンド追加"`
- **レビュー対応時**: `"セキュリティ脆弱性3件修正（認証情報の例をプレースホルダー化）"`
- **ドキュメント更新時**: `"Slack通知プラグインのREADMEを日本語化、.env対応を追加"`
- **複数ファイル変更時**: `"mcp-integrationにスラッシュコマンド6種を追加（PR, fix, review等）"`

### 手動でテスト

スクリプトを直接実行してテストすることもできます：

```bash
# 基本的なテスト（自動要約）
.claude/slack-notify.sh complete

# カスタム要約を指定してテスト
.claude/slack-notify.sh complete "READMEファイルを更新"

# サブディレクトリからでも動作
cd plugins/slack-notification
../../.claude/slack-notify.sh complete "テスト通知"
```

### スクリプトの引数

```bash
# 使用方法
.claude/slack-notify.sh [message_type] [work_summary]

# 引数1: メッセージタイプ（デフォルト: "complete"）
#   - complete: 作業完了
#   - error: エラー発生
#   - session_end: セッション終了

# 引数2: 作業内容（オプション）
#   - 指定した場合: その内容を使用
#   - 省略した場合: git diffから自動生成
```

### カスタムメッセージ

スクリプトを編集することで、通知メッセージをカスタマイズできます：

```bash
# .claude/slack-notify.shを編集
vim .claude/slack-notify.sh
```

## ファイル構成

```
plugins/slack-notification/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ
├── .claude/
│   ├── settings.json            # フック設定
│   └── slack-notify.sh          # 通知スクリプト
├── skills/
│   └── slack-notification/
│       └── SKILL.md             # スキル説明
└── README.md                    # このファイル
```

### .claude/settings.json

Claude Codeのstopフックを設定：

```json
{
  "stopHook": [".claude/slack-notify.sh", "complete"]
}
```

### slack-notify.sh

Slack通知を送信するシェルスクリプト：
- git変更の検出
- 日本語要約の生成
- Slack APIへの投稿

## トラブルシューティング

### 通知が届かない

**環境変数の確認：**
```bash
echo $SLACK_BOT_TOKEN
echo $SLACK_CHANNEL_ID
```

両方が出力されることを確認。空の場合は環境変数を設定し直してください。

**Botの権限確認：**
1. Slack Appの設定ページで "OAuth & Permissions" を開く
2. `chat:write` スコープがあるか確認
3. Botがチャンネルに追加されているか確認

### 通知音が鳴らない

**原因：** `SLACK_USER_MENTION` が設定されていない

**対処法：**
```bash
export SLACK_USER_MENTION="<@U0123456789>"
```

ユーザーIDは `<@` と `>` で囲む必要があります。

### スクリプトが実行されない

**スクリプトの実行権限を確認：**
```bash
ls -la .claude/slack-notify.sh
```

実行権限がない場合は追加：
```bash
chmod +x .claude/slack-notify.sh
```

**git リポジトリ確認：**
```bash
git status
```

gitリポジトリ外ではスクリプトが正常に動作しません。

### "command not found" エラー

**curl がインストールされているか確認：**
```bash
which curl
```

インストールされていない場合：
```bash
# macOS
brew install curl

# Ubuntu/Debian
sudo apt-get install curl
```

### タイムスタンプのフォーマットが正しくない

**原因：** macOSとLinuxで`date`コマンドの挙動が異なる

**対処法：**
macOSの場合、GNU版dateを使用：
```bash
brew install coreutils
# スクリプト内で gdate を使用
```

## セキュリティのベストプラクティス

- ✅ 環境変数でトークンを管理
- ✅ トークンをコードやドキュメントにコミットしない
- ✅ `.env`ファイルを使用する場合は`.gitignore`に追加
- ✅ 必要最小限のBotスコープを使用（`chat:write`のみ）
- ✅ トークンを定期的にローテーション
- ❌ スクリプト内にトークンをハードコードしない

## カスタマイズ

### 通知メッセージのフォーマット変更

`slack-notify.sh`の`DETAILED_MESSAGE`変数を編集：

```bash
# 現在
DETAILED_MESSAGE="[${REPO_NAME}] ${MESSAGE}\n作業内容: ${WORK_SUMMARY}"

# カスタム例
DETAILED_MESSAGE="✅ ${REPO_NAME} - ${WORK_SUMMARY} (${TIMESTAMP})"
```

### 通知条件のカスタマイズ

特定の条件でのみ通知を送信：

```bash
# 例: mainブランチへのコミット時のみ通知
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ]; then
    # 通知を送信
fi
```

## 詳細ドキュメント

- [SKILL.md](./skills/slack-notification/SKILL.md) - スキル概要
- [Slack API ドキュメント](https://api.slack.com/docs) - 公式API仕様

## サポート

問題が発生した場合：
1. 上記のトラブルシューティングセクションを確認
2. [Slack API公式ドキュメント](https://api.slack.com/docs)を参照
3. GitHubリポジトリでイシューを作成

## ライセンス

MIT License

## 作者

takemi-ohama - https://github.com/takemi-ohama

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずイシューを開いて変更内容を議論してください。
