#!/usr/bin/env bash
# cross-review gemini launcher (trusted directory 対策込み).
#
# Usage: launch-gemini.sh <STATE_PR> <ROUND>
#
# 引数 STATE_PR は state.json の key (= 最初に init した PR 番号)。
# レビュー対象の PR は state.json の `current_pr` を読む。
#
# 注意:
#   - worktree のような新規パスは untrusted 判定で --yolo が "default" に降格する。
#     `--skip-trust` と `GEMINI_CLI_TRUST_WORKSPACE=true` を **両方** 必須とする。
#   - 完了判定は monitor.py が pidfile + sentinel + result.json で多軸判定する。

set -euo pipefail

STATE_PR=${1:?STATE_PR required}
ROUND=${2:?ROUND required}

STATE=/tmp/cross-review-pr$STATE_PR-state.json
[ -s "$STATE" ] || { echo "state.json not found: $STATE" >&2; exit 1; }

WORKTREE=$(jq -r '.worktree_path' "$STATE")
REPO=$(jq -r '.repo' "$STATE")
EVENT_DOWNGRADE=$(jq -r '.event_downgrade // false' "$STATE")
# PR (=current_pr) は gh コマンドのレビュー対象 PR 番号として使う。
# tmp パス側は STATE_PR で固定 (monitor.py / state.py との読み書き整合のため)。
PR=$(jq -r '.current_pr' "$STATE")
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

PROMPT=/tmp/gemini-review-pr$STATE_PR-prompt.md
# 既存コメントは gemini の workspace 制約 (`/tmp/` は workspace 外) を回避するため、
# ファイルパスではなく **プロンプトにインライン埋め込み** する。
EXISTING_FILE=/tmp/cross-review-pr$STATE_PR-existing-comments.txt
if [ -s "$EXISTING_FILE" ]; then
  EXISTING_INLINE=$(cat "$EXISTING_FILE")
else
  EXISTING_INLINE="(なし)"
fi

cat > "$PROMPT" <<EOF
# /ndf:review 実行 (cross-review gemini / round $ROUND)

PR #$PR を **gemini の観点でレビューし、gh api で直接 PR に投稿** してください。

## 必須コンテキスト
- repo: $REPO
- PR: #$PR
- commit_id (headRefOid): $SHA
- worktree: $WORKTREE （**ファイル読み取りは必ず此処の絶対パスを使う**）
- event_downgrade: $EVENT_DOWNGRADE
  - true の場合: payload の \`event\` は \`COMMENT\` にすること。
    body 先頭 prefix の \`<event>\` は本来の intent を書く。

## 既存コメントスナップショット（重複指摘禁止）
gemini の workspace 制約で /tmp/ は読めないため、以下にインライン展開する:

\`\`\`
$EXISTING_INLINE
\`\`\`

## 出力契約
- review body の **先頭行** に必ず以下を入れる:
  \`\`\`
  ## 🤖 cross-review | round $ROUND | gemini | <event(intent)>
  \`\`\`
- インラインコメントは \`[重要度 / カテゴリ]\` プレフィックス
- 投稿後、サマリを **/tmp/gemini-review-pr$STATE_PR-result.json** に書く（フォーマットは launch-codex.sh と同じ）
- payload は **/tmp/gemini-review-pr$STATE_PR-round$ROUND-payload.json** に保存

## 守るべきこと
- **リポジトリ編集禁止**。gh api での投稿のみ許可
- worktree 外のパスは触らない
- gh api 失敗時は err.log にエラー詳細を残して即時終了
EOF

cd "$WORKTREE"
# ⚠ --skip-trust と GEMINI_CLI_TRUST_WORKSPACE=true は両方必須
GEMINI_CLI_TRUST_WORKSPACE=true nohup gemini --yolo --skip-trust --output-format text \
  -p "$(cat "$PROMPT")" \
  > /tmp/gemini-review-pr$STATE_PR-stdout.log \
  2> /tmp/gemini-review-pr$STATE_PR-err.log &
echo $! > /tmp/gemini-review-pr$STATE_PR.pid
disown
echo "🚀 gemini launched (pid=$(cat /tmp/gemini-review-pr$STATE_PR.pid))" >&2
