#!/usr/bin/env bash
# cross-review codex launcher.
#
# Usage: launch-codex.sh <STATE_PR> <ROUND>
#
# 引数 STATE_PR は **state.json の key (= 最初に init した PR 番号)**。
# rotation 後も state.json の場所は変わらないため、ここに渡すのは常に初期 PR。
# gh コマンドに使う「現在のレビュー対象 PR」は state.json の `current_pr` を読む。
#
# tmp ディレクトリは `_tmpdir.sh` の `tmpdir()` 関数で決定:
#   CROSS_REVIEW_TMP_DIR env → ~/.gemini/tmp/<workspace>/ → /tmp/
# gemini の workspace 制約を回避するため、`~/.gemini/tmp/...` を優先採用する。
#
# 状態ファイル: $TMP_DIR/codex-review-pr<STATE_PR>-{result,err,stdout,pid}.json
# (パスは STATE_PR ベースで固定 — monitor.py / state.py と一致させる。)

set -euo pipefail

STATE_PR=${1:?STATE_PR required}
ROUND=${2:?ROUND required}

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=_tmpdir.sh
. "$SCRIPT_DIR/_tmpdir.sh"
TMP_DIR=$(tmpdir)

STATE=$TMP_DIR/cross-review-pr$STATE_PR-state.json
[ -s "$STATE" ] || { echo "state.json not found: $STATE" >&2; exit 1; }

WORKTREE=$(jq -r '.worktree_path' "$STATE")
REPO=$(jq -r '.repo' "$STATE")
EVENT_DOWNGRADE=$(jq -r '.event_downgrade // false' "$STATE")
# PR (=current_pr) は gh コマンドのレビュー対象 PR 番号として使う。
# tmp パス側は STATE_PR で固定 (monitor.py / state.py が同じ STATE_PR 起点で
# 読みに来るため、ここを揃えないと PR rotation 後に読み書きパスが食い違う)。
PR=$(jq -r '.current_pr' "$STATE")
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

PROMPT=$TMP_DIR/codex-review-pr$STATE_PR-prompt.md
EXISTING=$TMP_DIR/cross-review-pr$STATE_PR-existing-comments.txt

cat > "$PROMPT" <<EOF
# /ndf:review 実行 (cross-review codex / round $ROUND)

PR #$PR を **codex の観点でレビューし、gh api で直接 PR に投稿** してください。

## 必須コンテキスト
- repo: $REPO
- PR: #$PR
- commit_id (headRefOid): $SHA
- worktree: $WORKTREE （**ファイル読み取りは必ず此処の絶対パスを使う**）
- event_downgrade: $EVENT_DOWNGRADE
  - true の場合: payload の \`event\` は \`COMMENT\` にすること。
    ただし body 先頭 prefix の \`<event>\` には **本来の intent** を書く。
- 既存コメントスナップショット: $EXISTING （重複指摘禁止）

## 出力契約
- review body の **先頭行** に必ず以下を入れる（fence 不要、Markdown 見出しとして）:
  \`\`\`
  ## 🤖 cross-review | round $ROUND | codex | <event(intent)>
  \`\`\`
  例: \`## 🤖 cross-review | round $ROUND | codex | REQUEST_CHANGES\`
  - \`<event>\` は **本来の intent** (REQUEST_CHANGES / APPROVE / COMMENT)
- インラインコメントは \`[major / 正確性]\` のように \`[重要度 / カテゴリ]\` プレフィックス
- 投稿後、サマリを **$TMP_DIR/codex-review-pr$STATE_PR-result.json** に書く:
  \`\`\`json
  {
    "event": "REQUEST_CHANGES",
    "posted_as": "COMMENT",
    "comments_count": 5,
    "review_url": "https://github.com/.../pull/$PR#pullrequestreview-...",
    "by_severity": {"critical": 0, "major": 3, "minor": 2, "nit": 0}
  }
  \`\`\`
- payload（全コメント詳細）は **$TMP_DIR/codex-review-pr$STATE_PR-round$ROUND-payload.json** に保存
  （振動検知用、\`{ "comments": [{path, line, body, severity}, ...] }\` 形式）

## 守るべきこと
- リポジトリ編集は行わない（コード修正は別ステップ）
- worktree 外のパスは触らない
- gh api 失敗時は err.log にエラー詳細を残して即時終了
EOF

cd "$WORKTREE"
nohup codex exec --dangerously-bypass-approvals-and-sandbox \
  --config reasoning.effort=medium -C "$WORKTREE" \
  < "$PROMPT" \
  > $TMP_DIR/codex-review-pr$STATE_PR-stdout.log \
  2> $TMP_DIR/codex-review-pr$STATE_PR-err.log &
echo $! > $TMP_DIR/codex-review-pr$STATE_PR.pid
disown
echo "🚀 codex launched (pid=$(cat $TMP_DIR/codex-review-pr$STATE_PR.pid))" >&2
