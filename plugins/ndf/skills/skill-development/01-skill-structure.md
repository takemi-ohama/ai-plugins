# SKILL.md構造ガイド

## 基本構造

```yaml
---
name: my-skill-name
description: |
  スキルの説明。Claudeがいつ使用するか判断するために使用。

  Triggers: "keyword1", "keyword2"
allowed-tools:
  - Read
  - Write
---

# スキルタイトル

## 概要

スキルの目的と使用方法の概要。

## 使用方法

具体的な使用手順。
```

## YAMLフロントマター フィールド一覧

### 必須/推奨フィールド

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `name` | いいえ | スキル名（省略時はディレクトリ名）。小文字、数字、ハイフンのみ。最大64文字 |
| `description` | **推奨** | スキルの目的と使用タイミング。Claudeの自動読み込み判断に使用 |

### ツール制御

| フィールド | デフォルト | 説明 |
|-----------|----------|------|
| `allowed-tools` | なし | 許可なく使用できるツールのリスト |

```yaml
# 例
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git *)      # gitで始まるBashコマンドのみ
  - Bash(npm *)      # npmで始まるBashコマンドのみ
```

### 呼び出し制御

| フィールド | デフォルト | 説明 |
|-----------|----------|------|
| `disable-model-invocation` | `false` | `true`でClaude自動呼び出し禁止（手動のみ） |
| `user-invocable` | `true` | `false`でスラッシュメニューから非表示 |

```yaml
# deployなど副作用のあるスキル
---
name: deploy
disable-model-invocation: true
---
```

### 実行コンテキスト

| フィールド | デフォルト | 説明 |
|-----------|----------|------|
| `context` | なし | `fork`でサブエージェントとして実行 |
| `agent` | なし | `context: fork`時のエージェントタイプ |
| `model` | 継承 | 使用するモデル |

```yaml
# サブエージェントとして実行
---
name: analyze
context: fork
agent: Explore
---
```

### フック

```yaml
---
hooks:
  pre-invoke:
    command: ./scripts/setup.sh
  post-invoke:
    command: ./scripts/cleanup.sh
---
```

## name フィールドのルール

- **使用可能文字**: 小文字、数字、ハイフン（`-`）
- **最大長**: 64文字
- **省略時**: ディレクトリ名を使用

```yaml
# OK
name: my-skill-name
name: deploy-prod
name: code-review

# NG
name: MySkill       # 大文字
name: my_skill      # アンダースコア
name: my skill      # スペース
```

## description のベストプラクティス

### 良い例

```yaml
description: |
  コードを視覚的な図と例えで説明します。
  コードの仕組みを説明する時、コードベースについて教える時、
  または「これはどう動くの？」と聞かれた時に使用。

  Triggers: "explain code", "how does this work", "コード説明"
```

### 悪い例

```yaml
# 曖昧すぎる
description: コードに関するスキル

# 長すぎる（100文字以内推奨）
description: このスキルは...（長文）
```

## スキルの配置場所

| レベル | パス | 適用範囲 |
|-------|-----|---------|
| Personal | `~/.claude/skills/<name>/SKILL.md` | 全プロジェクト |
| Project | `.claude/skills/<name>/SKILL.md` | このプロジェクトのみ |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | プラグイン有効時 |

**優先順位**: Enterprise > Personal > Project（同名の場合）
