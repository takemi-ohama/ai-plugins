# AI Plugins プロジェクト概要

## プロジェクトの目的

Claude Codeプラグインマーケットプレイス（内部用）として、チーム全体でClaude Codeの導入を加速するための事前設定されたプラグインを提供する。

## リポジトリ情報

- **リポジトリ名**: ai-plugins
- **オーナー**: takemi-ohama
- **ライセンス**: MIT
- **マーケットプレイスURL**: https://github.com/takemi-ohama/ai-plugins

## 配布コンポーネント

1. **MCPインテグレーションスキル**: GitHub、Serena、BigQuery、Notion MCPの自動セットアップ
2. **カスタムスラッシュコマンド**: 共通タスク用の再利用可能なスラッシュコマンド
3. **サブエージェント**: 異なるドメイン向けの専門AIエージェント
4. **プロジェクトフック**: イベントによってトリガーされる自動ワークフロー

## ディレクトリ構造

```
ai-plugins/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイスメタデータ
├── plugins/
│   ├── mcp-integration/          # MCPセットアップスキル
│   └── slack-notification/       # Slack通知フック
├── README.md                     # プロジェクトドキュメント
├── CLAUDE.md                     # AIエージェント向けガイドライン
└── LICENSE                       # MITライセンス
```

## 現在提供されているプラグイン

### 1. ndf (v2.1.3) ⭐ オールインワン
- **説明**: 専門エージェント、ワークフローコマンド、Slack通知を統合したプラグイン
- **タイプ**: 複合プラグイン（MCPサーバー + フック + コマンド + エージェント + スキル）
- **パス**: `./plugins/ndf`
- **含まれる機能**:
  - 7つのMCPサーバー（BigQuery、Notion、AWS Docs、DBHub、Chrome DevTools、Codex、Playwright）
  - 6つのスラッシュコマンド（/ndf:serena、/ndf:pr、/ndf:fix、/ndf:review、/ndf:merge、/ndf:clean）
  - 6つの専門エージェント（director、data-analyst、corder、researcher、scanner、qa）
  - 8つのClaude Code Skills
  - 自動Slack通知（Stop hookによる作業要約送信）
- **注意**: GitHub MCP、Serena MCP、Context7 MCPは公式プラグインに移行済み

### 2. mcp-integration (v2.0.0)
- **説明**: MCPサーバーの統合設定（単体利用可能）
- **タイプ**: プロジェクトスキル
- **パス**: `./plugins/mcp-integration`
- **注意**: NDFプラグインに含まれているため、単体インストールは非推奨

### 3. slack-notification (v2.0.0)
- **説明**: Claude Code作業完了時の自動Slack通知（日本語要約付き）
- **タイプ**: プロジェクトスキル + フック
- **パス**: `./plugins/slack-notification`
- **注意**: NDFプラグインに含まれているため、単体インストールは非推奨

### 4. workflow-commands (v1.0.0)
- **説明**: 開発ワークフロー用スラッシュコマンド
- **タイプ**: スラッシュコマンド
- **パス**: `./plugins/workflow-commands`
- **注意**: NDFプラグインに含まれているため、単体インストールは非推奨

**推奨**: ほとんどのユーザーは**NDFプラグイン**を使用することを推奨。個別プラグインは特定機能のみ必要な場合に使用。

## インストール方法

### マーケットプレイスの追加
```bash
/plugin marketplace add
# URL: https://github.com/takemi-ohama/ai-plugins
```

### プラグインのインストール
```bash
/plugin install mcp-integration@ai-plugins
/plugin install slack-notification@ai-plugins
```

## プラグイン開発ガイドライン

### 必須ファイル

1. **plugin.json**: プラグインメタデータ（name, version, description, author）
2. **SKILL.md**: プロジェクトスキルのエントリポイント（YAMLフロントマター必須）

### セマンティックバージョニング

- **MAJOR**: 破壊的変更
- **MINOR**: 後方互換性のある新機能
- **PATCH**: バグフィックス

### セキュリティ要件

- トークンや認証情報をコミットしない
- 環境変数を使用
- `.env`を`.gitignore`に追加
- テンプレートではプレースホルダー値を使用

## 管理タスク

### プラグインの追加
1. プラグインディレクトリ作成
2. plugin.json作成
3. コンテンツ追加（skills/commands/agents）
4. marketplace.jsonに登録
5. ドキュメント作成
6. テスト実行

### プラグインの更新
1. ファイル修正
2. plugin.jsonのバージョンインクリメント
3. コミット＆プッシュ

### プラグインの削除
1. marketplace.jsonから削除
2. プラグインディレクトリ削除（オプション）
3. コミット

## 参考リンク

- [Claude Codeドキュメント](https://docs.claude.com/en/docs/claude-code)
- [プラグインマーケットプレイスドキュメント](https://code.claude.com/docs/ja/plugin-marketplaces)
- [MCP仕様](https://modelcontextprotocol.io)
- [スキルドキュメント](https://docs.claude.com/en/docs/claude-code/skills)
