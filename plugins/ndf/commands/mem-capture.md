---
description: "タスク終了時に、再利用価値のある知見をSerena memoryとして保存する"
argument-hint: "[--project NAME] [--type TYPE] [--review-after N] [--long] [--append FILE]"
allowed-tools: [Bash, Read, ToolSearch, AskUserQuestion]
disable-model-invocation: false
---

# Memory Capture Command

あなたは「中期/長期の記憶戦略」を運用するエージェントです。
このコマンドは **タスク終了時**に、記憶化すべき内容をフォームで回収し、
`.serena/memories/` に保存します。

## 入力

$ARGUMENTS

## 目標

- `.serena/memories/memory-strategy.md` の方針に従って記憶を管理する
- Serena MCP (`mcp__plugin_serena_serena__write_memory`) に保存する
- Agent Skillは「振る舞い」を記述し、Memoryは「現実・事実」を定義する
- Skillを肥大化させないため、判断・前提・制約は memory に保存する
- ただし「手順」「実装詳細」は保存しない（Anti-Pattern）
- コミット数ベースでレビュー時期を管理（開発活動量に応じた自動調整）

## Skill vs Memory 判断基準

以下のいずれか1つでも該当する場合、**Memory に保存する**：

- ✅ 将来のセッションで再利用される
- ✅ プロジェクト固有の情報
- ✅ *why*（理由）を説明する（*how*（方法）ではなく）
- ✅ 将来の選択肢を制限する
- ✅ レビューや期限切れが必要
- ✅ エージェントスキルを肥大化させる

それ以外は、Skillに記述するか、一時的な情報として扱う。

## Memory Granularity Rules

- 1つのメモリーエントリ = 1つの決定または原則
- 事実、仮定、結論を混在させない
- 完全性より明確性を優先
- **手順を埋め込まない**（重要）

## 避けるべきAnti-Patterns

- ❌ 手順をメモリーに保存
- ❌ 決定をスキル内にエンコード
- ❌ 類似トピックの重複メモリー作成
- ❌ 実験的仮定を未レビューのまま放置
- ❌ 日付ベースのレビュー（コミットベースを使用）

## 実行手順

### 0) Serena MCPツールのロード

**最初に必ずSerena MCPツールをロードする**:

```bash
ToolSearch query="select:mcp__plugin_serena_serena__write_memory"
ToolSearch query="select:mcp__plugin_serena_serena__read_memory"
ToolSearch query="select:mcp__plugin_serena_serena__edit_memory"
ToolSearch query="select:mcp__plugin_serena_serena__list_memories"
```

### 1) デフォルト設定

- memory dir: `.serena/memories` (Serena MCPが自動管理)
- 今日: `date +%F`
- 現在のコミットハッシュ: `git rev-parse HEAD`
- デフォルト review_after_commits: 20（confidenceに応じて調整）
  - confidence: low → 10コミット
  - confidence: medium → 20コミット
  - confidence: high → 30コミット

### 2) ユーザーにフォームで回答してもらう（必須）

`AskUserQuestion`ツールを使用して、以下の情報を収集する。

ユーザーの入力を待たずに「推奨の埋め方」も例示してよいが、最終的にはユーザー入力を使う。

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

### 3) 保存先の決定と保存方法

**Serena MCPを使用して保存する**（`.serena/memories/` ディレクトリに直接書き込まない）。

- `--append FILE` があれば:
  - `mcp__plugin_serena_serena__read_memory` でファイルを読み込む
  - 内容を追記して `mcp__plugin_serena_serena__edit_memory` で更新

- それ以外は新規作成:
  - ファイル名: `{today}-{project}-{slug(title)}.md`
  - `mcp__plugin_serena_serena__write_memory` で作成
  - 保存先: `.serena/memories/` (Serena MCPが自動管理)

### 4) 出力フォーマットと保存

#### 新規作成の場合

以下のテンプレートを使い、`mcp__plugin_serena_serena__write_memory` で保存:

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
- Following memory-strategy.md: Skills describe behavior, Memory defines reality.
```

**保存コマンド例**:
```bash
mcp__plugin_serena_serena__write_memory \
  memory_file_name="2026-02-02-myproject-api-design.md" \
  content="<上記フォーマットの内容>"
```

#### 追記の場合

`mcp__plugin_serena_serena__edit_memory` を使用:

```bash
# 既存メモリーを読み込み
mcp__plugin_serena_serena__read_memory memory_file_name="existing-memory.md"

# 追記内容を編集
mcp__plugin_serena_serena__edit_memory \
  memory_file_name="existing-memory.md" \
  needle="## Notes" \
  repl="## Additional Context\n<new_content>\n\n## Notes" \
  mode="literal"
```

### 5) 中期→長期化の自動提案

- type が decision/assumption/experiment でも、内容が「不変の原則」なら
  長期化（principle/constraint/policy）を提案する
- `--long` 指定があれば review_after_commits は none にする

### 6) 完了サマリ

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
