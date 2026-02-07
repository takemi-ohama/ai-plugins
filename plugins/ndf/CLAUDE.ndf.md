<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
<!-- VERSION: 11 -->
# NDF Plugin Guide (v2.8.0)

## ポリシー

- 応答・ドキュメント・コミットメッセージは**日本語**
- **mainブランチへの直接push/merge禁止**（featureブランチ+PR必須）
- commit/push/PR mergeは**ユーザー確認後**に実行（明示的なスラッシュコマンド除く）
- コンテキスト節約: ファイル全体を読む前にSerenaのシンボル概要を確認

## コアMCP（2個）

| MCP | 用途 |
|-----|------|
| **Serena** | セマンティックコード操作、メモリー管理 |
| **Codex CLI** | corder/scannerエージェント経由で利用 |

**セッション開始時にSerenaをアクティベート:**
```
mcp__plugin_ndf_serena__activate_project /path/to/project
mcp__plugin_ndf_serena__check_onboarding_performed
mcp__plugin_ndf_serena__list_memories
```

## サブエージェント（6個）

Task toolで `subagent_type="ndf:{name}"` として起動。

| エージェント | 用途 | 起動タイミング |
|-------------|------|--------------|
| `ndf:director` | タスク統括・設計立案 | 複数エージェント連携が必要な複雑タスク |
| `ndf:corder` | コード実装・リファクタ・レビュー | コーディングタスク |
| `ndf:data-analyst` | SQL・BigQuery・データ分析 | データ分析・エクスポート |
| `ndf:researcher` | 技術調査・Web情報収集 | AWS docs調査、外部API仕様調査 |
| `ndf:scanner` | PDF・画像・Officeファイル読取 | ファイル内容の抽出 |
| `ndf:qa` | セキュリティ・品質レビュー | OWASP Top 10、コード品質チェック |

### directorの運用ルール

- directorは他のサブエージェントを**直接呼び出さない**
- Main Agentに「必要なエージェントと実行順序」を報告する
- Main Agentが報告に基づきサブエージェントを起動する
- 中〜大規模タスクでは計画を `issues/` `docs/` `specs/` に保存する

## Skills（24個）

すべてのスキルは `skills/` ディレクトリに統合。スラッシュコマンド（`/ndf:*`）もスキルとして実装。

### ワークフロースキル（10個） - ユーザー手動呼出

| スキル | 用途 |
|--------|------|
| `/ndf:pr` | commit, push, PR作成 |
| `/ndf:pr-tests` | PRのTest Plan自動実行 |
| `/ndf:review` | PRレビュー |
| `/ndf:fix` | PRレビューコメントの修正対応 |
| `/ndf:merged` | マージ後クリーンアップ |
| `/ndf:clean` | マージ済みブランチ削除 |
| `/ndf:serena` | 開発履歴・知見の記録 |
| `/ndf:mem-capture` | タスク終了時のSerena memory保存 |
| `/ndf:mem-review` | 中期memoryのコミット数ベース自動レビュー |
| `/ndf:deepwiki-transfer` | DeepWikiコンテンツをMarkdownファイルとして転載 |

### モデル起動型スキル（14個） - Claude自動活用

| カテゴリ | Skill名 | 概要 |
|---------|---------|------|
| Data Analyst | `data-analyst-sql-optimization` | SQL最適化パターン |
| | `data-analyst-export` | CSV/JSON/Excel/Markdownエクスポート |
| Corder | `corder-code-templates` | REST API、React、DB、認証のテンプレート |
| | `corder-test-generation` | ユニット/統合テスト自動生成 |
| Researcher | `researcher-report-templates` | 調査レポートテンプレート |
| Scanner | `scanner-pdf-analysis` | PDF解析・テーブル抽出 |
| | `scanner-excel-extraction` | Excelデータ抽出・変換 |
| QA | `qa-security-scan` | OWASP Top 10セキュリティスキャン |
| Docs | `markdown-writing` | Markdown文書作成ルール（mermaid/plantUML） |
| Memory | `memory-handling` | Serena memory読み書きの行動ルール |
| | `serena-memory-strategy` | Serena memoryの分類・メタデータ・レビュー戦略 |
| Common | `python-execution` | Python実行環境の自動判定 |
| | `docker-container-access` | Dockerコンテナアクセス判定 |
| | `skill-development` | Skill開発ベストプラクティス |

## オプションMCPプラグイン

必要に応じて個別インストール:
- `mcp-bigquery@ai-plugins` → data-analyst
- `mcp-chrome-devtools@ai-plugins` → researcher / qa
- `mcp-aws-docs@ai-plugins` → researcher
- `mcp-dbhub@ai-plugins` → data-analyst
- `mcp-notion@ai-plugins` → ノート管理

## DO / DON'T

**DO:**
- 複雑タスクは `ndf:director` に委譲
- 専門タスクは対応するエージェントに直接委譲
- 技術的に不確実な場合は推測せず外部リソースを調査
- Serena memoryで過去の判断・制約を確認してから作業開始

**DON'T:**
- Main Agentで複数エージェントの手動調整（directorを使う）
- PDF/画像をscannerなしで処理
- ファイル全体を無闇に読み込む（Serenaのシンボル概要を先に確認）
- エージェント間の直接呼び出し（必ずMain Agent経由）
<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->
