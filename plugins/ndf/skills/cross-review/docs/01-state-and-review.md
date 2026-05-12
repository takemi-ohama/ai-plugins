# 01: 状態管理 + レビュー実行 (Step 0〜4)

`SKILL.md` 本体から呼び出される **状態ファイル初期化 / ラウンド開始 /
並列レビュー / 判定 / 振動検知** までの詳細手順。

## 状態ファイル

`/tmp/cross-review-pr<番号>-state.json`:

```json
{
  "started_at": "2026-05-12T...",
  "max_rounds": 6,
  "rotate_after": 2,
  "only": null,
  "current_pr": 123,
  "pr_history": [
    {"pr": 123, "opened_at": "...", "closed_at": null, "rounds": 2}
  ],
  "rounds": [
    {
      "round": 1,
      "pr": 123,
      "started_at": "...",
      "codex":  {"event": "REQUEST_CHANGES", "comments": 5, "review_url": "..."},
      "gemini": {"event": "REQUEST_CHANGES", "comments": 3, "review_url": "..."},
      "fix":    {"commit": "abc1234", "fixed": 6, "deferred": 2, "rejected": 0, "ci": "SUCCESS"},
      "ended_at": "..."
    }
  ],
  "deferred_nits": [
    {"pr": 123, "round": 1, "path": "src/foo.py", "line": 42, "severity": "nit",
     "summary": "...", "comment_url": "..."}
  ],
  "final": null
}
```

`final` 値: `approved` / `max_rounds` / `oscillation` / `error`

## Step 0: 準備 + 既存 state 引き継ぎ

```bash
PR=<引数 or 直前PR>
MAX_ROUNDS=6
ROTATE_AFTER=2
ONLY=
STATE=/tmp/cross-review-pr$PR-state.json

if [ -f "$STATE" ] && jq -e '.final == null' "$STATE" >/dev/null; then
  echo "↻ 前回中断 state から再開（round=$(jq '.rounds | length' "$STATE")）"
  PR=$(jq -r '.current_pr' "$STATE")
else
  cat > "$STATE" <<JSON
{
  "started_at": "$(date -Iseconds)",
  "max_rounds": $MAX_ROUNDS,
  "rotate_after": $ROTATE_AFTER,
  "only": $(test -n "$ONLY" && echo "\"$ONLY\"" || echo "null"),
  "current_pr": $PR,
  "pr_history": [{"pr": $PR, "opened_at": "$(date -Iseconds)", "closed_at": null, "rounds": 0}],
  "rounds": [],
  "deferred_nits": [],
  "final": null
}
JSON
fi
```

## Step 1: Round 開始判定

```bash
TOTAL_ROUNDS=$(jq '.rounds | length' "$STATE")
ROUND=$((TOTAL_ROUNDS + 1))
PR=$(jq -r '.current_pr' "$STATE")
ROUND_IN_PR=$(jq --argjson p $PR '[.rounds[] | select(.pr == $p)] | length' "$STATE")
ROUND_IN_PR=$((ROUND_IN_PR + 1))

if [ "$TOTAL_ROUNDS" -ge "$MAX_ROUNDS" ]; then
  jq '.final = "max_rounds" | .ended_at = "'$(date -Iseconds)'"' "$STATE" > "$STATE.tmp"
  mv "$STATE.tmp" "$STATE"
  echo "❌ max_rounds=$MAX_ROUNDS 到達。中断。"
  exit 1
fi

echo "=== Round $ROUND / $MAX_ROUNDS (PR #$PR, round_in_pr=$ROUND_IN_PR) ==="
```

## Step 2: codex / gemini 並列レビュー（AI 直接投稿）

**要点**: メインは launcher を **並列バックグラウンド** で起動するだけ。
各 AI が `gh api` で投稿し `/tmp/<agent>-review-pr<PR>-result.json` に
サマリを書く。**ペイロード本体はメイン context に載せない**。

```bash
jq --arg ts "$(date -Iseconds)" --argjson r $ROUND --argjson p $PR \
   '.rounds += [{"round": $r, "pr": $p, "started_at": $ts}]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

[ "$ONLY" != "gemini" ] && ( /tmp/launch-codex-review.sh $PR ) & CODEX_PID=$!
[ "$ONLY" != "codex" ]  && ( /tmp/launch-gemini-review.sh $PR ) & GEMINI_PID=$!

[ "$ONLY" != "gemini" ] && wait $CODEX_PID
[ "$ONLY" != "codex" ]  && wait $GEMINI_PID

read_result() {
  local agent=$1
  local file=/tmp/$agent-review-pr$PR-result.json
  [ ! -s "$file" ] && { echo "❌ $agent: result 未生成" >&2; return 1; }
  jq --slurpfile r "$file" --arg agent "$agent" \
    ".rounds[-1].$agent = {event: \$r[0].event, comments: \$r[0].comments_count, review_url: \$r[0].review_url}" \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
}
[ "$ONLY" != "gemini" ] && read_result codex
[ "$ONLY" != "codex" ]  && read_result gemini
```

launcher の中身（codex 起動 / gemini 起動 / フォールバック投稿）は
`/ndf:review` + `/ndf:codex` + `/ndf:gemini` skill を参照。

## Step 3: 判定

```bash
CODEX_EVENT=$(jq -r ".rounds[-1].codex.event // \"SKIP\"" "$STATE")
GEMINI_EVENT=$(jq -r ".rounds[-1].gemini.event // \"SKIP\"" "$STATE")
is_pass() { [ "$1" = "APPROVE" ] || [ "$1" = "SKIP" ] || [ "$1" = "COMMENT" ]; }

if is_pass "$CODEX_EVENT" && is_pass "$GEMINI_EVENT"; then
  jq '.final = "approved" | .ended_at = "'$(date -Iseconds)'"' "$STATE" > "$STATE.tmp"
  mv "$STATE.tmp" "$STATE"
  echo "✅ 両方 APPROVE。収束。"
  exit 0
fi
echo "→ codex=$CODEX_EVENT gemini=$GEMINI_EVENT。修正へ。"
```

## Step 4: 振動検知

`/tmp/<agent>-review-pr<PR>-payload.json` から `path:line` を抽出し、
前ラウンドと現ラウンドを `comm -12` で重複検出。50% 以上重複なら
`final = "oscillation"` で中断（PR ローテーション後はリセットなので
`ROUND_IN_PR >= 2` のみで判定）。
