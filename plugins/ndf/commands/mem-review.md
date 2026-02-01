---
description: "中期Serena memory（review_after_commits付き）をコミット数ベースで自動レビュー"
argument-hint: "[--threshold N] [--dir PATH] 例: /ndf:mem-review --threshold 10"
allowed-tools: [Bash, Read, Edit]
disable-model-invocation: false
---

# Memory Review Command

あなたは「中期/長期の記憶戦略」を運用するエージェントです。
このコマンドは `.serena/memories/` の **中期 memory**（`review_after_commits` を持つもの）をコミット数ベースでレビューします。

## 入力

$ARGUMENTS

## 期待するmemory形式（例）

先頭付近に以下のようなメタ情報がある（YAMLでなくても "key: value" を本文に含めば可）:
- type: decision | assumption | experiment
- review_after_commits: 20 (例: 20コミット後にレビュー、デフォルト推奨値)
- last_reviewed_commit: abc123 (最後にレビューした時のコミットハッシュ)
- confidence: low | medium | high
- project: <name>

## コミット数ベースの利点

- 開発が活発な時期: 頻繁にレビュー
- 開発が停滞している時期: 無駄なレビューを回避
- プロジェクトの実際の活動量に応じた自動調整

## 実行手順

### 0) パラメータ解釈

- --threshold N : 「レビュー間近」とみなすコミット数の閾値（デフォルト5コミット）
- --dir PATH : memoryディレクトリ（デフォルト `.serena/memories`）

まず Bash で現在のコミット数を取得する:
```bash
git rev-list --count HEAD
```

次に、対象ディレクトリを決定する（存在確認も行う）。

### 1) レビュー超過・レビュー間近の抽出

Bash で以下を行う:
1. memoryファイル一覧を取得（*.md想定）
2. 各ファイルから `review_after_commits` と `last_reviewed_commit` を抽出
3. 最後のレビュー以降のコミット数を計算:
   ```bash
   # last_reviewed_commitからHEADまでのコミット数
   git rev-list --count <last_reviewed_commit>..HEAD
   ```
4. レビュー判定:
   - overdue: コミット差分 >= review_after_commits
   - due_soon: review_after_commits - threshold <= コミット差分 < review_after_commits
5. 結果を「overdue」「due_soon」に分けてリストアップ

**例:**
- review_after_commits: 20
- last_reviewed_commit: abc123
- 現在のコミット差分: 22
- 判定: overdue（20コミット超過）

**推奨設定:**
- 実験的な決定（confidence: low）: 10コミット
- 通常の決定（confidence: medium）: 20コミット
- 重要な決定（confidence: high）: 30コミット

### 2) レポート表示（必須）

以下を必ず出力:
- 今日の日付
- 設定（dir, days）
- overdue一覧（ファイル名・review_at・type・project・冒頭1〜2行の要約）
- due_soon一覧（同上）

要約のために必要なファイルだけ Read する。

### 3) 1件ずつレビュー処理

各対象memoryについて、次の選択肢を提示し、ユーザーが指示しなくても「推奨」を1つ示す:

**A. 延長**（review_at を未来に更新）
**B. 長期化**（type=principle/constraint/policyへ移行、expires: none 付与、review_at削除）
**C. 更新**（内容修正 + review_at更新）
**D. アーカイブ**（ファイル末尾に `status: archived` を追記、または `ARCHIVE/` に移動）
**E. 削除**

ユーザーが指示しない場合は、以下で自動推奨:
- 実験結果が確定して「原則」になっている → B
- まだ暫定だが有効 → A
- 内容が古い/前提が変わった → C or D
- 明らかに不要 → E

編集が必要なら Edit でファイルを更新する。

### 4) 変更サマリ

最後に、実行した変更を一覧で出力:
- 更新したファイル
- 変更内容（review_at変更/長期化/アーカイブ/削除）
- 次回のレビュー推奨日

## 注意

- このコマンド自体は「記憶戦略の運用」だけを行う。
- 新しい意思決定を作るのは /ndf:mem-capture に誘導する。

## 関連コマンド

- `/ndf:mem-capture` - タスク完了時にメモリーを記録
