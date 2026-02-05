---
name: skill-development
description: |
  Claude Code Agent Skillの開発ベストプラクティスを提供します。SKILL.mdの書き方、多段階読み込み、ツール登録方法を解説。

  このSkillは以下を提供します:
  - SKILL.mdの構造とYAMLフロントマター
  - Progressive Disclosure（多段階読み込み）の実装
  - allowed-toolsとトリガーキーワードの設定

  Triggers: "create skill", "skill development", "SKILL.md", "allowed-tools", "スキル開発", "スキル作成", "Progressive Disclosure"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# Skill Development Best Practices

## 概要

Claude Code Agent Skillの開発ベストプラクティスです。コンテキスト効率を最大化するための多段階読み込み設計を重視します。

## クイックリファレンス

### SKILL.md基本構造

```yaml
---
name: my-skill-name
description: |
  スキルの説明（Claudeが自動判断に使用）

  Triggers: "keyword1", "keyword2", "日本語キーワード"
allowed-tools:
  - Read
  - Bash
---

# スキルのメインコンテンツ

## 概要
...
```

### YAMLフロントマター主要フィールド

| フィールド | 説明 |
|-----------|------|
| `name` | スキル名（小文字、ハイフン、最大64文字） |
| `description` | 目的と使用タイミング（トリガーキーワード含む） |
| `allowed-tools` | 許可なく使用できるツール |
| `disable-model-invocation` | `true`で自動呼び出し禁止 |
| `context` | `fork`でサブエージェント実行 |

### Progressive Disclosure（3段階読み込み）

```
第1段階: name + description → 常にシステムプロンプトに含まれる
第2段階: SKILL.md全体 → スキル呼び出し時
第3段階: 参照ファイル → 必要時にClaudeが読み込み
```

### ディレクトリ構成例

```
my-skill/
├── SKILL.md           # メイン（~100行推奨）
├── 01-details.md      # 詳細ガイド
├── 02-examples.md     # 使用例
└── 03-reference.md    # APIリファレンス
```

## ベストプラクティス

| DO | DON'T |
|----|-------|
| SKILL.mdは100行以下に | 全情報をSKILL.mdに詰め込む |
| 詳細は別ファイルに分割 | 500行超のSKILL.md |
| descriptionにトリガーキーワード | 曖昧なdescription |
| 副作用スキルは`disable-model-invocation` | deploy等を自動実行可能に |

## 詳細ガイド

| ファイル | 内容 |
|---------|------|
| `01-skill-structure.md` | SKILL.md構造、YAMLフロントマター詳細 |
| `02-progressive-disclosure.md` | 多段階読み込みの実装方法 |
| `03-tools-triggers.md` | allowed-tools、トリガー設定、引数 |

## 関連リソース

- [Claude Code Skills公式ドキュメント](https://code.claude.com/docs/en/skills)
- [anthropics/skills GitHub](https://github.com/anthropics/skills)
