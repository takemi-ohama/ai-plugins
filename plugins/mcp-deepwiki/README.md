# DeepWiki MCP

リポジトリのドキュメントとコード知識にアクセスするためのMCPサーバープラグインです。

## 概要

このプラグインは、[DeepWiki](https://deepwiki.com)のMCPサーバーを利用して、GitHubなどのリポジトリのドキュメント構造や内容をAIエージェントから直接参照できるようにします。パブリックリポジトリは認証不要で無料で利用できます。プライベートリポジトリにはDevin APIキーが必要です。

## 機能

- **`read_wiki_structure`** - リポジトリのドキュメントトピック一覧を取得
- **`read_wiki_contents`** - ドキュメントの内容を閲覧
- **`ask_question`** - リポジトリに関するAI質問回答

## 前提条件

- パブリックリポジトリ: なし（認証不要）
- プライベートリポジトリ: Devin APIキー（環境変数 `DEVIN_API_KEY`）

## 環境変数の設定

プライベートリポジトリにアクセスする場合、プロジェクトルートの`.env`ファイルに以下を設定してください：

```bash
# Devin API Key（プライベートリポジトリアクセス用）
DEVIN_API_KEY=your-devin-api-key
```

パブリックリポジトリのみ利用する場合、環境変数の設定は不要です。

## インストール

```bash
/plugin install mcp-deepwiki@ai-plugins
```

## 使用方法

### 基本的な使用例

```bash
# リポジトリのドキュメント構造を取得
mcp__plugin_mcp-deepwiki__deepwiki__read_wiki_structure "owner/repo"

# ドキュメント内容を読み取り
mcp__plugin_mcp-deepwiki__deepwiki__read_wiki_contents "owner/repo" "topic"

# リポジトリについて質問
mcp__plugin_mcp-deepwiki__deepwiki__ask_question "owner/repo" "How does authentication work?"
```

### CLIで直接追加する場合

```bash
claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp
```

## 推奨される使用シーン

- OSSライブラリの仕様・アーキテクチャ調査
- 依存パッケージの内部実装の理解
- リポジトリのドキュメント横断検索
- 技術選定時のコード比較調査

## NDFエージェントとの連携

DeepWiki MCPは、NDFプラグインの`ndf:researcher`エージェントと連携して使用することを推奨します。

```bash
Task(
  subagent_type="ndf:researcher",
  prompt="DeepWikiを使ってlangchain/langchainリポジトリのRAG実装を調査してください",
  description="Research RAG implementation"
)
```

## 注意事項

- パブリックリポジトリは認証不要で利用可能
- プライベートリポジトリは `DEVIN_API_KEY` が必要（`/ndf:deepwiki-transfer` スキルの `fetch_wiki.py` 経由で利用）
- HTTPトランスポートを使用しています（Devin公式のDeepWiki MCPサーバー）
- レート制限がある場合があります

## 参考リンク

- [DeepWiki](https://deepwiki.com)
- [DeepWiki MCP ドキュメント](https://docs.devin.ai/ja/work-with-devin/deepwiki-mcp)
