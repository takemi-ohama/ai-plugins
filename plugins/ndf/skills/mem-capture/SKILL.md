---
name: mem-capture
description: "タスク終了時に、再利用価値のある知見をSerena memoryとして保存する"
argument-hint: "[--project NAME] [--type TYPE] [--review-after N] [--long] [--append FILE]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Memory Capture Command

**タスク終了時**に、記憶化すべき内容をフォームで回収し、Serena MCPメモリーに保存する。

## 入力

$ARGUMENTS

## 原則

- Skillは「振る舞い」、Memoryは「現実・事実」を定義する
- 判断・前提・制約はmemoryに保存する
- 手順・実装詳細は保存しない（Anti-Pattern）
- コミット数ベースでレビュー時期を管理

## Skill vs Memory 判断基準

以下のいずれか1つでも該当する場合、Memoryに保存:
- 将来のセッションで再利用される
- プロジェクト固有の情報
- *why*（理由）を説明する
- 将来の選択肢を制限する
- レビューや期限切れが必要
- Skillを肥大化させる

## 手順

### 1) デフォルト設定

- memory dir: `.serena/memories`（Serena MCPが自動管理）
- 現在のコミットハッシュ: `git rev-parse HEAD`
- デフォルト review_after_commits: confidence別（low→10, medium→20, high→30）

### 2) ユーザーにフォームで回答してもらう

`AskUserQuestion`ツールで以下を収集:

1. **project**: (例: carloc / mdx / global)
2. **type**: (decision / assumption / experiment / principle / constraint / policy)
3. **confidence**: (low / medium / high)
4. **title**: 短いタイトル
5. **context**: 何が起きた？ 1-2文
6. **decision_or_fact**: 確定事項を1-3点
7. **why**: 理由1-2文
8. **next_action**: 必要なら
9. **review_after_commits**: 中期のみ、長期はnone
10. **related_files**: 任意（パスやPR番号）

### 3) 保存

- `--append FILE`あり: `mcp__plugin_ndf_serena__edit_memory`で追記
- それ以外: `mcp__plugin_ndf_serena__write_memory`で新規作成
- ファイル名: `{today}-{project}-{slug(title)}.md`

### 4) 出力フォーマット

```markdown
---
# <title>
type: <type>
confidence: <confidence>
project: <project>
review_after_commits: <N or none>
last_reviewed_commit: <current_commit_hash>
created_at: <today>
status: active
---

## Context
<context>

## Decision / Facts
- <decision_or_fact>

## Why
<why>

## Next action
<next_action>

## Related
- <related_files>

## Notes
- This memory intentionally excludes procedures and implementation details.
```

### 5) 長期化提案

- 内容が「不変の原則」なら長期化（principle/constraint/policy）を提案
- `--long`指定時はreview_after_commitsをnoneにする

### 6) 完了サマリ

保存ファイルパスを表示し、次の推奨: `/ndf:mem-review`

## 関連

- `/ndf:mem-review` - 中期memoryの自動レビュー
