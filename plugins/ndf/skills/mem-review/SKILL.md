---
name: mem-review
description: "中期Serena memory（review_after_commits付き）をコミット数ベースで自動レビュー"
argument-hint: "[--threshold N] [--dir PATH] 例: /ndf:mem-review --threshold 10"
allowed-tools:
  - Bash
  - Read
  - Edit
---

# Memory Review Command

`.serena/memories/` の**中期memory**（`review_after_commits`を持つもの）をコミット数ベースでレビューする。

## 入力

$ARGUMENTS

## 期待するmemory形式

先頭付近に以下のメタ情報がある:
- type: decision | assumption | experiment
- review_after_commits: 20
- last_reviewed_commit: abc123
- confidence: low | medium | high
- project: <name>

## 手順

### 0) パラメータ解釈

- `--threshold N`: 「レビュー間近」とみなすコミット数の閾値（デフォルト5）
- `--dir PATH`: memoryディレクトリ（デフォルト`.serena/memories`）

### 1) レビュー対象の抽出

1. memoryファイル一覧を取得
2. 各ファイルから`review_after_commits`と`last_reviewed_commit`を抽出
3. `git rev-list --count <last_reviewed_commit>..HEAD`でコミット差分を計算
4. 判定:
   - overdue: コミット差分 >= review_after_commits
   - due_soon: review_after_commits - threshold <= コミット差分 < review_after_commits

### 2) レポート表示

- 日付、設定（dir, threshold）
- overdue一覧・due_soon一覧（ファイル名、review_after_commits、type、project、要約）

### 3) 1件ずつレビュー処理

各対象memoryについて選択肢を提示し、推奨を1つ示す:

- **A. 延長**: review_after_commitsを増やし、last_reviewed_commitを更新
- **B. 長期化**: type=principle/constraint/policyへ移行、expires: none付与
- **C. 更新**: 内容修正 + メタデータ更新
- **D. アーカイブ**: status: archivedを追記
- **E. 削除**

### 4) 変更サマリ

更新したファイル、変更内容、次回レビュー推奨コミット数を出力。

## 関連

- `/ndf:mem-capture` - タスク完了時にメモリーを記録
