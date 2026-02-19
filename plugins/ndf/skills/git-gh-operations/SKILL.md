---
name: git-gh-operations
description: |
  git/gh コマンド実行時の共通エラーパターンと正しい操作方法を提供します。
  CWD問題、パス指定、GitHub API操作の注意点を網羅。

  このSkillは以下を提供します:
  - git操作時のパス解決ルール
  - gh CLI / GitHub API の正しい使い方
  - 過去のエラー事例と対策

  Triggers: "git add", "git commit", "git push", "gh pr", "gh api", "GitHub操作", "gitエラー", "fatal:", "pathspec"
allowed-tools:
  - Bash
  - Read
---

# Git / gh 操作スキル

## 最重要ルール: CWD とパスの整合性

git コマンドはすべて **CWD からの相対パス** で解決される。
操作前に必ず `pwd` で CWD を確認すること。

### パターン1: CWDがサブディレクトリの場合

```
# CWD: /work/repo/lambda-batch/MyProject/
# リポジトリルート: /work/repo/

# NG: リポジトリルートからのパスを指定
git add lambda-batch/MyProject/src/foo.py
# => fatal: pathspec did not match any files

# OK: CWDからの相対パスを指定
git add src/foo.py

# OK: 絶対パスを指定
git add /work/repo/lambda-batch/MyProject/src/foo.py
```

### パターン2: 安全な方法

```bash
# 方法A: git -C でリポジトリルートを指定
git -C /work/repo add lambda-batch/MyProject/src/foo.py

# 方法B: CWD を変更せずに絶対パスを使用
git add "$(git rev-parse --show-toplevel)/lambda-batch/MyProject/src/foo.py"

# 方法C（推奨）: CWDからの相対パスを使用
# まず pwd で確認してからパスを組み立てる
```

## git 操作チェックリスト

### git add の前に

1. `pwd` で CWD を確認
2. `git status` で変更ファイルのパスを確認（表示されるパスはリポジトリルートからの相対パス）
3. `git status` の出力パスと CWD の関係を計算してから `git add` する

### git commit の前に

1. `git diff --cached` でステージング内容を確認
2. HEREDOC形式でメッセージを渡す（改行・特殊文字の問題回避）

```bash
git commit -m "$(cat <<'EOF'
コミットメッセージ

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

## gh CLI / GitHub API の注意点

### PRレビューコメントへの返信

```bash
# NG: -X POST がない
gh api repos/OWNER/REPO/pulls/comments/{id}/replies -f body='...'
# => 404 Not Found

# OK: -X POST を明示
gh api -X POST repos/OWNER/REPO/pulls/comments/{id}/replies -f body='...'
```

### 自分のPRは Approve できない

```
# GitHub の制約: 自分で作成した PR に APPROVE レビューは不可
# => "Can not approve your own pull request"
# 対策: event を "COMMENT" に変更して送信
```

### PR作成時の body は HEREDOC

```bash
# NG: \n がリテラルで混入する可能性
gh pr create --title "タイトル" --body "行1\n行2"

# OK: HEREDOC形式
gh pr create --title "タイトル" --body "$(cat <<'EOF'
## Summary
- 変更内容

## Test plan
- [ ] テスト項目
EOF
)"
```

## AWS CLI の注意点

### CloudWatch ログストリーム名の [$LATEST]

```bash
# NG: --query で [$LATEST] を含む文字列がパースエラー
aws logs get-log-events --query 'events[*].message' --output text

# OK: --output json にして python でパース
aws logs get-log-events --output json | python3 -c "
import sys,json
data = json.loads(sys.stdin.read())
for e in data['events']:
    print(e['message'].strip())
"
```

## エラー事例集

| エラーメッセージ | 原因 | 対策 |
|----------------|------|------|
| `fatal: pathspec '...' did not match any files` | CWD とパスの不一致 | `pwd` 確認後、CWD相対パスで指定 |
| `404 Not Found` (gh api) | HTTP メソッド未指定 | `-X POST` を明示 |
| `Can not approve your own pull request` | 自己 Approve 不可 | `COMMENT` イベントに変更 |
| `Unknown options: , , ,` (aws cli) | `[$LATEST]` のシェルエスケープ | `--output json` + python パース |

## 詳細ガイド

| ファイル | 内容 | 参照タイミング |
|---------|------|--------------|
| `01-common-errors.md` | 詳細なエラー事例と再現手順 | エラー発生時 |
