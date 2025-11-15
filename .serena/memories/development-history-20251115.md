# 開発履歴と知見 (2025-11-15)

## 期間
2025-11-12 〜 2025-11-15

## 主要な開発内容

### 1. Stop Hook無限ループ問題の解決

**課題:**
Stop hookスクリプト内でClaude CLIをサブプロセスとして呼び出すと、そのサブプロセスが終了時に自身のStop hookをトリガーし、無限ループが発生する問題。

**試行錯誤の履歴（失敗→成功）:**

#### 試行1: `CLAUDE_DISABLE_HOOKS`環境変数 ❌
```bash
export CLAUDE_DISABLE_HOOKS=1
claude -p "prompt"
```
**結果:** 動作せず。この環境変数は実装されていない。

**コミット:**
- 83263fd: Disable: Claude CLI要約を無効化して無限ループを防止
- cec82c5: Remove: 無効な環境変数CLAUDE_DISABLE_HOOKSを削除

#### 試行2: `stop_hook_active`フィールドチェック ❌
```bash
STOP_HOOK_ACTIVE=$(echo "$HOOK_INPUT" | grep -o '"stop_hook_active":[^,}]*')
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi
```
**結果:** ドキュメントには記載されているが、実際のhook入力には`stop_hook_active`フィールドが含まれない。

**コミット:**
- 84ce01c: Fix: stop_hook_activeチェック時の出力を削除

#### 試行3: `--settings`フラグでhooks無効化 ⚠️
```bash
claude -p --settings '{"disableAllHooks": true}' --output-format text
```
**結果:** hooksは無効化されたが、pluginsは有効のままでまだ問題が残る。

**コミット:**
- 9b09224: Fix: Stop Hook無限ループを解決 - Claude CLI呼び出し時に--settingsでhooks無効化

#### 試行4: `--settings`でhooksとplugins両方を無効化 ✅
```bash
claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' --output-format text
```
**結果:** 完全に無限ループを防止。これが最終解決策。

**コミット:**
- 758510b: Refactor: Claude CLI呼び出し時にhooksとplugins両方を無効化
- 6ed9859: Fix: Claude CLI呼び出し時にプラグインも無効化

**重要な学び:**
1. `CLAUDE_DISABLE_HOOKS`環境変数は存在しない（ドキュメント未記載）
2. `stop_hook_active`フィールドは実際には送信されない（ドキュメントと実装の乖離）
3. `--settings`フラグは`claude --help`で確認可能だが、ドキュメントには詳細記載なし
4. **hooksだけでなくpluginsも無効化することが重要** ← これが決定的

### 2. Slack通知機能の進化

#### Phase 1: Webhook方式 (v1.x)
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```
**問題:** 制御が限定的、メッセージ削除・更新ができない

#### Phase 2: Bot Token方式 (v2.x) ✅
```bash
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_CHANNEL_ID=C123456789
SLACK_USER_MENTION=U123456789
```
**利点:**
- `chat.postMessage`でメンション付き投稿→通知音
- `chat.delete`でメッセージ削除
- メンションなし再投稿でクリーンな履歴

**コミット:**
- 2eef43f: Slack通知のメンション削除機能を実装
- bde4943: Refactor: 要約生成後にメンション削除するよう変更

### 3. 要約生成の3段階フォールバック実装

**実装順序（優先度順）:**

#### 方法1: Claude CLI（AIによる高品質要約） 🥇
```bash
claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' \
  --output-format text <<EOF
以下の会話から実施した作業を40文字以内で要約してください。
...
EOF
```
**利点:** 最も高品質、文脈を理解した要約
**欠点:** 時間がかかる、無限ループリスクあり（対策済み）

**コミット:**
- c291f91: Claude CLIを使った要約生成機能を追加
- 359ed7b: 要約生成プロンプトを改善し挨拶文を除去
- 3588857: プロンプトを厳格化し具体例を追加

#### 方法2: transcript解析 🥈
```javascript
const transcript = fs.readFileSync(transcriptPath, 'utf-8');
const lines = transcript.trim().split('\n');
// 最後のAssistantメッセージから要約を抽出
```
**利点:** 高速、確実
**欠点:** セッションログが大きいと処理が重い

**コミット:**
- c253bbc: ShellスクリプトをNode.jsに置き換えてtranscript解析を改善
- 99d8aeb: Stopフックをcommandタイプに変更してtranscript解析機能を追加

#### 方法3: git diff 🥉
```bash
git diff HEAD~1 --stat | head -1 | awk '{print $1}'
```
**利点:** 最も軽量、フォールバックとして確実
**欠点:** 詳細な内容がわからない

### 4. 文字長制限の調整

**試行錯誤の履歴:**
- 当初: 30文字 → 短すぎて情報不足
- 次: 文字長調整処理を実装 → 複雑すぎて保守困難
- 最終: 40文字に統一、文字長調整処理を削除 ✅

**コミット:**
- a691d7d: Remove: すべての文字長調整処理を削除
- d9dfcce: Remove: スクリプト側の文字長調整を削除

**重要な学び:**
- プロンプトで明示的に文字数制限を指示する方がシンプルで確実
- スクリプト側での文字列切り詰めは不要な複雑さを生む

### 5. ドキュメント改善

**コミット:**
- ba8c77d: Docs: plugins/ndf/README.mdをブラッシュアップ

**改善内容:**
1. Slack設定を最新実装に統一（WEBHOOK → BOT TOKEN）
2. Stop Hook無限ループ防止を最新方式に更新
3. 要約生成フローの3段階フォールバックを明記
4. トラブルシューティングセクションを強化
   - Slack Bot Token Scopesの確認手順
   - hooks_log.logの参照方法

## 重要な教訓

### 1. ドキュメントと実装の乖離に注意
- `stop_hook_active`フィールド: ドキュメントに記載あり、実装では送信されず
- `CLAUDE_DISABLE_HOOKS`環境変数: 存在しない

→ **実際の動作を確認しながら実装する**

### 2. 無限ループ防止は多層防御
- `--settings`でhooksとplugins無効化（最優先）
- transcript処理フラグチェック（追加防御）
- stop_hook_activeチェック（動作しない場合あり）

→ **最も確実な方法を優先し、フォールバックも用意**

### 3. プロンプトエンジニアリングの重要性
- 文字列処理よりプロンプトで制御する方がシンプル
- 具体例を含めることで精度向上
- 禁止事項を明示することでノイズ除去

→ **スクリプトの複雑さよりプロンプトの明確さを優先**

### 4. 段階的なフォールバック設計
- 高品質な方法を優先
- 軽量な方法をフォールバックとして確保
- エラーハンドリングを各層に実装

→ **ユーザー体験の一貫性を保つ**

### 6. プラグイン統合と整理 (PR #37)

**課題:**
マーケットプレイスに4つの個別プラグイン（ndf、mcp-integration、install-slack-hook、workflow-commands）が存在し、管理が複雑化。

**実施内容:**

#### 削除したプラグイン
1. **plugins/mcp-integration/** - 10個のMCPサーバー統合
2. **plugins/install-slack-hook/** - Slack通知機能
3. **plugins/workflow-commands/** - 6つの開発ワークフローコマンド

**コミット:**
- 236ce98: Remove: NDF統合済みプラグイン3つを削除してマーケットプレイスを整理

#### 統合後の構成
- **NDFプラグイン単一化**: すべての機能をNDFに集約
- **10 MCP servers**: GitHub、Notion、Serena、AWS Docs、BigQuery、Context7、Chrome DevTools、Codex、Claude Code、DBHub
- **6 commands**: `/ndf:pr`、`/ndf:review`、`/ndf:clean`、`/ndf:merge`、`/ndf:fix`、`/ndf:serena`
- **6 agents**: corder、data-analyst、researcher、scanner、memory-recorder、slack-notifier
- **Slack notifications**: AI生成要約機能付き

#### ドキュメント更新
1. **marketplace.json**: pluginsをNDF単一エントリに更新
2. **README.md**: 
   - MCPサーバー数: 9→10（Claude Code MCP追加）
   - コマンド形式: プレフィックス付き（`/ndf:pr`等）に統一
   - プラグインバージョン: 1.0.0→1.0.1
   - AI生成要約機能を強調

**統計:**
- 17ファイル削除
- 1,519行削除、5行追加

**重要な学び:**
1. **単一プラグイン戦略**: ユーザーは1つのプラグインインストールで全機能利用可能
2. **バージョン管理の統一**: 個別プラグインの非同期更新問題を解消
3. **設定のシンプル化**: 単一の.mcp.json、単一のhooks設定で管理
4. **ドキュメント保守の容易さ**: 1つのREADME.mdに全情報を集約

**ユーザーへの影響:**
- **既存ユーザー**: NDFインストール済みなら影響なし、個別プラグインは削除推奨
- **新規ユーザー**: シンプルな導線、1プラグインのみインストール

## 次回開発時の注意点

1. **Stop Hook実装時:**
   - `--settings '{"disableAllHooks": true, "disableAllPlugins": true}'`を必ず使用
   - transcript処理フラグも併用

2. **Slack通知実装時:**
   - Bot Token方式を優先（Webhook方式は非推奨）
   - メンション→削除→再投稿のフローを維持

3. **要約生成実装時:**
   - Claude CLI → transcript → git diffの順でフォールバック
   - プロンプトで文字数制限を明示

4. **ドキュメント更新時:**
   - 実装と齟齬がないか確認
   - トラブルシューティングを充実させる
   - 設定例を最新化

## 関連ファイル

- `plugins/ndf/README.md` - メインドキュメント
- `plugins/ndf/hooks/hooks.json` - Stop hookフック定義
- `plugins/ndf/scripts/slack-notify.js` - Slack通知スクリプト（Node.js）
- `CLAUDE.md` - AIエージェント向けガイドライン

## 参考リンク

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [Slack API Documentation](https://api.slack.com/)
- [Claude CLI Documentation](https://docs.anthropic.com/en/docs/claude-cli)
