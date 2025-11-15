# NDF Plugin - AIエージェント向けガイドライン

## 概要

このドキュメントは、NDFプラグインを使用するAIエージェント（メインエージェント）向けのガイドラインです。

NDFプラグインは**10個のMCPサーバー、6つのコマンド、4つの専門サブエージェント**を提供します。タスクに応じて**適切なサブエージェントに委譲する**ことで、より高品質な結果を得られます。

## サブエージェントの積極的な活用

### 基本方針

**重要**: 複雑なタスクや専門性の高いタスクは、**必ず専門サブエージェントに委譲**してください。

メインエージェント（あなた）は全体の調整役として：
1. **タスクの分類**: ユーザーの要求を分析し、適切なサブエージェントを判断
2. **エージェント起動**: Taskツールで`subagent_type="ndf:agent-name"`を指定して起動
3. **結果の統合**: 複数のサブエージェントの結果を統合して報告
4. **品質確認**: サブエージェントの出力を検証

### サブエージェントの呼び出し方法

**Taskツールを使用**してサブエージェントを呼び出します：

```
Task(
  subagent_type="ndf:corder",           # エージェント名（ndf:プレフィックス必須）
  prompt="実装してほしい内容の詳細",    # エージェントへの指示
  description="Task description"        # 3-5語の説明
)
```

**利用可能なsubagent_type:**
- `ndf:corder` - コーディング専門家
- `ndf:data-analyst` - データ分析専門家
- `ndf:researcher` - 調査専門家
- `ndf:scanner` - ファイル読み取り専門家
- `ndf:memory-recorder` - Serenaメモリー記録専門家
- `ndf:slack-notifier` - Slack通知専門家

### 4つの専門サブエージェント

#### 1. @data-analyst - データ分析の専門家

**活用すべき場面:**
- データベースへのクエリ実行が必要な時
- SQLの生成や最適化が必要な時
- データの分析や統計処理が必要な時
- クエリ結果をファイル（CSV/JSON/Excel）に保存する時

**使用MCPツール:**
- BigQuery MCP
- DBHub MCP

**活用例:**
```
ユーザー: 「BigQueryで過去1ヶ月の売上データを分析して、トップ10の商品を教えて」

メインエージェントの判断: データ分析タスク → ndf:data-analyst に委譲

Task(
  subagent_type="ndf:data-analyst",
  prompt="BigQueryで過去1ヶ月の売上データを分析して、トップ10の商品を抽出してください。データセットは sales_data.transactions を使用してください。",
  description="Analyze sales data"
)
```

**NGパターン（やってはいけない）:**
- メインエージェント自身がSQLを書こうとする
- データ分析の専門知識がない状態で解釈を試みる

#### 2. @corder - コーディングの専門家

**活用すべき場面:**
- 新しいコードを書く時
- 既存コードをリファクタリングする時
- コードレビューやセキュリティチェックが必要な時
- 設計パターンやアーキテクチャの適用が必要な時
- 最新のベストプラクティスを確認したい時

**使用MCPツール:**
- Codex CLI MCP（AIコードレビュー）
- Serena MCP（コード構造理解）
- Context7 MCP（最新情報）

**活用例:**
```
ユーザー: 「ユーザー認証機能を実装してください」

メインエージェントの判断: コーディングタスク → ndf:corder に委譲

Task(
  subagent_type="ndf:corder",
  prompt="ユーザー認証機能を実装してください。JWT認証を使用し、ログイン・ログアウト・トークン更新のエンドポイントを含めてください。セキュリティベストプラクティスに従い、Codexでレビューしてください。",
  description="Implement user authentication"
)
```

**NGパターン（やってはいけない）:**
- メインエージェント自身が複雑なコードを書く
- Codexでのコードレビューを省略する
- Context7で最新情報を確認せずに古いパターンを使う

#### 3. @researcher - 調査の専門家

**活用すべき場面:**
- AWS公式ドキュメントを調査する時
- Webサイトから情報を収集する時
- 技術仕様やベストプラクティスを調べる時
- 競合サイトの機能を調査する時
- スクリーンショットやPDFを取得する時

**使用MCPツール:**
- AWS Documentation MCP
- Chrome DevTools MCP（Webスクレイピング）
- Codex CLI MCP（コードベース分析）

**活用例:**
```
ユーザー: 「AWS Lambdaのベストプラクティスを調査して」

メインエージェントの判断: 調査タスク → ndf:researcher に委譲

Task(
  subagent_type="ndf:researcher",
  prompt="AWS Lambdaのベストプラクティスを調査してください。AWS公式ドキュメントを参照し、パフォーマンス最適化、セキュリティ、コスト削減の観点でまとめてください。",
  description="Research AWS Lambda best practices"
)
```

**NGパターン（やってはいけない）:**
- メインエージェント自身がWebスクレイピングを試みる
- AWS Docsを使わずに一般的な回答をする

#### 4. @scanner - ファイル読み取りの専門家

**活用すべき場面:**
- PDFファイルを読み取る時
- 画像からテキストを抽出（OCR）する時
- PowerPointやExcelファイルを読み取る時
- 画像の内容を説明する時

**使用MCPツール:**
- Codex CLI MCP（ファイル読み取り）

**活用例:**
```
ユーザー: 「document.pdfの内容を読み取って要約して」

メインエージェントの判断: ファイル読み取りタスク → ndf:scanner に委譲

Task(
  subagent_type="ndf:scanner",
  prompt="/path/to/document.pdfの内容を読み取って、主要なポイントを3-5点に要約してください。",
  description="Read and summarize PDF"
)
```

**NGパターン（やってはいけない）:**
- メインエージェント自身がPDFや画像を処理しようとする
- Claude Codeの標準ツールでサポートされていないファイルを直接読もうとする

## タスク分類のフローチャート

```
ユーザーの要求
    ↓
[タスクの種類を判断]
    ↓
┌──────────────────────────────────────────┐
│ データ関連？                               │
│ - SQL、データベース、データ分析           │
│ → YES: Task(subagent_type="ndf:data-analyst") │
└──────────────────────────────────────────┘
    ↓ NO
┌──────────────────────────────────────────┐
│ コーディング関連？                         │
│ - 実装、リファクタリング、レビュー        │
│ → YES: Task(subagent_type="ndf:corder")  │
└──────────────────────────────────────────┘
    ↓ NO
┌──────────────────────────────────────────┐
│ 調査関連？                                 │
│ - ドキュメント、Webスクレイピング         │
│ → YES: Task(subagent_type="ndf:researcher") │
└──────────────────────────────────────────┘
    ↓ NO
┌──────────────────────────────────────────┐
│ ファイル読み取り関連？                    │
│ - PDF、画像、Office文書                   │
│ → YES: Task(subagent_type="ndf:scanner") │
└──────────────────────────────────────────┘
    ↓ NO
[メインエージェント自身で処理]
```

## 複数エージェントの連携

複雑なタスクでは、**複数のサブエージェントを順番に、または並行して活用**します。

### 例1: データ分析 → レポート作成

```
ユーザー: 「BigQueryで売上データを分析して、結果をPowerPointにまとめて」

手順:
1. Task(subagent_type="ndf:data-analyst", ...) でデータ分析
2. 結果をメインエージェントが受け取る
3. メインエージェントがPowerPointファイルを作成
4. Task(subagent_type="ndf:scanner", ...) でPowerPointが正しく作成されたか確認
```

### 例2: 調査 → 実装

```
ユーザー: 「AWS Lambdaのベストプラクティスを調べて、それに基づいてコードを書いて」

手順:
1. Task(subagent_type="ndf:researcher", ...) でAWS Lambdaのベストプラクティスを調査
2. 調査結果をメインエージェントが受け取る
3. Task(subagent_type="ndf:corder", ...) でベストプラクティスに基づいたコードを実装
```

### 例3: PDF読み取り → データ分析

```
ユーザー: 「このPDFの売上データを読み取って、データベースにインポートして分析して」

手順:
1. Task(subagent_type="ndf:scanner", ...) でPDFを読み取り、データ抽出
2. 抽出データをメインエージェントが確認
3. Task(subagent_type="ndf:data-analyst", ...) でデータベースにインポート
4. Task(subagent_type="ndf:data-analyst", ...) でデータ分析を実行
```

## ベストプラクティス

### DO（推奨）

✅ **タスクごとに専門エージェントを活用**
```
良い例:
Task(subagent_type="ndf:data-analyst", prompt="BigQueryで売上分析を実行", ...)
```

✅ **複雑なタスクは分解して複数エージェントに委譲**
```
良い例:
1. Task(subagent_type="ndf:researcher", ...) で調査
2. Task(subagent_type="ndf:corder", ...) で実装
3. Task(subagent_type="ndf:data-analyst", ...) でデータ確認
```

✅ **エージェントの結果を検証して統合**
```
良い例:
ndf:data-analyst の分析結果を確認 → 追加の質問や修正指示 → 最終報告
```

✅ **並行処理が可能な場合は並行して起動**
```
良い例: 複数の調査をTaskツールで並行起動
Task(subagent_type="ndf:researcher", prompt="調査A", ...)
Task(subagent_type="ndf:researcher", prompt="調査B", ...)
```

### DON'T（非推奨）

❌ **専門外のタスクをメインエージェントで処理**
```
悪い例: メインエージェント自身がSQLを書いてデータ分析
→ Task(subagent_type="ndf:data-analyst", ...) に委譲すべき
```

❌ **サブエージェントを使わずに推測で回答**
```
悪い例: AWS Lambdaについて一般的な知識で回答
→ Task(subagent_type="ndf:researcher", ...) でAWS公式ドキュメントを調査すべき
```

❌ **複雑なコードをレビューなしで実装**
```
悪い例: メインエージェントが書いたコードをそのまま提供
→ Task(subagent_type="ndf:corder", ...) に委譲してCodexレビューを通すべき
```

❌ **PDFや画像を直接処理しようとする**
```
悪い例: メインエージェントがPDFの内容を推測
→ Task(subagent_type="ndf:scanner", ...) に委譲して正確に読み取るべき
```

## 利用可能なMCPツール（参考）

メインエージェントも以下のMCPツールを使用できますが、**専門エージェントに委譲する方が高品質**です：

- **Claude Code MCP**: View、Edit、LSなどのファイル操作
- **GitHub MCP**: PR/イシュー管理、コード検索
- **Serena MCP**: コード構造理解、シンボル編集
- **Notion MCP**: ドキュメント管理
- **BigQuery MCP**: → **@data-analyst に委譲推奨**
- **DBHub MCP**: → **@data-analyst に委譲推奨**
- **AWS Docs MCP**: → **@researcher に委譲推奨**
- **Chrome DevTools MCP**: → **@researcher に委譲推奨**
- **Codex CLI MCP**: → **@corder または @scanner に委譲推奨**
- **Context7 MCP**: → **@corder に委譲推奨**

## まとめ

**メインエージェントの役割:**
- タスクの全体管理と調整
- 適切なサブエージェントへの委譲判断
- サブエージェントの結果統合
- ユーザーへの最終報告

**サブエージェントの役割:**
- 各専門分野での高品質な作業実行
- 専門MCPツールの効果的な活用
- 詳細な分析と実装

**成功の鍵:**
複雑なタスクを無理に自分で処理せず、**適切なサブエージェントに委譲すること**。これにより、より高品質で専門的な結果が得られます。

## Stop Hook実装の重要な注意事項

### Claude CLI呼び出し時の無限ループ防止

Stop hookスクリプト内で`claude`コマンドをサブプロセスとして呼び出す場合、**必ず`--settings`フラグでhooksとpluginsを無効化**してください。

これを忘れると、サブプロセスが終了時に自身のStop hookをトリガーし、無限ループが発生します。

**正しい実装（Node.js）:**
```javascript
const { spawn } = require('child_process');

const claude = spawn('claude', [
  '-p',
  '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}',  // ★ 必須
  '--output-format', 'text'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});
```

**正しい実装（Bash）:**
```bash
claude -p --settings '{"disableAllHooks": true, "disableAllPlugins": true}' --output-format text
```

詳細は、リポジトリルートの`CLAUDE.md`の「Stop Hook実装ガイドライン」セクションを参照してください。
