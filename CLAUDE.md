# AI Plugins - Claude Code開発ガイドライン

## 基本ガイドライン

プロジェクトの基本的な開発ガイドラインは **@AGENTS.md** を参照してください。

このファイルには、Claude Code固有の機能（Serena MCP）に関する情報のみを記載します。

## Serena MCPの活用（Claude Code固有）

このプロジェクトでは**Serena MCP**（NDFプラグインに統合）を積極的に活用してください。

> **Note (v2.6.0)**: Serena MCPはNDFプラグインのコアMCPです。GOOGLE_API_KEY、ANTHROPIC_API_KEYは不要（Claude Codeの設定を自動継承）。

### 基本ワークフロー

#### 1. プロジェクトのアクティベート
```bash
mcp__plugin_serena_serena__activate_project /work/ai-plugins
mcp__plugin_serena_serena__check_onboarding_performed
```

#### 2. メモリーの活用
```bash
# メモリー一覧を確認
mcp__plugin_serena_serena__list_memories

# プロジェクト概要を読む
mcp__plugin_serena_serena__read_memory project-overview.md

# プラグイン情報を読む
mcp__plugin_serena_serena__read_memory plugin-ndf.md
```

#### 3. コード探索（ファイル全体を読む前に）
```bash
# ディレクトリ構造を確認
mcp__plugin_serena_serena__list_dir plugins/ndf recursive=false

# シンボル概要を取得
mcp__plugin_serena_serena__get_symbols_overview relative_path="plugins/ndf/.claude-plugin/plugin.json"

# パターン検索
mcp__plugin_serena_serena__search_for_pattern substring_pattern="version" relative_path="plugins/"
```

#### 4. 編集作業
```bash
# シンボルベース編集（推奨）
mcp__plugin_serena_serena__replace_symbol_body name_path="/symbol" relative_path="file.md" body="new content"

# メモリー更新
mcp__plugin_serena_serena__write_memory memory_file_name="plugin-example.md" content="詳細..."
```

## 一般的な開発タスク（Serena MCP活用）

基本的な開発タスクの手順は **@AGENTS.md** を参照してください。

以下はClaude CodeでSerena MCPを活用する場合の追加手順です。

### 新しいプラグインの追加

**手順**:

1. **既存プラグインを参考に構造を理解**
   ```bash
   mcp__plugin_serena_serena__list_dir plugins/ndf recursive=true
   mcp__plugin_serena_serena__read_memory project-overview.md
   ```

2. **ディレクトリ構造を作成**
   ```bash
   mkdir -p plugins/{plugin-name}/{.claude-plugin,commands,agents,skills}
   ```

3. **plugin.jsonを作成**
   - 必須フィールドをすべて含める
   - セマンティックバージョニングに従う

4. **プラグインコンテンツを実装**
   - スキル、コマンド、エージェントを追加

5. **marketplace.jsonに登録**
   ```bash
   # Serenaで既存の設定を確認
   mcp__plugin_serena_serena__read_memory project-overview.md
   ```

6. **ドキュメント作成**
   - README.md
   - 使用例
   - トラブルシューティング

7. **テスト**
   ```bash
   claude plugin validate
   ```

8. **Serenaメモリーに記録**
   ```bash
   mcp__plugin_serena_serena__write_memory memory_file_name="plugin-{name}.md" content="プラグイン情報..."
   ```

9. **コミット＆PR作成**

### 既存プラグインの更新

**手順**:

1. **Serenaメモリーで現在の状態を確認**
   ```bash
   mcp__plugin_serena_serena__read_memory plugin-{name}.md
   ```

2. **変更対象ファイルの構造を理解**
   ```bash
   mcp__plugin_serena_serena__get_symbols_overview relative_path="plugins/{name}/file.md"
   ```

3. **変更を実施**
   - Serenaのシンボルベース編集を活用

4. **plugin.jsonのバージョンをインクリメント**

5. **ドキュメント更新**

6. **Serenaメモリーを更新**
   ```bash
   mcp__plugin_serena_serena__edit_memory memory_file_name="plugin-{name}.md" needle="old" repl="new" mode="literal"
   ```

7. **テスト**

8. **コミット＆PR作成**

## 検証とテスト

検証とテストの詳細は **@AGENTS.md** を参照してください。

### Claude Code固有の検証

```bash
# プラグイン検証
claude plugin validate
```

## NDFプラグインガイドライン

NDFプラグインの詳細は **@AGENTS.md** を参照してください。

NDFプラグインを使用する際の詳細なガイドラインは、以下のファイルに記載されています：

@plugins/ndf/CLAUDE.ndf.md
@CLAUDE.ndf.md

## ベストプラクティス（Serena MCP）

基本的なベストプラクティスは **@AGENTS.md** を参照してください。

### Claude Code + Serena MCP固有

✅ Serena MCPを活用してコード構造を理解
✅ ファイル全体を読む前にシンボル概要を取得
✅ 段階的な探索（list_dir → get_symbols_overview → find_symbol）
✅ メモリーを活用してプロジェクト文脈を維持
✅ シンボルベース編集で安全な変更

❌ ファイル全体を無闇に読み込む
❌ メモリーを確認せずに作業開始

## 参考リンク

基本的な参考リンクは **@AGENTS.md** を参照してください。

## Serena MCPメモリー管理

### 記憶更新日時
**最終更新**: 2026-01-18

### 利用可能なメモリー
- `project-overview` - プロジェクト概要
- `plugin-ndf` - NDFプラグイン詳細情報
- `development-history-20251115` - 開発履歴（2025-11-15）
- `development-history-20260118` - 開発履歴（2026-01-18）

### メモリー活用方法
```bash
# メモリー一覧を確認
mcp__plugin_serena_serena__list_memories

# プロジェクト概要を読む
mcp__plugin_serena_serena__read_memory project-overview.md

# NDFプラグイン情報を読む
mcp__plugin_serena_serena__read_memory plugin-ndf.md

# 開発履歴（最新）を読む
mcp__plugin_serena_serena__read_memory development-history-20260118.md
```
