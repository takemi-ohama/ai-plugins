---
description: "タスク終了時に、再利用価値のある知見をSerena memoryとして保存する"
argument-hint: "[--project NAME] [--type TYPE] [--review-after N] [--long] [--append FILE]"
allowed-tools: [Bash, Read, Write]
disable-model-invocation: false
---

# Memory Capture Command

あなたは「中期/長期の記憶戦略」を運用するエージェントです。
このコマンドは **タスク終了時**に、記憶化すべき内容をフォームで回収し、
`.serena/memories/` に保存します。

## 入力

$ARGUMENTS

## 目標

- Skillを肥大化させないため、判断・前提・制約は memory に保存する
- ただし「手順」「実装詳細」は保存しない
- コミット数ベースでレビュー時期を管理（開発活動量に応じた自動調整）

## 実行手順

### 0) デフォルト設定

- memory dir: `.serena/memories`
- 今日: `date +%F`
- 現在のコミットハッシュ: `git rev-parse HEAD`
- デフォルト review_after_commits: 20（confidenceに応じて調整）
  - confidence: low → 10コミット
  - confidence: medium → 20コミット
  - confidence: high → 30コミット

### 1) ユーザーにフォームで回答してもらう（必須）

以下をそのまま提示し、ユーザーの入力を待たずに「推奨の埋め方」も例示してよいが、最終的にはユーザー入力を使う。

#### Memory Capture Form

1. **project**: (例 carloc / mdx / global)
2. **type**: (decision / assumption / experiment / principle / constraint / policy)
3. **confidence**: (low / medium / high)
4. **title**: (短いタイトル)
5. **context**: (何が起きた？ 1-2文)
6. **decision_or_fact**: (確定事項を1-3点)
7. **why**: (理由があれば1-2文)
8. **next_action**: (必要なら)
9. **review_after_commits**: (中期のみ、コミット数、長期は none)
   - confidence: low → 10コミット推奨
   - confidence: medium → 20コミット推奨
   - confidence: high → 30コミット推奨
10. **related_files**: (任意。パスやPR番号など)

### 2) 保存先の決定

- `--append FILE` があれば、そのファイルを Read して追記する
- それ以外は新規作成:
  - ファイル名: `{today}-{project}-{slug(title)}.md`
  - 保存先: `.serena/memories/`

必要なら mkdir を Bash で実行。

### 3) 出力フォーマット

新規作成の場合、以下のテンプレを使う（内容はフォームから埋める）:

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
- <decision_or_fact 1>
- <decision_or_fact 2>

## Why
<why>

## Next action
<next_action>

## Related
- <related_files>

## Notes
- This memory intentionally excludes procedures and implementation details.
```

### 4) 中期→長期化の自動提案

- type が decision/assumption/experiment でも、内容が「不変の原則」なら
  長期化（principle/constraint/policy）を提案する
- `--long` 指定があれば review_after_commits は none にする

### 5) 完了サマリ

保存/追記したファイルパスを必ず表示し、次の推奨コマンドを提示:
- 次回レビュー: `/ndf:mem-review`

## 使用例

### 中期memoryの記録（20コミット後レビュー）
```
/ndf:mem-capture --project myproject --type decision
```

### 中期memory（実験的、10コミット後レビュー）
```
/ndf:mem-capture --project myproject --type experiment --review-after 10
```

### 長期memory（原則）の記録
```
/ndf:mem-capture --project global --type principle --long
```

### 既存memoryへの追記
```
/ndf:mem-capture --append .serena/memories/2025-01-15-myproject-api-design.md
```

## 注意

- このコマンドは「記憶の記録」のみを行う
- 記憶のレビューは `/ndf:mem-review` を使用

## 関連コマンド

- `/ndf:mem-review` - 中期memoryの自動レビュー
