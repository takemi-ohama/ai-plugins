# NDF Plugin - 開発者向けガイドライン

## 概要

**NDFプラグインの開発・メンテナンス**を行うAIエージェント向けガイドライン。

**利用者向けガイドライン**は`CLAUDE.ndf.md`を参照。

## プラグイン情報

- **名前**: ndf
- **現在バージョン**: 2.7.0
- **種類**: 統合プラグイン（MCP + Skills + Agents + Hooks）
- **リポジトリ**: https://github.com/takemi-ohama/ai-plugins

## 開発ルール

- ドキュメント・コミットメッセージ・PR説明は**日本語**
- **mainブランチへの直接コミット禁止**（featureブランチ+PR）
- **セマンティックバージョニング**: MAJOR（破壊的変更）、MINOR（新機能）、PATCH（バグ修正）

## ディレクトリ構造

```
plugins/ndf/
├── .claude-plugin/
│   └── plugin.json              # プラグインメタデータ
├── .mcp.json                    # MCPサーバー定義（Serena, Codex CLI）
├── hooks/
│   └── hooks.json               # プロジェクトフック定義
├── scripts/
│   ├── slack-notify.js          # Slack通知スクリプト
│   └── inject-plugin-guide.js   # CLAUDE.ndf.md自動注入スクリプト
├── agents/                      # サブエージェント（6個）
│   ├── director.md
│   ├── data-analyst.md
│   ├── corder.md
│   ├── researcher.md
│   ├── scanner.md
│   └── qa.md
├── skills/                      # スキル（23個）
│   ├── pr/                      # ワークフロー系（9個、/ndf:* で呼出）
│   ├── pr-tests/
│   ├── fix/
│   ├── review/
│   ├── merged/
│   ├── clean/
│   ├── serena/
│   ├── mem-review/
│   ├── mem-capture/
│   ├── data-analyst-sql-optimization/  # モデル起動型（14個）
│   ├── data-analyst-export/
│   ├── corder-code-templates/
│   ├── corder-test-generation/
│   ├── researcher-report-templates/
│   ├── scanner-pdf-analysis/
│   ├── scanner-excel-extraction/
│   ├── qa-security-scan/
│   ├── markdown-writing/
│   ├── memory-handling/
│   ├── serena-memory-strategy/
│   ├── python-execution/
│   ├── docker-container-access/
│   └── skill-development/
├── CLAUDE.md                    # このファイル（開発者向け）
├── CLAUDE.ndf.md                # 利用者向けガイドライン
└── README.md                    # プラグイン説明書
```

## 一般的な開発タスク

### 新しいスキルの追加

1. `skills/{skill-name}/SKILL.md` を作成（YAMLフロントマター必須）
2. `plugin.json` の `skills` 配列に `"./skills/{skill-name}"` を追加
3. `CLAUDE.ndf.md` のスキル一覧を更新
4. `plugin.json` のバージョンをMINOR上げ
5. Serenaメモリーを更新
6. テスト・コミット

**スキルのフロントマター:**
```yaml
---
name: skill-name
description: "スキルの説明"
argument-hint: "[引数のヒント]"          # オプション
disable-model-invocation: true           # true=手動呼出のみ、false=Claude自動呼出可
user-invocable: true                     # false=/メニューから非表示
allowed-tools:
  - Bash
  - Read
---
```

### 新しいサブエージェントの追加

1. `agents/{agent-name}.md` を作成（YAMLフロントマター必須）
2. `plugin.json` の `agents` 配列に追加
3. `CLAUDE.ndf.md` のエージェント一覧を更新
4. バージョンMINOR上げ → Serenaメモリー更新 → テスト・コミット

### MCPサーバーの追加・更新

1. `.mcp.json` の `mcpServers` に追加
2. README.mdに説明追加
3. バージョン更新 → Serenaメモリー更新 → テスト・コミット

### フックの追加・更新

1. `hooks/hooks.json` を編集
2. スクリプトは `scripts/` に配置（`CLAUDE_PLUGIN_ROOT`環境変数利用）
3. バージョン更新 → テスト・コミット

## 検証チェックリスト

- [ ] plugin.jsonが有効なJSON
- [ ] バージョン番号が適切にインクリメント
- [ ] すべてのスキル/エージェントファイルが存在
- [ ] YAMLフロントマターが正しい
- [ ] .mcp.jsonが有効なJSON
- [ ] README.md / CLAUDE.ndf.md が最新
- [ ] Serenaメモリーが更新されている

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| エージェントが認識されない | plugin.jsonのagents配列、ファイルパス、YAMLフロントマターを確認 |
| スキル/コマンドが表示されない | plugin.jsonのskills配列、SKILL.mdのフロントマターを確認、`/plugin reload ndf` |
| MCPサーバーが起動しない | .mcp.jsonの構文、コマンドパス、環境変数を確認 |
| フックが動作しない | hooks.jsonの構文、スクリプト実行権限、CLAUDE_PLUGIN_ROOTを確認 |

## 開発履歴

### v2.7.0
- commandsをskillsに統合（Claude Code 2.1.3対応）
- `commands/`ディレクトリ廃止、全9コマンドを`skills/`に移行
- `serena-memory-strategy`スキル追加（init-memory-strategyフック廃止）
- Skills: 14個→23個（ワークフロー9個 + モデル起動型14個）

### v2.6.0
- NDFプラグインのMCP構成を最適化し個別プラグイン化

### v2.5.0
- スキル分割改修とProgressive Disclosure実装
- directorエージェントをClaude Code機能活用の指揮者として再定義

### v2.0.0
- GitHub MCP, Serena MCP, Context7 MCPを公式プラグインに移行
