---
name: cross-review
description: "PR を codex / gemini 両方にレビューさせ、両方が APPROVE になるまで `/ndf:review` → `/ndf:fix` を繰り返すクロスレビューループ"
argument-hint: "[PR番号] [--max-rounds N] [--only codex|gemini]"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# クロスレビュー収束ループ

PR を **codex と gemini 両方** にレビューさせ、両者が `APPROVE` を返すまで
`/ndf:review` と `/ndf:fix` を自動で回す。レビュー結果は PR 上にインラインコメントとして残り、
修正対応した指摘は `/ndf:fix` 経由で Resolve Conversation される。

## 引数

| 引数 | 意味 | 既定値 |
|---|---|---|
| `[PR番号]` | 対象 PR | 直前 PR / 現在のブランチに紐付く PR |
| `--max-rounds N` | 最大ラウンド数（無限ループ防止） | `5` |
| `--only codex` / `--only gemini` | 片方のみで回す（デバッグ用） | 両方 |

例:

```
/ndf:cross-review 123
/ndf:cross-review 123 --max-rounds 3
/ndf:cross-review 123 --only codex
```

## 前提

- `/ndf:review` skill が「外部AI（codex/gemini）に委譲して Reviews API ペイロードを書き出させ、メインエージェントが投稿する」フローを実装済みであること
- `/ndf:fix` skill がレビューコメント取得・修正・コミット・push・reply・Resolve Conversation・CI 待ちまで実装済みであること
- `codex` / `gemini` CLI が動作する環境であること（各 skill の前提条件を参照）

## 全体フロー

```
                +-----------------------------+
                | Round N start               |
                +--------------+--------------+
                               |
                  並列実行     v
        +----------------------+----------------------+
        |                                             |
+-------+--------+                          +---------+--------+
| /ndf:review    |                          | /ndf:review      |
|   <PR#> codex  |                          |   <PR#> gemini   |
+-------+--------+                          +---------+--------+
        |                                             |
        +----------------------+----------------------+
                               |
                               v
                +-----------------------------+
                | 判定                        |
                | - 両方 APPROVE → 終了      |
                | - どちらか REQUEST_CHANGES |
                |   → /ndf:fix 起動          |
                +--------------+--------------+
                               |
                               v
                +-----------------------------+
                | /ndf:fix <PR#>              |
                | - 修正コミット & push       |
                | - reply + Resolve Conv.     |
                | - CI 完了待ち               |
                +--------------+--------------+
                               |
                               v
                +-----------------------------+
                | 収束チェック                |
                | - max-rounds 到達 → 中断    |
                | - 振動検知 → 中断           |
                +--------------+--------------+
                               |
                               v
                          Round N+1 へ
```

## 状態ファイル

ループ進捗は以下に永続化する（中断 / 再開 / 振動検知のため）:

`/tmp/cross-review-pr<番号>-state.json`

```json
{
  "pr": 123,
  "started_at": "2026-05-12T...",
  "max_rounds": 5,
  "only": null,
  "rounds": [
    {
      "round": 1,
      "started_at": "...",
      "codex": {
        "event": "REQUEST_CHANGES",
        "comments": 5,
        "review_url": "https://github.com/.../pull/123#pullrequestreview-...",
        "payload_path": "/tmp/codex-review-pr123-payload.json"
      },
      "gemini": {
        "event": "REQUEST_CHANGES",
        "comments": 3,
        "review_url": "...",
        "payload_path": "/tmp/gemini-review-pr123-payload.json"
      },
      "fix": {
        "commit": "abc123",
        "resolved_threads": 8,
        "ci_status": "SUCCESS"
      },
      "ended_at": "..."
    }
  ],
  "final": null
}
```

`final` は終了時に以下のいずれかを設定:
- `"approved"` — 両方 APPROVE で正常終了
- `"max_rounds"` — max-rounds 到達で中断
- `"oscillation"` — 振動検知で中断
- `"error"` — AI 呼び出し or fix 失敗で中断

## 詳細手順

### Step 0: 準備

```bash
PR=<引数 or 直前PR>
MAX_ROUNDS=5  # --max-rounds の引数解析
ONLY=        # --only の引数解析（"codex" / "gemini" / 空）

STATE=/tmp/cross-review-pr$PR-state.json

# 既存状態の引き継ぎ（中断 → 再実行）
if [ -f "$STATE" ] && jq -e '.final == null' "$STATE" >/dev/null; then
  echo "前回中断した状態から再開します（round=$(jq '.rounds | length' "$STATE")）"
else
  cat > "$STATE" <<JSON
{
  "pr": $PR,
  "started_at": "$(date -Iseconds)",
  "max_rounds": $MAX_ROUNDS,
  "only": $(test -n "$ONLY" && echo "\"$ONLY\"" || echo "null"),
  "rounds": [],
  "final": null
}
JSON
fi
```

### Step 1: Round 開始

```bash
ROUND=$(jq '.rounds | length' "$STATE")
ROUND=$((ROUND + 1))

if [ "$ROUND" -gt "$MAX_ROUNDS" ]; then
  jq '.final = "max_rounds"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "❌ max_rounds 到達。中断。"
  exit 1
fi

echo "=== Round $ROUND / $MAX_ROUNDS ==="
```

### Step 2: codex / gemini を並列レビュー

**重要**: `/ndf:review` は slash command（skill）であり、メインエージェントが手動で読み込んで実行する。
ここではメインエージェントが以下を **並列バックグラウンド** で実行することを記述する:

```bash
# codex 側
if [ "$ONLY" != "gemini" ]; then
  # /ndf:review の codex 委譲フロー（plugins/ndf/skills/review/SKILL.md 参照）に従い、
  # codex を起動して /tmp/codex-review-pr$PR-payload.json を生成
  # 完了検知: grep -q '^tokens used$' /tmp/codex-review-pr$PR-err.log
  # 詳細は /ndf:codex skill を参照
  : "codex review backgrounded"
fi &
CODEX_PID=$!

# gemini 側
if [ "$ONLY" != "codex" ]; then
  # /ndf:review の gemini 委譲フロー（plugins/ndf/skills/review/SKILL.md 参照）に従い、
  # gemini を起動して /tmp/gemini-review-pr$PR-payload.json を生成
  # 完了検知: プロセス exit（kill -0）
  # 詳細は /ndf:gemini skill を参照
  : "gemini review backgrounded"
fi &
GEMINI_PID=$!

# 両方の完了を待つ
wait $CODEX_PID 2>/dev/null
wait $GEMINI_PID 2>/dev/null
```

実装の要点:
- 並列実行することで wall-clock を短縮（codex 5〜10 分 + gemini 1〜5 分が合計 = max(両者)）
- 片方が失敗しても他方は走り切らせる（fail-fast しない）
- 完了検知は各 skill の sentinel に従う（codex: `^tokens used$` / gemini: プロセス exit）

### Step 3: ペイロード投稿

各 AI が書き出した JSON ペイロードを `gh api` で PR に投稿する
（詳細は `/ndf:review` skill の「委譲結果の投稿」セクション参照）:

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

post_review() {
  local agent=$1
  local payload=/tmp/$agent-review-pr$PR-payload.json
  [ ! -s "$payload" ] && { echo "❌ $agent: payload 取得失敗" >&2; return 1; }

  jq --arg sha "$SHA" '.commit_id = $sha' "$payload" > /tmp/post-payload.json
  local result=$(gh api -X POST "repos/$OWNER_REPO/pulls/$PR/reviews" --input /tmp/post-payload.json)
  local review_url=$(echo "$result" | jq -r '.html_url')
  local event=$(jq -r '.event' "$payload")
  local n=$(jq '.comments | length' "$payload")

  echo "$agent: event=$event comments=$n url=$review_url"

  # state に記録
  jq --arg agent "$agent" --arg event "$event" --arg url "$review_url" --argjson n $n \
     --arg path "$payload" \
    ".rounds[-1].$agent = {event: \$event, comments: \$n, review_url: \$url, payload_path: \$path}" \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
}

# round エントリを新規追加
jq --arg ts "$(date -Iseconds)" --argjson r $ROUND \
   '.rounds += [{"round": $r, "started_at": $ts}]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

[ "$ONLY" != "gemini" ] && post_review codex
[ "$ONLY" != "codex" ]  && post_review gemini
```

### Step 4: 判定

```bash
CODEX_EVENT=$(jq -r ".rounds[-1].codex.event // \"SKIP\"" "$STATE")
GEMINI_EVENT=$(jq -r ".rounds[-1].gemini.event // \"SKIP\"" "$STATE")

# 両方 APPROVE（SKIP は ONLY モード時の不在を意味するので合格扱い）
is_pass() { [ "$1" = "APPROVE" ] || [ "$1" = "SKIP" ]; }

if is_pass "$CODEX_EVENT" && is_pass "$GEMINI_EVENT"; then
  jq '.final = "approved" | .ended_at = "'$(date -Iseconds)'"' \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "✅ 両方 APPROVE。収束。"
  # 作業完了報告へ
  exit 0
fi

echo "→ codex=$CODEX_EVENT gemini=$GEMINI_EVENT。修正へ進む。"
```

### Step 5: 振動検知

同じ指摘が連続 2 ラウンドで出ているかチェック（fix が効いていないサイン）:

```bash
if [ "$ROUND" -ge 2 ]; then
  # 直前 round の comments と現 round の comments を path:line で比較
  prev_keys=$(jq -r ".rounds[-2] | (.codex.payload_path, .gemini.payload_path) | select(.)" "$STATE" \
              | xargs -I{} jq -r '.comments[] | "\(.path):\(.line)"' {} | sort -u)
  curr_keys=$(jq -r ".rounds[-1] | (.codex.payload_path, .gemini.payload_path) | select(.)" "$STATE" \
              | xargs -I{} jq -r '.comments[] | "\(.path):\(.line)"' {} | sort -u)
  overlap=$(comm -12 <(echo "$prev_keys") <(echo "$curr_keys") | wc -l)
  total=$(echo "$curr_keys" | wc -l)

  if [ "$total" -gt 0 ] && [ "$overlap" -ge $((total / 2)) ]; then
    jq '.final = "oscillation"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
    echo "⚠️ 振動検知: 同じ指摘が 50% 以上繰り返されている。中断してユーザ判断を仰ぐ。"
    exit 2
  fi
fi
```

### Step 6: `/ndf:fix` を呼ぶ

`/ndf:fix <PR#>` skill を実行する（`plugins/ndf/skills/fix/SKILL.md` 参照）。要点:
- 両方のレビューコメント（インライン）を fix skill が取得 → 修正 → コミット & push
- 各コメントに reply + Resolve Conversation
- CI 完了を待つ（`gh pr checks --watch`）
- 失敗したら state に記録して中断:

```bash
# fix の実行（メインエージェントが /ndf:fix の手順を実行）
# 成果として以下を取得:
FIX_COMMIT=$(git rev-parse HEAD)
FIX_CI=$(gh pr checks "$PR" --json state -q '[.[].state] | unique | join(",")')
# resolved_threads は fix skill 内で resolveReviewThread した件数

jq --arg sha "$FIX_COMMIT" --arg ci "$FIX_CI" --argjson n "$RESOLVED_COUNT" \
   '.rounds[-1].fix = {commit: $sha, resolved_threads: $n, ci_status: $ci}
   | .rounds[-1].ended_at = "'$(date -Iseconds)'"' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

if [[ "$FIX_CI" == *"FAILURE"* ]]; then
  jq '.final = "error"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "❌ CI が失敗。中断してユーザ判断を仰ぐ。"
  exit 3
fi
```

### Step 7: 次ラウンドへ

Step 1 に戻る。

## 終了条件

| `final` | 意味 | 終了コード |
|---|---|---|
| `approved` | 両方 APPROVE で正常終了 | 0 |
| `max_rounds` | max-rounds 到達 | 1 |
| `oscillation` | 同じ指摘が連続して残り続けるため中断（fix が収束しない） | 2 |
| `error` | AI 呼び出し or fix or CI 失敗 | 3 |

中断時は state ファイルを残し、ユーザに以下を含めて報告:
- 中断理由
- 残った指摘の path:line リスト
- 各 round の review URL
- 次のアクション提案（手動で対処すべき指摘 / ユーザ判断要の論点）

## 並列実行のヒント

codex と gemini を本当に並列実行するには:

```bash
# 同一プロンプトを両方に渡し、別々の出力ファイルへ
# （プロンプト生成は共通化、CLI 呼び出しのみ別プロセス）
( /tmp/codex-launcher.sh ) &
CODEX_PID=$!
( /tmp/gemini-launcher.sh ) &
GEMINI_PID=$!

# 個別 PID で完了待ち
wait $CODEX_PID; CODEX_EXIT=$?
wait $GEMINI_PID; GEMINI_EXIT=$?
```

エージェントハーネスのシェルタイムアウトに引っかかる場合は、本 skill 自体を
**バックグラウンド + ポーリング待機** として扱うか、`ScheduleWakeup` で
ラウンド境界ごとに再開する設計に切り替える。

## アンチパターン

- **`gh api` を外部 AI に直接叩かせる** — 外部AI は JSON ペイロード生成までに留め、投稿はメインエージェントが行う（SHA 更新・パス検証を集約するため）
- **`/ndf:fix` を呼ばずに自力で修正する** — 修正フローは fix skill に集約。重複実装は禁物
- **max-rounds なしで回す** — 無限ループの温床
- **振動検知をスキップする** — 同じ指摘が永遠に残り続けるケースがある（仕様判断要件など）
- **CI 失敗を無視して次ラウンドに進む** — fix の前提が壊れていれば次回も失敗するため、CI 失敗時は即中断

## 作業完了報告（必須）

ループ終了後、ユーザに以下を報告:

- **最終ステータス**: `approved` / `max_rounds` / `oscillation` / `error`
- **ラウンド数**: 実行した round 数 / max
- **各ラウンドのサマリ表**:
  | round | codex | gemini | fix commit | CI |
  |---|---|---|---|---|
  | 1 | REQ (5件) | REQ (3件) | abc123 | ✅ |
  | 2 | APPROVE | APPROVE | — | — |
- **残課題**（中断時のみ）: 未解決の指摘 path:line と内容
- **PR URL** と各 round の review URL

詳細な指摘内容は PR 上のインラインコメントに残っているため、ユーザ宛報告では繰り返さない。

## 関連

- `/ndf:review` — 単発レビュー（本 skill が内部で利用）
- `/ndf:fix` — 修正対応（本 skill が内部で利用）
- `/ndf:codex` — codex CLI 呼び出し手順
- `/ndf:gemini` — gemini CLI 呼び出し手順
- `/ndf:resolve-pr-comments` — Resolve Conversation の詳細
