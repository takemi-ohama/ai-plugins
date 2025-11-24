# AI Agent Marketplace - 開発ガイドライン

## プロジェクト概要

このリポジトリは**Claude Codeプラグインマーケットプレイス**の開発プロジェクトです。チーム全体でClaude Codeの導入を加速するための事前設定されたプラグインを提供します。

**リポジトリ**: https://github.com/takemi-ohama/ai-agent-marketplace

## 重要な注意事項

### 言語とコミュニケーション
- すべてのAIエージェントとのやり取りは**日本語**で行う
- ドキュメント、コミットメッセージ、PR説明も日本語

### Git運用ルール
- **mainブランチへの直接コミット/プッシュ禁止**
- 必ずfeatureブランチを作成して作業
- Pull Requestを通じてレビュー・マージ
- ユーザーの許可なくPRを承認しない

## マーケットプレイスの構造

### 必須ファイル

```
ai-agent-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイス定義（必須）
├── plugins/
│   ├── ndf/                      # NDFプラグイン
│   └── {plugin-name}/            # その他のプラグイン
├── README.md                     # マーケットプレイス説明
└── CLAUDE.md                     # このファイル
```

### marketplace.json

プラグインマーケットプレイスの中心となる設定ファイル：

```json
{
  "name": "ai-agent-marketplace",
  "owner": {
    "name": "takemi-ohama",
    "url": "https://github.com/takemi-ohama"
  },
  "plugins": [
    {
      "name": "ndf",
      "source": "./plugins/ndf"
    }
  ]
}
```

## プラグイン開発ガイドライン

### 1. プラグイン構造

各プラグインは以下の構造を持ちます：

```
plugins/{plugin-name}/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ（必須）
├── commands/                    # スラッシュコマンド（オプション）
│   └── *.md
├── agents/                      # サブエージェント（オプション）
│   └── *.md
├── skills/                      # プロジェクトスキル（オプション）
│   └── {skill-name}/
│       └── SKILL.md
├── hooks/                       # プロジェクトフック（オプション）
│   └── hooks.json
└── README.md                    # プラグイン説明
```

### 2. plugin.json の作成

**必須フィールド**:
- `name`: プラグイン名（ケバブケース）
- `version`: セマンティックバージョニング（MAJOR.MINOR.PATCH）
- `description`: プラグインの説明
- `author`: 作成者情報

**例**:
```json
{
  "name": "example-plugin",
  "version": "1.0.0",
  "description": "Example plugin for demonstration",
  "author": {
    "name": "Your Name",
    "url": "https://github.com/yourname"
  },
  "keywords": ["example", "demo"],
  "commands": ["./commands/example.md"],
  "agents": ["./agents/example-agent.md"]
}
```

### 3. バージョン管理

**セマンティックバージョニング**:
- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換性のある新機能
- **PATCH**: バグフィックス

**バージョン更新時の手順**:
1. `plugin.json`のバージョンをインクリメント
2. 変更内容をドキュメント化
3. 破壊的変更がある場合は明示
4. テストを実行

### 4. ドキュメント要件

**各プラグインに必要なドキュメント**:
- ✅ README.md: プラグインの概要、インストール方法、使用方法
- ✅ 各機能の説明とサンプルコード
- ✅ トラブルシューティングガイド
- ✅ 必要な環境変数や認証情報の説明

## Serena MCPの活用

このプロジェクトでは**Serena MCP**を積極的に活用してください。

### 基本ワークフロー

#### 1. プロジェクトのアクティベート
```bash
mcp__plugin_ndf_serena__activate_project /home/ubuntu/work/ai-agent-marketplace
mcp__plugin_ndf_serena__check_onboarding_performed
```

#### 2. メモリーの活用
```bash
# メモリー一覧を確認
mcp__plugin_ndf_serena__list_memories

# プロジェクト概要を読む
mcp__plugin_ndf_serena__read_memory project-overview.md

# プラグイン情報を読む
mcp__plugin_ndf_serena__read_memory plugin-ndf.md
```

#### 3. コード探索（ファイル全体を読む前に）
```bash
# ディレクトリ構造を確認
mcp__plugin_ndf_serena__list_dir plugins/ndf recursive=false

# シンボル概要を取得
mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/ndf/.claude-plugin/plugin.json"

# パターン検索
mcp__plugin_ndf_serena__search_for_pattern substring_pattern="version" relative_path="plugins/"
```

#### 4. 編集作業
```bash
# シンボルベース編集（推奨）
mcp__plugin_ndf_serena__replace_symbol_body name_path="/symbol" relative_path="file.md" body="new content"

# メモリー更新
mcp__plugin_ndf_serena__write_memory memory_file_name="plugin-example.md" content="詳細..."
```

## 一般的な開発タスク

### 新しいプラグインの追加

**手順**:

1. **既存プラグインを参考に構造を理解**
   ```bash
   mcp__plugin_ndf_serena__list_dir plugins/ndf recursive=true
   mcp__plugin_ndf_serena__read_memory project-overview.md
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
   mcp__plugin_ndf_serena__read_memory project-overview.md
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
   mcp__plugin_ndf_serena__write_memory memory_file_name="plugin-{name}.md" content="プラグイン情報..."
   ```

9. **コミット＆PR作成**

### 既存プラグインの更新

**手順**:

1. **Serenaメモリーで現在の状態を確認**
   ```bash
   mcp__plugin_ndf_serena__read_memory plugin-{name}.md
   ```

2. **変更対象ファイルの構造を理解**
   ```bash
   mcp__plugin_ndf_serena__get_symbols_overview relative_path="plugins/{name}/file.md"
   ```

3. **変更を実施**
   - Serenaのシンボルベース編集を活用

4. **plugin.jsonのバージョンをインクリメント**

5. **ドキュメント更新**

6. **Serenaメモリーを更新**
   ```bash
   mcp__plugin_ndf_serena__edit_memory memory_file_name="plugin-{name}.md" needle="old" repl="new" mode="literal"
   ```

7. **テスト**

8. **コミット＆PR作成**

## 検証とテスト

### ローカルテスト

```bash
# マーケットプレイス追加
/plugin marketplace add /path/to/ai-agent-marketplace

# プラグインインストール
/plugin install {plugin-name}@ai-agent-marketplace

# プラグイン検証
claude plugin validate
```

### 検証チェックリスト

- [ ] marketplace.jsonが正しい形式
- [ ] 各plugin.jsonが必須フィールドを含む
- [ ] バージョン番号が適切
- [ ] ドキュメントが完全
- [ ] 機密情報が含まれていない
- [ ] プラグインが正常にインストールできる
- [ ] 各機能が動作する

## セキュリティ要件

### 禁止事項

❌ **絶対にコミットしてはいけないもの**:
- APIトークン、パスワード
- 認証情報
- 秘密鍵
- 個人を特定できる情報

### 推奨事項

✅ **実施すべきこと**:
- 認証情報は環境変数で管理
- `.env.example`でテンプレートを提供
- ドキュメントでセキュアな設定方法を説明
- `.gitignore`に機密ファイルを追加

## NDFプラグインについて

**NDFプラグイン**は、このマーケットプレイスの主要プラグインです：
- 10個のMCPサーバー統合
- 6個のスラッシュコマンド
- 6個の専門サブエージェント
- 自動Slack通知

詳細は`plugins/ndf/README.md`を参照してください。

NDFプラグインを使用する場合は、`plugins/ndf/CLAUDE.ndf.md`にある詳細なガイドラインを参照してください。

## ベストプラクティス

### DO（推奨）

✅ Serena MCPを活用してコード構造を理解
✅ ファイル全体を読む前にシンボル概要を取得
✅ 段階的な探索（list_dir → get_symbols_overview → find_symbol）
✅ メモリーを活用してプロジェクト文脈を維持
✅ シンボルベース編集で安全な変更
✅ セマンティックバージョニングに従う
✅ 包括的なドキュメントを提供
✅ 変更前にテスト

### DON'T（非推奨）

❌ ファイル全体を無闇に読み込む
❌ メモリーを確認せずに作業開始
❌ mainブランチに直接コミット
❌ バージョン番号の更新を忘れる
❌ ドキュメントをスキップ
❌ 機密情報をコミット
❌ テストをスキップ

## トラブルシューティング

### よくある問題

**Q: marketplace.jsonが認識されない**
- A: `.claude-plugin/marketplace.json`の配置を確認
- A: JSON形式の検証（`claude plugin validate`）

**Q: プラグインがインストールできない**
- A: plugin.jsonの必須フィールドを確認
- A: パスが正しいか確認（相対パス）

**Q: バージョン更新が反映されない**
- A: plugin.jsonとmarketplace.jsonの両方を更新
- A: Claude Codeを再起動

## 参考リンク

- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
- [プラグインマーケットプレイス](https://code.claude.com/docs/ja/plugin-marketplaces)
- [プラグインスキル](https://docs.claude.com/en/docs/claude-code/skills)
- [MCP仕様](https://modelcontextprotocol.io)

## NDFプラグインガイドライン

NDFプラグインを使用する際の詳細なガイドラインは、以下のファイルに記載されています：

@plugins/ndf/CLAUDE.ndf.md
