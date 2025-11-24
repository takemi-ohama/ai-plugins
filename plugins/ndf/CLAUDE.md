# NDF Plugin - 開発者向けガイドライン

## 概要

このドキュメントは、**NDFプラグインの開発・メンテナンス**を行うAIエージェント向けのガイドラインです。

**プラグイン利用者向けガイドライン**は`CLAUDE.ndf.md`を参照してください。

## プラグイン情報

- **名前**: ndf
- **現在バージョン**: 1.0.6
- **種類**: 統合プラグイン（MCP + Commands + Agents + Hooks）
- **リポジトリ**: https://github.com/takemi-ohama/ai-agent-marketplace

## 重要な開発ルール

### 言語
- すべてのドキュメント、コミットメッセージ、PR説明は**日本語**

### Git運用
- **mainブランチへの直接コミット禁止**
- featureブランチで作業し、PRを通じてマージ
- ユーザーの許可なくPRを承認しない

### バージョン管理
- **セマンティックバージョニング**（MAJOR.MINOR.PATCH）に厳密に従う
- 変更内容に応じて適切なバージョンをインクリメント
  - **MAJOR**: 破壊的変更
  - **MINOR**: 後方互換性のある新機能
  - **PATCH**: バグフィックス

## ディレクトリ構造

```
plugins/ndf/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ（必須）
├── .mcp.json                    # MCPサーバー定義
├── hooks/
│   └── hooks.json               # プロジェクトフック定義
├── scripts/
│   ├── slack-notify.js          # Slack通知スクリプト
│   └── inject-plugin-guide.js   # SessionStartフック用スクリプト
├── commands/                    # スラッシュコマンド（6個）
│   ├── serena.md
│   ├── pr.md
│   ├── fix.md
│   ├── review.md
│   ├── merged.md
│   └── clean.md
├── agents/                      # サブエージェント（6個）
│   ├── director.md
│   ├── data-analyst.md
│   ├── corder.md
│   ├── researcher.md
│   ├── scanner.md
│   └── qa.md
├── CLAUDE.md                    # このファイル（開発者向け）
├── CLAUDE.ndf.md                # プラグイン利用者向けガイドライン
└── README.md                    # プラグイン説明書
```

## Serena MCPの活用

### プロジェクトアクティベート

```bash
# プロジェクトをアクティベート
mcp__plugin_ndf_serena__activate_project /home/ubuntu/work/ai-agent-marketplace

# オンボーディング確認
mcp__plugin_ndf_serena__check_onboarding_performed
```

### メモリーの活用

```bash
# NDFプラグイン情報を読む
mcp__plugin_ndf_serena__read_memory plugin-ndf.md

# プロジェクト概要を読む
mcp__plugin_ndf_serena__read_memory project-overview.md
```

### コード探索（ファイル全体を読む前に）

```bash
# ディレクトリ構造を確認
mcp__plugin_ndf_serena__list_dir plugins/ndf recursive=false

# plugin.jsonの構造を理解
mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/ndf/.claude-plugin/plugin.json"

# エージェント一覧を確認
mcp__plugin_ndf_serena__list_dir plugins/ndf/agents recursive=false
```

## 一般的な開発タスク

### 1. 新しいサブエージェントの追加

**手順**:

1. **既存エージェントを参考に理解**
   ```bash
   mcp__plugin_ndf_serena__list_dir plugins/ndf/agents recursive=false
   mcp__plugin_ndf_serena__read_memory plugin-ndf.md
   ```

2. **エージェントファイルを作成**
   ```bash
   # YAMLフロントマター必須
   # - name: エージェント名
   # - description: 簡潔な説明
   ```

3. **plugin.jsonに登録**
   ```bash
   # Serenaで既存のagents配列を確認
   mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/ndf/.claude-plugin/plugin.json"
   ```

4. **CLAUDE.ndf.mdに説明を追加**
   - Available subagent_type
   - Specialized Sub-Agents セクション
   - 使用例

5. **plugin.jsonのバージョンをインクリメント**
   - MINOR版を上げる（新機能）

6. **Serenaメモリーを更新**
   ```bash
   mcp__plugin_ndf_serena__edit_memory memory_file_name="plugin-ndf.md" needle="専門エージェント (X種類)" repl="専門エージェント (Y種類)" mode="literal"
   ```

7. **テストとコミット**

### 2. 新しいスラッシュコマンドの追加

**手順**:

1. **既存コマンドを参考に理解**
   ```bash
   mcp__plugin_ndf_serena__list_dir plugins/ndf/commands recursive=false
   ```

2. **コマンドファイルを作成**
   - `commands/{command-name}.md`
   - マークダウン形式でコマンド説明を記述

3. **plugin.jsonに登録**
   ```json
   {
     "commands": [
       "./commands/existing.md",
       "./commands/new-command.md"
     ]
   }
   ```

4. **README.mdに説明を追加**

5. **plugin.jsonのバージョンをインクリメント**
   - MINOR版を上げる

6. **Serenaメモリーを更新**

7. **テストとコミット**

### 3. MCPサーバーの追加・更新

**手順**:

1. **既存の.mcp.jsonを確認**
   ```bash
   mcp__plugin_ndf_serena__read_memory plugin-ndf.md
   ```

2. **.mcp.jsonに新しいMCPサーバーを追加**
   - `mcpServers`オブジェクトに追加
   - `command`または`url`を指定
   - 環境変数が必要な場合は`env`を設定

3. **README.mdに説明を追加**
   - MCPサーバー一覧
   - 認証方法
   - 使用例

4. **環境変数ドキュメントを更新**
   - 必要な環境変数を明記
   - セットアップ手順を提供

5. **plugin.jsonのバージョンをインクリメント**
   - MINOR版を上げる（新MCP追加の場合）
   - PATCH版を上げる（既存MCPの修正）

6. **Serenaメモリーを更新**

7. **テストとコミット**

### 4. フックの追加・更新

**手順**:

1. **hooks/hooks.jsonを確認**
   ```bash
   mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/ndf/hooks/hooks.json"
   ```

2. **フックを追加・修正**
   - SessionStart, Stop, UserPromptSubmitなどのイベント
   - command型またはprompt型

3. **スクリプトファイルを作成（command型の場合）**
   - `scripts/`ディレクトリに配置
   - 環境変数`CLAUDE_PLUGIN_ROOT`を活用

4. **README.mdに説明を追加**

5. **plugin.jsonのバージョンをインクリメント**
   - MINOR版を上げる（新フック）
   - PATCH版を上げる（既存フックの修正）

6. **テストとコミット**

### 5. CLAUDE.ndf.mdの更新

**CLAUDE.ndf.mdは利用者向けガイドライン**のため、以下の場合に更新：

- サブエージェントの追加・変更
- 使用方法の変更
- 新機能の追加
- ベストプラクティスの更新

**手順**:

1. **構造を理解**
   ```bash
   mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/ndf/CLAUDE.ndf.md"
   ```

2. **該当セクションを更新**
   - Overview
   - Available subagent_type
   - Specialized Sub-Agents
   - Task Classification
   - Multi-Agent Collaboration
   - Summary

3. **バージョンコメントを更新**
   ```markdown
   <!-- VERSION: 2 -->
   ```

4. **plugin.jsonのバージョンをインクリメント**
   - MINOR版を上げる（機能追加・変更）
   - PATCH版を上げる（ドキュメント修正のみ）

5. **Serenaメモリーを更新**

6. **コミット**

## plugin.jsonの管理

### 必須フィールド

```json
{
  "name": "ndf",
  "version": "1.0.6",
  "description": "Integrated plugin combining MCP servers, development workflow commands, specialized agents, and Slack notifications",
  "author": {
    "name": "takemi-ohama",
    "url": "https://github.com/takemi-ohama"
  },
  "keywords": ["mcp", "github", "serena", ...],
  "commands": ["./commands/serena.md", ...],
  "agents": ["./agents/director.md", ...]
}
```

### バージョン更新ルール

**MAJOR（破壊的変更）**:
- APIの非互換変更
- 既存機能の削除
- 設定ファイル形式の変更

**MINOR（新機能）**:
- 新しいサブエージェントの追加
- 新しいコマンドの追加
- 新しいMCPサーバーの追加
- 後方互換性のある機能追加

**PATCH（バグフィックス）**:
- バグ修正
- ドキュメント修正
- 既存機能の改善（動作変更なし）

### バージョン更新手順

1. **plugin.jsonのversionフィールドを更新**

2. **関連ドキュメントのバージョン参照を更新**
   - README.md
   - CLAUDE.ndf.md

3. **Serenaメモリーを更新**
   ```bash
   mcp__plugin_ndf_serena__edit_memory memory_file_name="plugin-ndf.md" needle="**バージョン:** 1.0.X" repl="**バージョン:** 1.0.Y" mode="literal"
   ```

4. **コミット**

## Serenaメモリーの管理

### メモリーファイル: plugin-ndf.md

**含まれる情報**:
- プラグイン概要
- バージョン情報
- 重要な変更履歴
- ディレクトリ構造
- 機能一覧（MCP、コマンド、エージェント、フック）
- 環境変数
- トラブルシューティング
- 設計の利点

### メモリー更新のタイミング

- サブエージェント追加・削除
- コマンド追加・削除
- MCPサーバー追加・削除
- バージョン更新
- 重要な設計変更

### メモリー更新方法

```bash
# 部分的な更新（推奨）
mcp__plugin_ndf_serena__edit_memory \
  memory_file_name="plugin-ndf.md" \
  needle="old text" \
  repl="new text" \
  mode="literal"

# 全体の再作成（大規模変更時）
mcp__plugin_ndf_serena__write_memory \
  memory_file_name="plugin-ndf.md" \
  content="完全な新しい内容"
```

## テストとデバッグ

### ローカルテスト

```bash
# マーケットプレイスを追加（ローカルパス）
/plugin marketplace add /home/ubuntu/work/ai-agent-marketplace

# プラグインをインストール
/plugin install ndf@ai-agent-marketplace

# プラグインを再読み込み（開発中）
/plugin reload ndf

# エージェントが認識されているか確認
/help agents

# コマンドが認識されているか確認
/help commands
```

### 検証チェックリスト

- [ ] plugin.jsonが有効なJSON形式
- [ ] バージョン番号が適切にインクリメントされている
- [ ] すべてのコマンドファイルが存在する
- [ ] すべてのエージェントファイルが存在する
- [ ] YAMLフロントマターが正しい
- [ ] .mcp.jsonが有効なJSON形式
- [ ] 環境変数のドキュメントが完全
- [ ] README.mdが最新
- [ ] CLAUDE.ndf.mdが最新
- [ ] Serenaメモリーが更新されている

## トラブルシューティング

### よくある問題

**Q: エージェントが認識されない**
- A: plugin.jsonのagents配列を確認
- A: ファイルパスが正しいか確認（相対パス）
- A: YAMLフロントマターの構文を確認

**Q: コマンドが表示されない**
- A: plugin.jsonのcommands配列を確認
- A: ファイルパスが正しいか確認
- A: プラグインを再読み込み（/plugin reload ndf）

**Q: MCPサーバーが起動しない**
- A: .mcp.jsonの構文を確認
- A: コマンドパスが正しいか確認
- A: 環境変数が設定されているか確認
- A: Claude Codeを再起動

**Q: フックが動作しない**
- A: hooks/hooks.jsonの構文を確認
- A: スクリプトの実行権限を確認
- A: CLAUDE_PLUGIN_ROOT環境変数を確認

## ベストプラクティス

### DO（推奨）

✅ **変更前にSerenaメモリーで現状を確認**
✅ **Serenaで構造を理解してから編集**
✅ **セマンティックバージョニングに厳密に従う**
✅ **すべての変更をドキュメント化**
✅ **Serenaメモリーを必ず更新**
✅ **変更後にローカルテスト**
✅ **PRの説明を詳細に記述**

### DON'T（非推奨）

❌ **メモリーを確認せずに変更開始**
❌ **ファイル全体を無闇に読み込む**
❌ **バージョン更新を忘れる**
❌ **ドキュメント更新をスキップ**
❌ **Serenaメモリー更新をスキップ**
❌ **テストをスキップ**
❌ **mainブランチに直接コミット**

## セキュリティ

### 禁止事項

❌ **絶対にコミットしてはいけないもの**:
- APIトークン、パスワード
- SLACK_BOT_TOKEN、GITHUB_PERSONAL_ACCESS_TOKEN等の実際の値
- 認証情報
- 秘密鍵

### 推奨事項

✅ **実施すべきこと**:
- 環境変数で認証情報を管理
- ドキュメントで環境変数の設定方法を説明
- テンプレートには`your-token-here`等のプレースホルダーを使用
- .gitignoreに.envファイルを追加

## 参考リンク

- [Claude Codeプラグイン開発](https://docs.claude.com/en/docs/claude-code)
- [プラグインマーケットプレイス](https://code.claude.com/docs/ja/plugin-marketplaces)
- [MCP仕様](https://modelcontextprotocol.io)
- [Serena MCP](https://github.com/oraios/serena)

## 開発履歴

### v1.0.6 (最新)
- directorサブエージェント追加
- Main Agent責務をdirectorに移譲
- CLAUDE_plugin.md → CLAUDE.ndf.mdにリネーム

### v1.0.5
- 細かいバグフィックスとドキュメント改善

### v1.0.1
- 3つのプラグインを統合（mcp-integration、install-slack-hook、workflow-commands）
- マーケットプレイスをNDF単一プラグインに整理

### v1.0.0
- 初期リリース
