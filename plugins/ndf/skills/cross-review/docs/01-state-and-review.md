# 01: 状態管理 + レビュー実行 (Step 0〜4)

`SKILL.md` 本体から呼び出される **状態ファイル初期化 / ラウンド開始 /
並列レビュー / 判定 / 振動検知** までの詳細手順。

## 状態ファイル

`/tmp/cross-review-pr<番号>-state.json`:

```json
{
  "started_at": "2026-05-12T...",
  "max_rounds": 6,
  "rotate_after": 5,
  "only": null,
  "current_pr": 123,
  "worktree_path": "/work/worktrees/pr123",
  "pr_author": "someone",
  "is_own_pr": false,
  "event_downgrade": false,
  "pr_history": [
    {"pr": 123, "opened_at": "...", "closed_at": null, "rounds": 2}
  ],
  "rounds": [
    {
      "round": 1,
      "pr": 123,
      "started_at": "...",
      "codex":  {"intent": "REQUEST_CHANGES", "posted_as": "COMMENT",
                 "comments": 5, "review_url": "...",
                 "by_severity": {"critical": 0, "major": 3, "minor": 2, "nit": 0}},
      "gemini": {"intent": "REQUEST_CHANGES", "posted_as": "COMMENT",
                 "comments": 3, "review_url": "...",
                 "by_severity": {"critical": 0, "major": 2, "minor": 1, "nit": 0}},
      "fix":    {"commit": "abc1234", "fixed": 6, "deferred": 2, "rejected": 0,
                 "resolved_threads": 4, "ci": "SUCCESS", "ci_note": null},
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

### 重要なフィールド

- `worktree_path` — 並行セッションとの分離。サブエージェントへの cwd 指示にも使う
- `is_own_pr` / `event_downgrade` — 自分の PR の場合 `REQUEST_CHANGES → COMMENT` 強制ダウングレード
- `rounds[].codex.intent` — AI の本来判定。**ループ判定はこれを見る**
- `rounds[].codex.posted_as` — GitHub に実際に送った event。`is_own_pr=true` なら `COMMENT` になる
- `rounds[].fix.resolved_threads` — fix サブエージェントが `resolveReviewThread` で resolve した件数
- `rounds[].fix.ci_note` — コード無関係の CI 失敗時に「Assignees 未設定」等の理由を残す

## Step 0: 準備 + 既存 state 引き継ぎ

```bash
PR=<引数 or 直前PR>
MAX_ROUNDS=6
ROTATE_AFTER=5
ONLY=
STATE=/tmp/cross-review-pr$PR-state.json

if [ -f "$STATE" ] && jq -e '.final == null' "$STATE" >/dev/null; then
  echo "↻ 前回中断 state から再開（round=$(jq '.rounds | length' "$STATE")）"
  PR=$(jq -r '.current_pr' "$STATE")
  WORKTREE=$(jq -r '.worktree_path // ""' "$STATE")
  [ -n "$WORKTREE" ] && cd "$WORKTREE"
else
  # === プリチェック (SKILL.md「事前確認」参照) ===

  # 1. 自分の PR 判定 → event ダウングレード設定
  ME=$(gh api user --jq .login)
  AUTHOR=$(gh pr view "$PR" --json author --jq .author.login)
  IS_OWN=false
  EVENT_DOWNGRADE=false
  if [ "$ME" = "$AUTHOR" ]; then
    IS_OWN=true
    EVENT_DOWNGRADE=true
    echo "⚠ 自分の PR (author=$ME) — REQUEST_CHANGES → COMMENT に強制ダウングレード"
  fi

  # 2. worktree 分離
  HEAD_BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)
  WORKTREE=/work/worktrees/pr$PR
  if [ ! -d "$WORKTREE" ]; then
    git fetch origin "$HEAD_BRANCH"
    git worktree add "$WORKTREE" "$HEAD_BRANCH"
  fi
  cd "$WORKTREE"

  # 3. 既存コメントスナップショット（重複指摘防止）
  gh api "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pulls/$PR/comments" \
    --paginate | jq -r '.[] | "\(.path):\(.line) [\(.user.login)] \(.body | split("\n")[0])"' \
    > /tmp/cross-review-pr$PR-existing-comments.txt

  # 4. state 初期化
  cat > "$STATE" <<JSON
{
  "started_at": "$(date -Iseconds)",
  "max_rounds": $MAX_ROUNDS,
  "rotate_after": $ROTATE_AFTER,
  "only": $(test -n "$ONLY" && echo "\"$ONLY\"" || echo "null"),
  "current_pr": $PR,
  "worktree_path": "$WORKTREE",
  "pr_author": "$AUTHOR",
  "is_own_pr": $IS_OWN,
  "event_downgrade": $EVENT_DOWNGRADE,
  "pr_history": [{"pr": $PR, "opened_at": "$(date -Iseconds)", "closed_at": null, "rounds": 0}],
  "rounds": [],
  "deferred_nits": [],
  "final": null
}
JSON
fi
```

**重要**: 以降の全ステップで `cd $WORKTREE` を強制すること。
特にサブエージェント（fix）を起動するときも、prompt 内で worktree path を明示する。

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

### 2.1 プロンプト共通要件（両 AI 必須）

両 launcher のプロンプトに以下を必ず含める:

- **headRefOid (commit_id) を明示**: `gh pr view <PR> --json headRefOid` の値。AI が
  自前で取得すると headRefOid を誤って `baseRefOid` などにする事故が多発する
- **作業 worktree の絶対パス**: 「**ファイル読み取りは必ず `/work/worktrees/pr<PR>/` 配下の絶対パスを使うこと**」
- **review body 先頭 prefix の必須化**:
  ```
  body の先頭に必ず以下の 1 行を入れてください（fence 不要、そのまま Markdown 見出しとして書く）:

  ## 🤖 cross-review | round <N> | <agent> | <event(intent)>

  例: ## 🤖 cross-review | round 1 | codex | REQUEST_CHANGES

  - <agent>: codex または gemini
  - <event>: あなたの本来の判定 (REQUEST_CHANGES / APPROVE / COMMENT)
  ```
- **event ダウングレード警告**: `is_own_pr=true` のときは `event: COMMENT` で投稿させる
  （ペイロード上は `event=COMMENT` だが、body 先頭 prefix の `<event>` には本来の intent を書く）
- **既存コメント差分**: `/tmp/cross-review-pr<PR>-existing-comments.txt` を読み、重複指摘禁止

### 2.2 codex launcher の中身

```bash
# /tmp/launch-codex-review-<PR>.sh
PR=$1
WORKTREE=/work/worktrees/pr$PR
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)
EVENT_DOWNGRADE=$(jq -r '.event_downgrade // false' /tmp/cross-review-pr$PR-state.json)

cat > /tmp/codex-review-pr$PR-prompt.md <<EOF
（上記 2.1 の要件 + /ndf:review の出力フォーマット）
- commit_id: $SHA
- worktree: $WORKTREE
- event_downgrade: $EVENT_DOWNGRADE
  → true の場合、ペイロードの "event" は "COMMENT" にすること。
    ただし body 先頭の prefix には本来の intent を書く。
EOF

# pidfile + 完了 sentinel で堅牢に
cd "$WORKTREE"
nohup codex exec --dangerously-bypass-approvals-and-sandbox \
  --config reasoning.effort=medium -C "$WORKTREE" \
  < /tmp/codex-review-pr$PR-prompt.md \
  > /tmp/codex-review-pr$PR-stdout.log \
  2> /tmp/codex-review-pr$PR-err.log &
echo $! > /tmp/codex-review-pr$PR.pid
disown
```

### 2.3 gemini launcher の中身（trusted directory 対策込み）

```bash
# /tmp/launch-gemini-review-<PR>.sh
PR=$1
WORKTREE=/work/worktrees/pr$PR
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

cat > /tmp/gemini-review-pr$PR-prompt.md <<EOF
（上記 2.1 と同じ要件。gemini 向けに「リポジトリ編集禁止、gh api 投稿のみ許可」を強調）
EOF

cd "$WORKTREE"
# ⚠ --skip-trust と GEMINI_CLI_TRUST_WORKSPACE=true は両方必須
# （worktree のような新規パスは untrusted 判定 → YOLO が "default" に降格される）
GEMINI_CLI_TRUST_WORKSPACE=true nohup gemini --yolo --skip-trust --output-format text \
  -p "$(cat /tmp/gemini-review-pr$PR-prompt.md)" \
  > /tmp/gemini-review-pr$PR-stdout.log \
  2> /tmp/gemini-review-pr$PR-err.log &
echo $! > /tmp/gemini-review-pr$PR.pid
disown
```

### 2.4 launcher 起動 + waiter（pidfile + sentinel ベース）

```bash
jq --arg ts "$(date -Iseconds)" --argjson r $ROUND --argjson p $PR \
   '.rounds += [{"round": $r, "pr": $p, "started_at": $ts}]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

[ "$ONLY" != "gemini" ] && bash /tmp/launch-codex-review-$PR.sh $PR
[ "$ONLY" != "codex" ]  && bash /tmp/launch-gemini-review-$PR.sh $PR

# === waiter ===
# codex は ^tokens used$ sentinel / gemini は pidfile + kill -0
wait_codex() {
  until grep -q '^tokens used$' /tmp/codex-review-pr$PR-err.log 2>/dev/null; do
    sleep 30
  done
}
wait_gemini() {
  local pid=$(cat /tmp/gemini-review-pr$PR.pid)
  until ! kill -0 "$pid" 2>/dev/null; do
    sleep 30
  done
}
[ "$ONLY" != "gemini" ] && wait_codex
[ "$ONLY" != "codex" ]  && wait_gemini
```

> ⚠ **罠**: `nohup ... &` でラッパーシェルは即終了し、ハーネスから
> 「タスク完了」通知が飛んでくる。これに惑わされず、上記 waiter で
> 実プロセスの完了を pidfile / sentinel で確認すること。
>
> ⚠ **`pgrep -fa <prompt>` で完了判定しない**: gemini は long `-p` プロンプトを
> 引数に持つため、`grep` のキーワード選定で誤検知する。**pidfile 必須**。

### 2.5 result.json 読み込み（intent / posted_as / by_severity を分離保存）

```bash
read_result() {
  local agent=$1
  local file=/tmp/$agent-review-pr$PR-result.json
  [ ! -s "$file" ] && { echo "❌ $agent: result 未生成" >&2; return 1; }
  jq --slurpfile r "$file" --arg agent "$agent" \
    '.rounds[-1][$agent] = {
      intent:    $r[0].event,
      posted_as: ($r[0].posted_as // $r[0].event),
      comments:  $r[0].comments_count,
      review_url: $r[0].review_url,
      by_severity: ($r[0].by_severity // {})
    }' \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
}
[ "$ONLY" != "gemini" ] && read_result codex
[ "$ONLY" != "codex" ]  && read_result gemini
```

`/ndf:review` の result.json 出力規約に `posted_as` フィールドを追加すること
（自分PR ダウングレード時に GitHub に実際送った event を残す。デフォルトは `event` と同値）。

## Step 3: 判定（intent ベース）

**重要**: ループ収束判定は `posted_as` ではなく `intent` を見る。
自分の PR で `REQUEST_CHANGES → COMMENT` にダウングレードしていても、
intent が `REQUEST_CHANGES` ならループは継続する。

```bash
CODEX_INTENT=$(jq -r ".rounds[-1].codex.intent // \"SKIP\"" "$STATE")
GEMINI_INTENT=$(jq -r ".rounds[-1].gemini.intent // \"SKIP\"" "$STATE")
# is_pass: APPROVE / SKIP のみ pass。COMMENT は「軽微な指摘あり」として 1 度は次ラウンドで再評価
is_pass() { [ "$1" = "APPROVE" ] || [ "$1" = "SKIP" ]; }

if is_pass "$CODEX_INTENT" && is_pass "$GEMINI_INTENT"; then
  jq '.final = "approved" | .ended_at = "'$(date -Iseconds)'"' "$STATE" > "$STATE.tmp"
  mv "$STATE.tmp" "$STATE"
  echo "✅ 両方 APPROVE。収束。"
  exit 0
fi
echo "→ codex=$CODEX_INTENT gemini=$GEMINI_INTENT。修正へ。"
```

**`COMMENT` の扱い**: 旧設計では `COMMENT` も pass 扱いだったが、自分の PR で
ダウングレード投稿した場合 intent が REQUEST_CHANGES のままになるため、
intent が APPROVE か SKIP のときのみ pass とする。AI が本当に COMMENT 判定したら
`intent="COMMENT"` で来るが、その場合は **指摘内容に critical/major があれば修正へ、
無ければ pass** とする 2 段判定でもよい:

```bash
# COMMENT を厳密に評価したい場合の拡張
if [ "$CODEX_INTENT" = "COMMENT" ]; then
  CRIT=$(jq -r '.rounds[-1].codex.by_severity.critical // 0' "$STATE")
  MAJ=$(jq -r '.rounds[-1].codex.by_severity.major // 0' "$STATE")
  [ "$CRIT" -eq 0 ] && [ "$MAJ" -eq 0 ] && CODEX_INTENT=APPROVE_SOFT
fi
```

## Step 4: 振動検知

`/tmp/<agent>-review-pr<PR>-payload.json` から `path:line` を抽出し、
前ラウンドと現ラウンドを `comm -12` で重複検出。50% 以上重複なら
`final = "oscillation"` で中断（PR ローテーション後はリセットなので
`ROUND_IN_PR >= 2` のみで判定）。
