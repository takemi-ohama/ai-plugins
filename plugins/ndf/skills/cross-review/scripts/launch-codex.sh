#!/usr/bin/env bash
# cross-review codex launcher.
#
# Usage: launch-codex.sh <PR> <ROUND>
#
# state.json から worktree / event_downgrade / repo を読み、headRefOid を gh で
# 取得した上で、codex に /ndf:review 相当のプロンプトを渡してバックグラウンド実行する。
# AI が gh api で直接投稿し、/tmp/codex-review-pr<PR>-result.json にサマリを書く契約。
#
# 完了判定は err.log の sentinel "^tokens used$" を wait-review.sh が検知する。

set -euo pipefail

PR=${1:?PR required}
ROUND=${2:?ROUND required}

STATE=/tmp/cross-review-pr$PR-state.json
[ -s "$STATE" ] || { echo "state.json not found: $STATE" >&2; exit 1; }

WORKTREE=$(jq -r '.worktree_path' "$STATE")
REPO=$(jq -r '.repo' "$STATE")
EVENT_DOWNGRADE=$(jq -r '.event_downgrade // false' "$STATE")
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

PROMPT=/tmp/codex-review-pr$PR-prompt.md
EXISTING=/tmp/cross-review-pr$PR-existing-comments.txt

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
- 投稿後、サマリを **/tmp/codex-review-pr$PR-result.json** に書く:
  \`\`\`json
  {
    "event": "REQUEST_CHANGES",
    "posted_as": "COMMENT",
    "comments_count": 5,
    "review_url": "https://github.com/.../pull/$PR#pullrequestreview-...",
    "by_severity": {"critical": 0, "major": 3, "minor": 2, "nit": 0}
  }
  \`\`\`
- payload（全コメント詳細）は **/tmp/codex-review-pr$PR-round$ROUND-payload.json** に保存
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
  > /tmp/codex-review-pr$PR-stdout.log \
  2> /tmp/codex-review-pr$PR-err.log &
echo $! > /tmp/codex-review-pr$PR.pid
disown
echo "🚀 codex launched (pid=$(cat /tmp/codex-review-pr$PR.pid))" >&2
