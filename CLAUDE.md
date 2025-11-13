# Claude Code AIエージェント ガイドライン

## 目的

このドキュメントは、AI Agent Marketplaceリポジトリと対話するAIエージェント向けのガイドラインを提供します。

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
