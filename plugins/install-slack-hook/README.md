# Slack Notification Hook Plugin

Claude Code終了時に**自動的にSlack通知を送信**するプラグインです。AIが作業内容を分析し、日本語要約付きの通知をSlackチャンネルに投稿します。

## 概要

このプラグインは、Claude Code終了時（Stopフック）に自動的にSlack通知を送信します。gitの変更内容から日本語要約を生成し、リポジトリ名とタイムスタンプ付きで通知します。

**主な特徴：**

- **自動通知**: プラグインインストールのみで動作、追加設定不要
- **日本語要約**: git diffから自動的に日本語の作業要約を生成
- **スマート通知**: メンション→削除→再投稿で通知音とクリーン履歴を両立
- **リポジトリ識別**: 通知にリポジトリ名を含めて複数プロジェクトを識別
- **環境変数管理**: トークンは環境変数で安全に管理

## インストール

### 前提条件

- Claude Code がインストール済み
- Slack Workspace へのアクセス権限
- Slack Appの作成権限

### ステップ1: マーケットプレイスの追加

```bash
# Claude Codeで実行
/plugin marketplace add https://github.com/takemi-ohama/ai-agent-marketplace
```

### ステップ2: プラグインのインストール

```bash
# Claude Codeで実行
/plugin install install-slack-hook@ai-agent-marketplace
```

**これだけです！** プラグインをインストールすると、Stopフックが自動的に有効になります。

### ステップ3: Slack Appのセットアップ

#### 3a. Slack Appの作成

1. https://api.slack.com/apps にアクセス
2. "Create New App" をクリック
3. "From scratch" を選択
4. App名を入力（例: "Claude Code Notifier"）
5. Workspaceを選択

#### 3b. Bot Token Scopesの追加

1. 左メニューから "OAuth & Permissions" を選択
2. "Scopes" セクションまでスクロール
3. "Bot Token Scopes" に以下を追加：
   - `chat:write` （必須 - メッセージ送信・削除用）
   - `channels:read` （オプション - チャンネル情報取得用）

#### 3c. Workspaceへのインストール

1. ページ上部の "Install to Workspace" をクリック
2. 権限を確認して "Allow" をクリック
3. **Bot User OAuth Token** をコピー（`xoxb-`で始まる）

#### 3d. Botをチャンネルに追加

1. Slackで通知先チャンネルを開く
2. チャンネル名をクリック → "Integrations" タブ
3. "Add apps" をクリック
4. 作成したアプリを選択して追加

#### 3e. チャンネルIDの取得

1. 通知先チャンネルを開く
2. チャンネル名をクリック
3. 下部の「その他」→ チャンネルIDをコピー（`C`で始まる）

#### 3f. ユーザーIDの取得（オプション - 通知音用）

1. Slackでプロフィールを開く
2. "その他" → "メンバーIDをコピー"（`U`で始まる）

### ステップ4: 環境変数の設定

シェル設定ファイル（`~/.bashrc`, `~/.zshrc`等）に環境変数を追加します：

```bash
# Slack Bot Token（必須）
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"

# 通知先チャンネルID（必須）
export SLACK_CHANNEL_ID="C0123456789"

# メンション用ユーザーID（オプション - 通知音を鳴らす場合）
export SLACK_USER_MENTION="<@U0123456789>"
```

設定後、シェルを再起動するか以下を実行：

```bash
source ~/.bashrc  # または ~/.zshrc
```

**⚠️ セキュリティ注意事項:**
- ✅ 環境変数はシェル設定ファイル（`~/.bashrc`, `~/.zshrc`）に追加
- ✅ トークンの値は引用符で囲む
- ✅ `SLACK_USER_MENTION`は`<@...>`形式
- ❌ **絶対に**トークンをGitにコミットしない
- ❌ **絶対に**トークンをコードやドキュメントに記載しない
- ❌ **絶対に**トークンをスクリーンショットや画面共有で公開しない
- ⚠️ トークンは実際のトークン値に置き換えてください（`xoxb-your-bot-token-here`は例です）
- ⚠️ トークンが漏洩した場合は、即座にSlack Appの設定でトークンをリボーク（無効化）してください

### ステップ5: 動作確認

プラグインをインストールした後、Claude Codeを一度終了して動作確認します。

**自動テスト（推奨）:**
```bash
# Claude Codeでなにか作業を行い、終了するだけ
# 自動的にSlack通知が送信されます
```

**手動テスト（任意）:**
スクリプトを直接実行する場合：
```bash
# プラグインのスクリプトパスを確認
find ~/.claude/plugins -name "slack-notify.sh" -type f

# 見つかったパスを使って実行
bash <見つかったパス> complete "テスト通知"
```

成功すると、Slackチャンネルに通知が届きます：

```
[リポジトリ名] Claude Codeの作業が完了しました (2025-11-14 15:30:00)
作業内容: slack-notify.shを更新
```

## 仕組み

### 通知フロー

1. **Claude Code終了** → Stopフックがトリガー
2. **スクリプト実行** → `scripts/slack-notify.sh complete`が実行される
3. **要約生成** → git diffから日本語の作業要約を自動生成
4. **Slack通知（3段階）**
   - **ステップ1**: メンション付きで投稿 → 通知音が鳴る
   - **ステップ2**: メッセージを即座に削除
   - **ステップ3**: メンションなしで詳細メッセージを再投稿 → 履歴はクリーン

### プラグインHooksの自動マージ

このプラグインは`hooks/hooks.json`を含んでいます。プラグインが有効な間、これらのhooksは**自動的にユーザーのhooksとマージ**されます：

- ユーザーの`.claude/settings.json`は変更されません
- プラグインを無効化すると、hooksも自動的に無効化されます
- 複数のプラグインhooksが同時に動作可能です

### 要約生成ロジック

`scripts/slack-notify.sh`は以下の情報から要約を生成：

- **git diff**: 変更されたファイル名とdiffステータス
- **ファイル名の日本語化**: 拡張子やファイル名から判断
- **変更タイプ**: 更新/追加/削除を検出
- **40文字制限**: Slackメッセージに適した長さ

**例：**
- `slack-notify.sh`を更新 → "slack-notify.shを更新"
- `README.md`, `SKILL.md`, `plugin.json`を更新 → "README.md等3件のファイルを更新"

### 通知メッセージの形式

```
[リポジトリ名] Claude Codeの作業が完了しました (日時)
作業内容: [git変更から生成された日本語要約]
```

## ファイル構成

```
plugins/install-slack-hook/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ
├── hooks/
│   └── hooks.json               # Stopフック定義
├── scripts/
│   └── slack-notify.sh          # 通知スクリプト
└── README.md                    # このファイル
```

### hooks/hooks.json

プラグインのStopフック定義：

```json
{
  "Stop": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "bash",
          "args": [
            "${CLAUDE_PLUGIN_ROOT}/scripts/slack-notify.sh",
            "complete"
          ],
          "description": "Send Slack notification when Claude Code exits"
        }
      ]
    }
  ]
}
```

- `${CLAUDE_PLUGIN_ROOT}`: プラグインディレクトリへのパス（自動設定）
- `type: "command"`: bashコマンドを実行
- `Stop`: Claude Code終了時にトリガー

### scripts/slack-notify.sh

Slack通知を送信するシェルスクリプト：
- git変更の検出と日本語要約生成
- Slack APIへのメッセージ投稿
- メンション→削除→再投稿のスマート通知

## カスタマイズ

### 通知メッセージのフォーマット変更

`scripts/slack-notify.sh`の`DETAILED_MESSAGE`変数を編集：

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

### 手動実行

スクリプトを直接実行してテストする場合：

```bash
# プラグインのインストール先を確認
PLUGIN_PATH=$(find ~/.claude/plugins -name "install-slack-hook" -type d | head -1)

# 基本的なテスト（自動要約）
bash "${PLUGIN_PATH}/scripts/slack-notify.sh" complete

# カスタム要約を指定
bash "${PLUGIN_PATH}/scripts/slack-notify.sh" complete "READMEファイルを更新"
```

### スクリプトの引数

```bash
# 使用方法
slack-notify.sh [message_type] [work_summary]

# 引数1: メッセージタイプ（デフォルト: "complete"）
#   - complete: 作業完了
#   - error: エラー発生
#   - session_end: セッション終了

# 引数2: 作業内容（オプション）
#   - 指定した場合: その内容を使用
#   - 省略した場合: git diffから自動生成
```

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

**原因：** `SLACK_USER_MENTION` が設定されていない、または形式が間違っている

**対処法：**
```bash
export SLACK_USER_MENTION="<@U0123456789>"
```

ユーザーIDは `<@` と `>` で囲む必要があります。

### プラグインhooksが動作しない

**プラグインが有効か確認：**
```bash
# Claude Codeで実行
/plugin list
```

`install-slack-hook`が表示され、有効になっているか確認。

**Claude Codeを再起動：**
プラグインインストール後は、Claude Codeを再起動する必要があります。

### スクリプトが実行されない

**スクリプトの実行権限を確認：**
```bash
# プラグインパスを探す
PLUGIN_PATH=$(find ~/.claude/plugins -name "install-slack-hook" -type d | head -1)
ls -la "${PLUGIN_PATH}/scripts/slack-notify.sh"
```

実行権限がない場合は追加：
```bash
chmod +x "${PLUGIN_PATH}/scripts/slack-notify.sh"
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

## セキュリティのベストプラクティス

### トークン管理

**必須:**
- ✅ **環境変数でトークンを管理**（シェル設定ファイルに記載）
- ✅ **必要最小限のBotスコープ**を使用（`chat:write`のみ、`channels:read`は任意）
- ✅ **トークンを定期的にローテーション**（推奨: 3-6ヶ月ごと）
- ❌ **絶対に**スクリプト内にトークンをハードコードしない
- ❌ **絶対に**トークンをGitリポジトリにコミットしない
- ❌ **絶対に**トークンをドキュメントやコメントに記載しない

### トークン漏洩時の対応

万が一トークンが漏洩した場合、**即座に**以下を実行してください：

1. **トークンを無効化**
   - https://api.slack.com/apps にアクセス
   - 対象のアプリを選択
   - "OAuth & Permissions" → "Revoke" ボタンをクリック

2. **新しいトークンを発行**
   - "Reinstall to Workspace" で再インストール
   - 新しいトークンを環境変数に設定

3. **影響範囲を確認**
   - Slackのアクセスログを確認
   - 不審なメッセージ投稿がないか確認

### ファイルパーミッション

シェル設定ファイルの権限を適切に設定：

```bash
# ~/.bashrc または ~/.zshrc の権限を確認
ls -la ~/.bashrc

# 他のユーザーが読めないように設定
chmod 600 ~/.bashrc
```

### 共有環境での注意

- 共有サーバーでは個人用トークンを使用
- チーム用トークンは専用のサービスアカウントで管理
- トークンをログに出力しない（スクリプトは既に対策済み）

## プラグインのアンインストール

```bash
# Claude Codeで実行
/plugin uninstall install-slack-hook
```

プラグインをアンインストールすると、hooksも自動的に無効化されます。

## サポート

問題が発生した場合：
1. 上記のトラブルシューティングセクションを確認
2. [Slack API公式ドキュメント](https://api.slack.com/docs)を参照
3. [GitHubリポジトリ](https://github.com/takemi-ohama/ai-agent-marketplace)でイシューを作成

## ライセンス

MIT License

## 作者

takemi-ohama - https://github.com/takemi-ohama

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずイシューを開いて変更内容を議論してください。
