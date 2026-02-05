# AI Plugins - Kiro CLI開発ガイドライン

## プロジェクト概要

このリポジトリは**Claude Codeプラグインマーケットプレイス**の開発プロジェクトです。チーム全体でClaude Codeの導入を加速するための事前設定されたプラグインを提供します。

**リポジトリ**: https://github.com/takemi-ohama/ai-plugins

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
ai-plugins/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイス定義（必須）
├── plugins/
│   ├── ndf/                      # NDFプラグイン
│   └── {plugin-name}/            # その他のプラグイン
├── README.md                     # マーケットプレイス説明
├── CLAUDE.md                     # Claude Code用ガイドライン
└── KIRO.md                       # このファイル（Kiro CLI用）
```

### marketplace.json

プラグインマーケットプレイスの中心となる設定ファイル：

```json
{
  "name": "ai-plugins",
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

## Kiro CLIでのコード探索

### 基本ワークフロー

#### 1. プロジェクト構造の把握
```bash
# ディレクトリ構造を確認
ls -la plugins/

# 特定のプラグインディレクトリを確認
ls -la plugins/ndf/
```

#### 2. コードインテリジェンスの活用

**シンボル検索**:
```
# プラグイン名でシンボルを検索
code search_symbols "ndf"

# 特定のファイル内のシンボル一覧
code get_document_symbols plugins/ndf/.claude-plugin/plugin.json
```

**パターン検索**:
```
# バージョン情報を検索
grep "version" --include="*.json"

# 特定のキーワードを検索
grep "MCP" --include="*.md"
```

#### 3. ファイル読み取り

**効率的な読み取り**:
```
# ファイル全体を読む
fs_read plugins/ndf/.claude-plugin/plugin.json

# 特定の行範囲を読む
fs_read plugins/ndf/README.md --start_line=1 --end_line=50
```

## 一般的な開発タスク

### 新しいプラグインの追加

**手順**:

1. **既存プラグインを参考に構造を理解**
   ```bash
   ls -la plugins/ndf/
   cat plugins/ndf/.claude-plugin/plugin.json
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
   # 既存の設定を確認
   cat .claude-plugin/marketplace.json
   ```

6. **ドキュメント作成**
   - README.md
   - 使用例
   - トラブルシューティング

7. **テスト**
   - ローカルでプラグインをテスト

8. **コミット＆PR作成**
   ```bash
   git checkout -b feature/add-{plugin-name}
   git add .
   git commit -m "Add {plugin-name} plugin"
   git push origin feature/add-{plugin-name}
   ```

### 既存プラグインの更新

**手順**:

1. **現在の状態を確認**
   ```bash
   cat plugins/{name}/.claude-plugin/plugin.json
   cat plugins/{name}/README.md
   ```

2. **変更対象ファイルの構造を理解**
   ```bash
   code get_document_symbols plugins/{name}/file.md
   ```

3. **変更を実施**
   - ファイル編集ツールを使用

4. **plugin.jsonのバージョンをインクリメント**

5. **ドキュメント更新**

6. **テスト**

7. **コミット＆PR作成**

## 検証とテスト

### ローカルテスト

```bash
# マーケットプレイス追加（Claude Codeで）
/plugin marketplace add /path/to/ai-plugins

# プラグインインストール
/plugin install {plugin-name}@ai-plugins
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

## ベストプラクティス

### DO（推奨）

✅ コードインテリジェンスツールを活用してコード構造を理解
✅ ファイル全体を読む前にシンボル概要を取得
✅ 段階的な探索（ls → get_document_symbols → fs_read）
✅ セマンティックバージョニングに従う
✅ 包括的なドキュメントを提供
✅ 変更前にテスト
✅ featureブランチで作業
✅ PRを通じてマージ

### DON'T（非推奨）

❌ ファイル全体を無闇に読み込む
❌ mainブランチに直接コミット
❌ バージョン番号の更新を忘れる
❌ ドキュメントをスキップ
❌ 機密情報をコミット
❌ テストをスキップ
❌ ユーザーの許可なくPRを承認

## トラブルシューティング

### よくある問題

**Q: marketplace.jsonが認識されない**
- A: `.claude-plugin/marketplace.json`の配置を確認
- A: JSON形式の検証

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

## Git運用フロー

### ブランチ戦略

```bash
# 新機能開発
git checkout -b feature/{feature-name}

# バグ修正
git checkout -b fix/{bug-name}

# ドキュメント更新
git checkout -b docs/{doc-name}
```

### コミットメッセージ

日本語で明確に記述：

```
Add: 新機能追加
Update: 既存機能の更新
Fix: バグ修正
Docs: ドキュメント更新
Refactor: リファクタリング
Test: テスト追加・修正
```

### PR作成

1. featureブランチで作業完了
2. 変更をコミット
3. リモートにプッシュ
4. GitHubでPR作成
5. レビュー依頼
6. ユーザーの承認後にマージ

## Kiro CLI特有の注意事項

### サブエージェントの活用

複雑なタスクは専門のサブエージェントに委譲：

```
# 複数の独立したタスクを並列実行
use_subagent InvokeSubagents
```

### LSP統合

コードインテリジェンスを最大限活用：

```bash
# プロジェクトルートでLSP初期化（必要に応じて）
/code init
```

### AWS統合

AWS CLIを使用してリソース管理：

```bash
# S3バケット一覧
use_aws s3 list-buckets

# Lambda関数一覧
use_aws lambda list-functions
```

## 最小限のコード実装

**重要**: コード実装時は以下を厳守：
- 要件を満たす最小限のコードのみを記述
- 冗長な実装を避ける
- ソリューションに直接貢献しないコードは書かない
- シンプルで明確な実装を優先

## まとめ

このガイドラインに従って、効率的かつ安全にai-pluginsプロジェクトの開発を進めてください。不明点があれば、既存のドキュメントやコードを参照し、必要に応じてユーザーに確認してください。
