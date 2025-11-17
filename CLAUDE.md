# Claude Code AIエージェント ガイドライン

## 目的

このドキュメントは、AI Agent Marketplaceリポジトリと対話するAIエージェント向けのガイドラインを提供します。

## Important Notes
* All AI agent interactions must be in Japanese.
* Never commit/push directly to main branch. Always create a working branch.
* Do not approve PRs without permission.


## リポジトリ概要

Claude Codeプラグインマーケットプレイスとして、以下を配布します：
- MCP（Model Context Protocol）統合スキル
- カスタムスラッシュコマンド
- サブエージェント設定
- プロジェクトフック

## Serena MCPの積極的な活用

このプロジェクトでの開発では、**Serena MCPを積極的に利用**してください。Serena MCPはセマンティックコード理解とシンボルベース編集を提供し、効率的なコード分析と編集を可能にします。

### Serena MCPの基本ワークフロー

#### 1. プロジェクトのアクティベート

最初に必ずプロジェクトをアクティベートします：

```bash
# プロジェクトをアクティベート
mcp__serena__activate_project /path/to/ai-agent-marketplace

# オンボーディング状態を確認
mcp__serena__check_onboarding_performed

# 必要に応じてオンボーディング実行
mcp__serena__onboarding
```

#### 2. メモリーの活用

プロジェクト情報はSerenaメモリーに記録されています：

```bash
# 利用可能なメモリー一覧
mcp__serena__list_memories

# メモリーの読み込み
mcp__serena__read_memory project-overview.md
mcp__serena__read_memory plugin-mcp-integration.md
mcp__serena__read_memory plugin-slack-notification.md
```

**重要**: タスク開始時に関連するメモリーを読み込んで、プロジェクトの文脈を理解してください。

#### 3. コード構造の理解

**ファイル全体を読む前に**、まずシンボル概要を取得します：

```bash
# ファイルのシンボル概要を取得（トップレベルのみ）
mcp__serena__get_symbols_overview plugins/mcp-integration/skills/mcp-integration/SKILL.md

# ディレクトリ構造の確認
mcp__serena__list_dir plugins recursive=false
```

#### 4. ターゲットを絞ったコード探索

シンボル検索を使って必要な部分だけを読み込みます：

```bash
# シンボルを名前で検索
mcp__serena__find_symbol name_path="/class_name" relative_path="plugins/example/"

# シンボルの本体を含めて読み込む
mcp__serena__find_symbol name_path="function_name" include_body=true

# 子要素も含めて取得（depth=1でメソッド等）
mcp__serena__find_symbol name_path="/ClassName" depth=1 include_body=false
```

#### 5. パターン検索

シンボル名が不明な場合は、パターン検索を使用します：

```bash
# 特定のパターンを検索
mcp__serena__search_for_pattern substring_pattern="SKILL.md" relative_path="plugins/"

# コードファイルのみに制限
mcp__serena__search_for_pattern substring_pattern="version" restrict_search_to_code_files=true
```

#### 6. シンボルベース編集

**推奨**: 可能な限りシンボルベース編集を使用します：

```bash
# シンボル本体の置き換え
mcp__serena__replace_symbol_body name_path="/function_name" relative_path="file.md" body="新しいコード"

# シンボルの後に挿入
mcp__serena__insert_after_symbol name_path="/ClassName" relative_path="file.py" body="新しいメソッド"

# シンボルの前に挿入（import文等）
mcp__serena__insert_before_symbol name_path="/first_function" relative_path="file.py" body="import statement"

# シンボルのリネーム（コードベース全体）
mcp__serena__rename_symbol name_path="/OldName" relative_path="file.py" new_name="NewName"
```

#### 7. 参照の検索

コード変更の影響範囲を理解します：

```bash
# シンボルを参照している箇所を検索
mcp__serena__find_referencing_symbols name_path="function_name" relative_path="source.py"
```

#### 8. メモリーへの記録

新しい情報や重要な発見をメモリーに記録します：

```bash
# 新しいメモリーを作成
mcp__serena__write_memory memory_file_name="plugin-new-feature.md" content="詳細な説明..."

# メモリーの編集
mcp__serena__edit_memory memory_file_name="project-overview.md" regex="old text" repl="new text"
```

### Serenaを使うべき場面

**必ず使用:**
- ✅ プラグイン構造の理解
- ✅ 既存のSKILL.mdファイルの編集
- ✅ plugin.jsonの更新
- ✅ 複数ファイルにまたがる参照の検索
- ✅ シンボルのリネーム

**使用を検討:**
- 🔍 マークダウンファイルの構造把握
- 🔍 設定ファイルの検索
- 🔍 パターンマッチング

**使用不要:**
- ❌ 小さなテキストファイルの読み込み（Readツール使用）
- ❌ JSON/YAMLの検証のみ（Readツール使用）
- ❌ 新規ファイルの作成（Writeツール使用）

### Serenaベストプラクティス

1. **段階的な探索**
   ```
   list_dir → get_symbols_overview → find_symbol → 詳細読み込み
   ```

2. **メモリーファースト**
   - タスク開始時に関連メモリーを読む
   - 新しい発見は必ずメモリーに記録

3. **シンボルベース編集優先**
   - 正規表現より安全で正確
   - リファクタリングにも対応

4. **トークン効率**
   - ファイル全体を読まない
   - 必要なシンボルだけを取得
   - `include_body=false`でメタデータのみ取得

## AIエージェントの責任

### 1. プラグイン開発

プラグインを作成・修正する際：

**実施すること:**
- README.mdに記載されたディレクトリ構造に従う
- `plugin.json`に完全なメタデータを含める
- YAMLフロントマターを含む明確なSKILL.mdファイルを書く
- 包括的なドキュメントを提供する
- コミット前に設定をテストする
- プラグイン追加時はmarketplace.jsonを更新する
- **Serena MCPでコード構造を理解してから編集する**

**してはいけないこと:**
- 機密トークンや認証情報をコミットする
- 適切なメタデータなしでプラグインを作成する
- ドキュメントをスキップする
- 一貫性のない命名規則を使用する
- **ファイル全体を読んでからSerenaツールで重複読み込みする**

### 2. MCP設定

MCP設定を扱う際：

**実施すること:**
- 認証に環境変数を使用する
- 明確なセットアップ手順を提供する
- トラブルシューティングセクションを含める
- 必要な権限をすべてドキュメント化する
- 異なる環境で設定をテストする

**してはいけないこと:**
- `.mcp.json`テンプレートにトークンをハードコードする
- 認証ドキュメントをスキップする
- セキュリティベストプラクティスを省略する
- ユーザー環境について仮定する

### 3. ドキュメント

ドキュメントを書く際：

**実施すること:**
- 明確で簡潔な言語で書く
- ステップバイステップの手順を提供する
- 使用例を含める
- 公式ドキュメントへのリンクを含める
- 一般的なトラブルシューティングシナリオをカバーする
- シンタックスハイライト付きコードブロックを使用する
- **Serenaメモリーで既存のドキュメントパターンを確認する**

**してはいけないこと:**
- 事前知識を前提とする
- 検証手順をスキップする
- 前提条件を省略する
- 曖昧な指示を書く

### 4. バージョン管理

バージョンを管理する際：

**実施すること:**
- セマンティックバージョニング（MAJOR.MINOR.PATCH）に従う
- plugin.jsonのバージョン番号を更新する
- 破壊的変更をドキュメント化する
- 以前のバージョンからのアップグレードをテストする

**してはいけないこと:**
- マイナーバージョンで破壊的変更を行う
- バージョンインクリメントをスキップする
- marketplace.jsonの更新を忘れる

## ファイル構造リファレンス

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
│       └── skills/               # プロジェクトスキル
│           └── {skill-name}/
│               ├── SKILL.md      # エントリポイント（必須）
│               └── *.md          # サポートドキュメント
├── README.md
├── CLAUDE.md                     # このファイル
└── .serena/                      # Serenaメモリー（自動生成）
    └── memories/
        ├── project-overview.md
        ├── plugin-mcp-integration.md
        └── plugin-slack-notification.md
```

## MCPインテグレーションプラグイン

### コンポーネント

MCPインテグレーションプラグインの構成：

1. **SKILL.md**: YAMLフロントマター付きエントリポイント
2. **mcp-config-template.md**: 完全な`.mcp.json`テンプレート
3. **mcp-authentication-guide.md**: トークンセットアップ手順
4. **mcp-setup-guide.md**: ステップバイステップインストール

### メンテナンスタスク

MCPインテグレーションを更新する際：

1. 新しいMCPサーバーを確認
2. 設定テンプレートを更新
3. 認証方法を検証
4. 最新のClaude Codeバージョンでテスト
5. ドキュメントを更新
6. plugin.jsonのバージョンをインクリメント
7. **Serenaメモリーを更新**

### サポート対象のMCP

現在統合されているMCP：

1. **GitHub MCP** (HTTP)
   - ツール: PR管理、イシュートラッキング、コード検索
   - 認証: GitHub Personal Access Token
   - ドキュメント: https://github.com/github/github-mcp-server

2. **Notion MCP** (HTTP)
   - ツール: 検索、ページ作成、データベース操作
   - 認証: Notion統合トークン
   - ドキュメント: https://mcp.notion.com

3. **Serena MCP** (Local)
   - ツール: コード分析、シンボル編集、メモリー管理
   - 認証: 不要（ローカル）
   - ドキュメント: https://github.com/oraios/serena

4. **AWS Documentation MCP** (Local)
   - ツール: ドキュメント検索、コンテンツ読み込み
   - 認証: 不要（公開ドキュメント）
   - ドキュメント: https://github.com/awslabs/aws-documentation-mcp-server

5. **BigQuery MCP** (Local)
   - ツール: クエリ実行、テーブル操作
   - 認証: Google Cloud認証情報
   - ドキュメント: https://github.com/ergut/mcp-server-bigquery

## 一般的なタスク

### 新しいMCPサーバーの追加

**Serenaワークフロー:**

1. **既存の構造を理解**
   ```bash
   mcp__serena__read_memory plugin-mcp-integration.md
   mcp__serena__get_symbols_overview plugins/mcp-integration/skills/mcp-integration/mcp-config-template.md
   ```

2. **設定ファイルを編集**
   ```bash
   # シンボルベースで既存の設定を確認
   mcp__serena__find_symbol name_path="mcpServers" relative_path="plugins/mcp-integration/skills/mcp-integration/mcp-config-template.md"
   ```

3. 新しいMCP設定を`mcp-config-template.md`に追加
4. 認証手順を`mcp-authentication-guide.md`に追加
5. 使用例を`mcp-setup-guide.md`に含める
6. SKILL.mdの説明を更新
7. 設定をテスト
8. プラグインバージョンをインクリメント
9. **メモリーを更新**
   ```bash
   mcp__serena__edit_memory memory_file_name="plugin-mcp-integration.md" regex="含まれるMCPサーバー\n\n### 1\\." repl="含まれるMCPサーバー\n\n### 0. 新しいMCP\n詳細...\n\n### 1."
   ```
10. 変更をコミット

### 新しいプラグインの作成

**Serenaワークフロー:**

1. **既存プラグインをパターンとして理解**
   ```bash
   mcp__serena__list_dir plugins/mcp-integration recursive=true
   mcp__serena__read_memory project-overview.md
   ```

2. ディレクトリ構造を作成:
   ```bash
   mkdir -p plugins/{plugin-name}/{.claude-plugin,commands,agents,skills}
   ```

3. メタデータ付きplugin.jsonを作成

4. コンテンツを追加（スキル、コマンド、またはエージェント）

5. marketplace.jsonに登録
   ```bash
   # Serenaで既存のmarketplace.jsonを読む
   mcp__serena__find_symbol name_path="plugins" relative_path=".claude-plugin/marketplace.json"
   ```

6. ドキュメントを作成

7. インストールプロセスをテスト

8. **新しいプラグインのメモリーを作成**
   ```bash
   mcp__serena__write_memory memory_file_name="plugin-{plugin-name}.md" content="詳細なドキュメント"
   ```

9. コミット＆プッシュ

### ドキュメントの更新

**Serenaワークフロー:**

1. **関連メモリーを確認**
   ```bash
   mcp__serena__list_memories
   mcp__serena__read_memory plugin-{name}.md
   ```

2. 既存コンテンツの正確性をレビュー

3. **シンボル検索で構造を理解**
   ```bash
   mcp__serena__get_symbols_overview path/to/file.md
   ```

4. リンク切れを確認

5. バージョン固有情報を更新

6. 新しいトラブルシューティングシナリオを追加

7. 明確さと完全性を向上

8. すべてのコマンドと例をテスト

9. **メモリーを更新**
   ```bash
   mcp__serena__edit_memory memory_file_name="plugin-{name}.md" regex="古い情報" repl="新しい情報"
   ```

10. 変更をコミット

## セキュリティガイドライン

### トークンと認証情報

**絶対にコミットしてはいけないもの:**
- GitHub Personal Access Tokens
- Notion統合トークン
- Google Cloudサービスアカウントキー
- その他の認証情報やシークレット

**必ず使用すること:**
- トークンには環境変数を使用
- テンプレートではプレースホルダー値を使用
- 認証情報セキュリティに関する明確な警告
- 安全な認証情報保存の手順

### 設定テンプレート

**含めるべきもの:**
- 環境変数用の`${VARIABLE_NAME}`構文
- 必要な権限を説明するコメント
- セキュリティベストプラクティスセクション
- 公式認証ガイドへのリンク

**避けるべきもの:**
- 本物に見える例示トークン
- インライン認証情報保存の推奨
- セキュリティ考慮事項のスキップ

## Stop Hook実装ガイドライン

### 重要: Stop Hookの正しい構造

Stop hookは**必ず以下の入れ子構造**で定義してください：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here"
          }
        ]
      }
    ]
  }
}
```

**注意**: `"Stop": [{"hooks": [...]}]`という入れ子構造が正しい仕様です。`"Stop": [{type: "command", ...}]`のようにフラットな構造にしないでください。

参照: https://code.claude.com/docs/en/hooks#stop-and-subagentstop-input

### Stop Hookの入力形式

Stop hookには以下のJSON入力が渡されます：

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

### 無限ループ防止（必須）

**重要**: Stop hookスクリプト内でClaude CLIを呼び出す場合、**必ず無限ループ防止策を実装**してください。

#### 方法1: stop_hook_activeフィールドのチェック

```bash
#!/bin/bash

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Check if stop_hook_active is true
STOP_HOOK_ACTIVE=$(echo "$HOOK_INPUT" | grep -o '"stop_hook_active":[^,}]*' | grep -o 'true\|false')

# If hook already executed, exit immediately
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  echo '{"continue": false}'
  exit 0
fi

# Your hook logic here...
```

#### 方法2: CLAUDE_DISABLE_HOOKS環境変数の設定

```bash
#!/bin/bash

# IMPORTANT: Prevent infinite loop when calling Claude CLI
export CLAUDE_DISABLE_HOOKS=1

# Now safe to call Claude CLI
claude --help
```

#### 方法3: transcriptの処理状態チェック

```bash
#!/bin/bash

# Check if transcript has already been processed
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | grep -o '"transcript_path":"[^"]*"' | cut -d'"' -f4)
PROCESSED_FLAG="/tmp/.claude-hook-processed-$(basename "$TRANSCRIPT_PATH")"

if [ -f "$PROCESSED_FLAG" ]; then
  echo '{"continue": false}'
  exit 0
fi

# Mark as processed
touch "$PROCESSED_FLAG"

# Your hook logic here...
```

### Stop Hookの出力形式

Stop hookは以下のJSON形式で出力できます：

```json
{
  "decision": "block",
  "reason": "追加のタスクがあります。次のステップ: ..."
}
```

- `"decision": "block"`: Claude Codeの停止をブロック（継続実行）
- `"decision"`: undefined または省略: 通常通り終了
- `"reason"`: blockの場合は必須。Claudeへの次の指示を記述

### 実装チェックリスト

Stop hookを実装する際：

- [ ] 入れ子構造 `"Stop": [{"hooks": [...]}]` を使用
- [ ] `stop_hook_active`チェックを実装
- [ ] Claude CLI呼び出し時は`CLAUDE_DISABLE_HOOKS=1`を設定
- [ ] transcriptの重複処理を防ぐ仕組みを実装（**最も確実**）
- [ ] 無限ループのテストを実施

### 実際の問題と解決策（実装時の注意点）

#### 問題1: stop_hook_activeフィールドが含まれない

**ドキュメントでは`stop_hook_active`フィールドが含まれると記載されていますが、実際のhook入力には含まれない場合があります。**

実際のhook入力例：
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project"
}
```

**解決策**: `stop_hook_active`チェックだけに依存せず、**transcript処理状態チェック（方法3）を必ず実装してください**。

#### 問題2: 複数のプラグインがStop hookを設定している

複数のプラグイン（例: `ndf`と`install-slack-hook`）がStop hookを設定している場合、それぞれが独立して実行され、無限ループが発生する可能性があります。

**解決策**:
1. 各プラグインでtranscript処理状態チェックを実装
2. 同じフラグファイル名を使用（例: `/tmp/.claude-hook-processed-{transcript-basename}`）
3. 最初に実行されたhookがフラグを作成し、2番目以降は即座に終了

#### 問題3: マーケットプレイスの更新が反映されない

ローカルで`hooks.json`やスクリプトを更新しても、`~/.claude/plugins/marketplaces/`にあるマーケットプレイスのコピーは自動的に更新されません。

**解決策**:
1. マーケットプレイスを再読み込み: Claude Codeを再起動またはプロジェクトを再読み込み
2. または、開発中は直接`~/.claude/plugins/marketplaces/`内のファイルを確認・更新
3. または、プラグインを一度削除して再インストール

#### 問題4: Stop hookスクリプト内でClaude CLIを呼び出すと無限ループ

Stop hookスクリプト内で`claude`コマンドをサブプロセスとして呼び出すと、そのサブプロセスが終了時に自身のStop hookをトリガーし、無限ループが発生します。

**解決策**: `--settings`フラグを使って、サブプロセスのhooksとpluginsを無効化します。

Node.jsの実装例：
```javascript
const { spawn } = require('child_process');

// Claude CLIをサブプロセスとして呼び出す際、hooksとpluginsを無効化
const claude = spawn('claude', [
  '-p',
  '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}',  // ★ これが重要
  '--output-format', 'text'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});
```

Bashの実装例：
```bash
# Claude CLIをサブプロセスとして呼び出す際、hooksとpluginsを無効化
claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' --output-format text
```

**重要**: `--settings`フラグは`claude --help`で確認できます：
```
--settings <file-or-json>   Path to a settings JSON file or a JSON string to load additional settings from
```

#### 推奨実装パターン（Bash）

```bash
#!/bin/bash

# IMPORTANT: Prevent infinite loop - Read stdin first
HOOK_INPUT=""
if [ ! -t 0 ]; then
  HOOK_INPUT=$(cat)
fi

# Method 1: Check stop_hook_active (may not always be present)
STOP_HOOK_ACTIVE=$(echo "$HOOK_INPUT" | grep -o '"stop_hook_active":[^,}]*' | grep -o 'true\|false')
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  echo '{"continue": false}'
  exit 0
fi

# Method 2: Extract transcript_path
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | grep -o '"transcript_path":"[^"]*"' | cut -d'"' -f4)

# Method 3: Check if transcript already processed (MOST RELIABLE)
if [ -n "$TRANSCRIPT_PATH" ]; then
  PROCESSED_FLAG="/tmp/.claude-hook-processed-$(basename "$TRANSCRIPT_PATH")"

  if [ -f "$PROCESSED_FLAG" ]; then
    echo '{"continue": false}'
    exit 0
  fi

  # Mark as processed
  touch "$PROCESSED_FLAG"
fi

# Your hook logic here...
```

#### 推奨実装パターン（Node.js）

```javascript
#!/usr/bin/env node

// Method 1: Set CLAUDE_DISABLE_HOOKS when calling Claude CLI
const claude = spawn('claude', ['-p'], {
  env: {
    ...process.env,
    CLAUDE_DISABLE_HOOKS: '1'  // Prevent Stop hook in subprocess
  }
});

// Method 2: Check transcript processed flag (MOST RELIABLE)
if (transcriptPath) {
  const processedFlagFile = path.join(
    require('os').tmpdir(),
    `.claude-hook-processed-${path.basename(transcriptPath)}`
  );

  if (fs.existsSync(processedFlagFile)) {
    console.log('{"continue": false}');
    process.exit(0);
  }

  fs.writeFileSync(processedFlagFile, new Date().toISOString());
}
```

## テストチェックリスト

変更をコミットする前に：

- [ ] すべてのJSONファイルが有効
- [ ] YAMLフロントマターが正しくパース可能
- [ ] リンクが正しい宛先を指している
- [ ] コード例が構文的に正しい
- [ ] インストール手順がゼロから機能する
- [ ] ドキュメントが明確で完全
- [ ] バージョン番号が更新されている
- [ ] 機密データがコミットに含まれていない
- [ ] **Serenaメモリーが最新の状態**

## Serena MCP活用チェックリスト

プラグイン開発時：

- [ ] プロジェクトをアクティベート済み
- [ ] 関連メモリーを読み込み済み
- [ ] ファイル全体読み込み前にsymbols_overviewを使用
- [ ] シンボル検索で必要な部分のみ取得
- [ ] 可能な限りシンボルベース編集を使用
- [ ] 新しい情報をメモリーに記録
- [ ] 参照検索で影響範囲を確認

## リファレンス

- [Claude Codeドキュメント](https://docs.claude.com/en/docs/claude-code)
- [プラグインマーケットプレイス](https://code.claude.com/docs/ja/plugin-marketplaces)
- [MCP仕様](https://modelcontextprotocol.io)
- [プラグイン開発ガイド](https://docs.claude.com/en/docs/claude-code/plugins)
- [スキルドキュメント](https://docs.claude.com/en/docs/claude-code/skills)
- [Serena MCP](https://github.com/oraios/serena)

## サポート

マーケットプレイス開発に関する質問：
1. このドキュメントを確認
2. **Serenaメモリーを検索**
3. Claude Codeドキュメントを確認
4. 既存プラグインのパターンを調査
5. 必要に応じてイシューを開く

---

**重要**: このプロジェクトで作業する際は、常にSerena MCPを第一選択肢として考えてください。効率的なコード理解と安全な編集を実現します。

## Serenaメモリー更新履歴

**最終更新日時**: 2025-11-15 (UTC)

**更新内容**:
- プラグイン統合（PR #37）: 3つの個別プラグインを削除し、NDFに統合
- development-history-20251115にプラグイン統合の知見を追記
- plugin-mcp-integration、plugin-slack-notificationメモリーを削除（NDFに統合）
- plugin-ndfメモリーを最新化（v1.0.3、10 MCP servers、5 agents）

**利用可能なメモリー**:
- `plugin-ndf` - NDFプラグインの詳細（v1.0.3、統合版）
- `project-overview` - プロジェクト全体概要
- `development-history-20251115` - 2025-11-12〜2025-11-15の開発履歴と知見（プラグイン統合を含む）

<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
<!-- VERSION: 1 -->
# NDF Plugin - AI Agent Guidelines (Mini)

## Overview

NDF plugin provides **10 MCP servers, 6 commands, and 5 specialized sub-agents**. Delegate complex tasks to appropriate sub-agents for better results.

## Core Policies

### 1. Language
- All responses, documentation, and commit messages must be in **Japanese**.

### 2. Git Restrictions
- **No unauthorized git push/merge**
- **Never push/merge directly to default branch (main/master)**
- Always confirm with user before commit/push/PR merge (except explicit slash commands)
- Use feature branches and create pull requests

## Action Guidelines

### 1. Context Management

**Critical**: Load only necessary information progressively.

- Check symbol overview before reading entire files
- Load only required portions
- Be conscious of token usage

### 2. Sub-Agent Delegation

**Main Agent Responsibilities:**
- **TodoList management**: Track overall task progress
- **Result integration**: Consolidate results from sub-agents
- **Task distribution**: Delegate to appropriate sub-agents

**Core Principle:**
- Delegate complex/specialized tasks to sub-agents
- Main agent handles only simple coordination
- Use specialized agents for data analysis, coding, research, file reading, QA

### 3. Serena MCP Usage

**Use Serena MCP actively** for efficient code exploration and editing.

#### Key Commands

**Read code progressively (not entire files):**
```bash
# 1. Get symbol overview first
mcp__plugin_ndf_serena__get_symbols_overview relative_path="path/to/file.py"

# 2. Find specific symbol
mcp__plugin_ndf_serena__find_symbol name_path="/ClassName" relative_path="src/" include_body=true

# 3. Search pattern if symbol name unknown
mcp__plugin_ndf_serena__search_for_pattern substring_pattern="TODO" relative_path="src/"
```

**Edit code safely:**
```bash
# Replace symbol body (preferred)
mcp__plugin_ndf_serena__replace_symbol_body name_path="/function_name" relative_path="file.py" body="new code"

# Rename across codebase
mcp__plugin_ndf_serena__rename_symbol name_path="/OldName" relative_path="file.py" new_name="NewName"

# Find all references
mcp__plugin_ndf_serena__find_referencing_symbols name_path="function_name" relative_path="source.py"
```

**Use memories:**
```bash
mcp__plugin_ndf_serena__read_memory project-overview.md
mcp__plugin_ndf_serena__write_memory memory_file_name="feature.md" content="..."
```

#### Best Practices

✅ **DO**: Get symbol overview before reading files, use symbol-based editing
❌ **DON'T**: Read entire files, use for binary files (PDF/images)

### 4. Research Facts

**For technically challenging tasks, research external resources instead of guessing.**

- Cloud services (AWS, GCP) → **researcher agent** with AWS Docs MCP
- Latest libraries/frameworks → **corder agent** with Context7 MCP
- Website behavior → **researcher agent** with Chrome DevTools MCP

## Sub-Agent Invocation

Use **Task tool** to invoke sub-agents:

```
Task(
  subagent_type="ndf:corder",          # Agent name (ndf: prefix required)
  prompt="detailed instructions",      # Instructions for agent
  description="Task description"       # 3-5 word description
)
```

**Available subagent_type:**
- `ndf:corder` - Coding expert
- `ndf:data-analyst` - Data analysis expert
- `ndf:researcher` - Research expert
- `ndf:scanner` - File reading expert
- `ndf:qa` - Quality assurance expert

### 5 Specialized Sub-Agents

#### 1. @data-analyst - Data Analysis Expert

**Use Cases:**
- Database queries
- SQL generation/optimization
- Data analysis/statistics
- Save query results to files (CSV/JSON/Excel)

**MCP Tools:** BigQuery MCP

**Example:**
```
User: "Analyze last month's sales data in BigQuery and show top 10 products"

Main Agent: Data analysis task → delegate to ndf:data-analyst

Task(
  subagent_type="ndf:data-analyst",
  prompt="Analyze last month's sales data in BigQuery and extract top 10 products. Use sales_data.transactions dataset.",
  description="Analyze sales data"
)
```

#### 2. @corder - Coding Expert

**Use Cases:**
- Writing new code
- Refactoring existing code
- Code review/security check
- Applying design patterns/architecture
- Checking latest best practices

**MCP Tools:** Codex CLI MCP, Serena MCP, Context7 MCP

**Example:**
```
User: "Implement user authentication feature"

Main Agent: Coding task → delegate to ndf:corder

Task(
  subagent_type="ndf:corder",
  prompt="Implement user authentication feature using JWT. Include login/logout/token refresh endpoints. Follow security best practices and review with Codex.",
  description="Implement user authentication"
)
```

#### 3. @researcher - Research Expert

**Use Cases:**
- Research AWS official documentation
- Collect information from websites
- Investigate technical specifications/best practices
- Research competitor site features
- Capture screenshots/PDFs

**MCP Tools:** AWS Documentation MCP, Chrome DevTools MCP, Codex CLI MCP

**Example:**
```
User: "Research AWS Lambda best practices"

Main Agent: Research task → delegate to ndf:researcher

Task(
  subagent_type="ndf:researcher",
  prompt="Research AWS Lambda best practices. Reference AWS official documentation and summarize from performance optimization, security, and cost reduction perspectives.",
  description="Research AWS Lambda best practices"
)
```

#### 4. @scanner - File Reading Expert

**Use Cases:**
- Reading PDF files
- Extracting text from images (OCR)
- Reading PowerPoint/Excel files
- Describing image content

**MCP Tools:** Codex CLI MCP

**Example:**
```
User: "Read document.pdf and summarize"

Main Agent: File reading task → delegate to ndf:scanner

Task(
  subagent_type="ndf:scanner",
  prompt="Read /path/to/document.pdf and summarize key points in 3-5 items.",
  description="Read and summarize PDF"
)
```

#### 5. @qa - Quality Assurance Expert

**Use Cases:**
- Code quality review
- Security vulnerability check
- Web application performance measurement
- Test coverage verification
- Documentation quality validation
- Claude Code plugin specification compliance check

**MCP Tools:** Codex CLI MCP, Serena MCP, Chrome DevTools MCP

**Examples:**
```
User: "Review this code's quality and security"

Main Agent: QA task → delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Review src/auth.js code. Check code quality (readability, maintainability), security (OWASP Top 10), best practices compliance, and provide improvement suggestions. Perform security scan with Codex.",
  description="Code quality and security review"
)
```

```
User: "Measure web application performance"

Main Agent: Performance test task → delegate to ndf:qa

Task(
  subagent_type="ndf:qa",
  prompt="Measure performance of https://example.com. Evaluate Core Web Vitals (LCP, FID, CLS) with Chrome DevTools, analyze network and rendering performance. Include improvement suggestions if bottlenecks found.",
  description="Performance testing with Chrome DevTools"
)
```

## Task Classification

**Quick Decision Flow:**

1. **Data-related?** (SQL, database, data analysis) → `ndf:data-analyst`
2. **Coding-related?** (implementation, refactoring, review) → `ndf:corder`
3. **Research-related?** (documentation, web scraping) → `ndf:researcher`
4. **File reading?** (PDF, images, Office docs) → `ndf:scanner`
5. **QA-related?** (code review, security, performance) → `ndf:qa`
6. **Simple coordination** → Handle by main agent

## Multi-Agent Collaboration

For complex tasks, use **multiple sub-agents sequentially or in parallel**.

**Example 1: Data Analysis → Reporting**
```
User: "Analyze sales data in BigQuery and create PowerPoint report"

Steps:
1. Task(ndf:data-analyst) for data analysis
2. Main agent receives results
3. Main agent creates PowerPoint
4. Task(ndf:scanner) to verify PowerPoint creation
```

**Example 2: Research → Implementation**
```
User: "Research AWS Lambda best practices and write code based on findings"

Steps:
1. Task(ndf:researcher) to research AWS Lambda best practices
2. Main agent receives research results
3. Task(ndf:corder) to implement code based on best practices
```

**Example 3: PDF Reading → Data Analysis**
```
User: "Read sales data from PDF, import to database, and analyze"

Steps:
1. Task(ndf:scanner) to read PDF and extract data
2. Main agent verifies extracted data
3. Task(ndf:data-analyst) to import to database
4. Task(ndf:data-analyst) to perform data analysis
```

## Best Practices

### DO (Recommended)

✅ **Use specialized agents for each task type**
✅ **Decompose complex tasks and delegate to multiple agents**
✅ **Validate and integrate agent results**
✅ **Start parallel tasks simultaneously when possible**

### DON'T (Not Recommended)

❌ **Handle specialized tasks with main agent** → Delegate to sub-agents
❌ **Respond with guesses without sub-agents** → Research with appropriate agent
❌ **Implement complex code without review** → Delegate to corder with Codex review
❌ **Try to process PDFs/images directly** → Delegate to scanner

## Available MCP Tools (Reference)

Main agent can use these MCPs, but **delegating to specialized agents produces better quality**:

**Core MCPs (frequently used):**
- **Serena MCP**: Code structure understanding, symbol editing
- **GitHub MCP**: PR/issue management, code search
- **Codex CLI MCP**: → **Delegate to @corder or @scanner**
- **Context7 MCP**: Latest library documentation → **Delegate to @corder**

**Specialized MCPs (delegate to agents):**
- **BigQuery MCP**: Database queries → **Delegate to @data-analyst**
- **AWS Docs MCP**: AWS documentation → **Delegate to @researcher**
- **Chrome DevTools MCP**: Web performance/debugging → **Delegate to @researcher or @qa**

## Summary

**Main Agent Role:**
- Overall task management and coordination
- Delegation decisions
- Result integration
- Final reporting to user

**Sub-Agent Role:**
- High-quality execution in specialized domains
- Effective use of specialized MCP tools
- Detailed analysis and implementation

**Success Key:**
Don't try to handle complex tasks alone. **Delegate to appropriate sub-agents** for higher quality and more specialized results.
<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
