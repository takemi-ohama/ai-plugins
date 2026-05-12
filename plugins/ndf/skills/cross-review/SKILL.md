---
name: cross-review
description: "PR を codex / gemini 両方にレビューさせ、両方 APPROVE まで /ndf:review → /ndf:fix を自動ループ。サブエージェント分離・PR ローテーション・nit 集約でメイン context 消費を最小化"
argument-hint: "[PR番号] [--max-rounds N] [--rotate-after K] [--only codex|gemini]"
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

PR を **codex / gemini 両方** にレビューさせ、両者が `APPROVE` を返すまで
`/ndf:review` と `/ndf:fix` を自動で回す。

## 設計方針（重要）

長丁場が予想されるため、以下の方針で **メインセッションの context 消費を最小化** する:

| 観点 | 方針 |
|---|---|
| レビュー投稿 | **AI 自身が `gh api` で PR に直接投稿**。メインはペイロードを保持しない |
| 修正 | **必ずサブエージェント (`general-purpose`) で実行**。メイン context に diff は載せない |
| ユーザ問い合わせ | 自動判断を最大化（`critical`/`major`/`minor` は自動修正、`nit` は最後にまとめて 1 回だけ問い合わせ） |
| 状態の永続化 | `/tmp/cross-review-pr<番号>-state.json` に集約。中断・再開可能 |
| 長尺PR対策 | **`--rotate-after` ラウンドで PR をローテーション**（squash + 新ブランチ + 新 PR）。会話が長くなる前に巻き直す |
| 振動検知 | 同じ指摘が 2 round で 50%以上重複したら中断 |

## 引数

| 引数 | 意味 | 既定 |
|---|---|---|
| `[PR番号]` | 対象 PR（省略時は直前 PR / 現在ブランチ） | — |
| `--max-rounds N` | 全体最大ラウンド数（PR ローテーションを含む通算） | `6` |
| `--rotate-after K` | この round 数で未収束なら PR ローテーション | `2` |
| `--only codex` / `--only gemini` | 片方だけで回す（デバッグ用） | 両方 |

例:

```
/ndf:cross-review 123
/ndf:cross-review 123 --max-rounds 4 --rotate-after 2
/ndf:cross-review 123 --only codex
```

## 前提

- `/ndf:review` が **AI 直接投稿**（外部 AI 自身が `gh api` で投稿）に対応していること
- `/ndf:fix` が **サブエージェント起動 + 重要度ベース自動修正** に対応していること
- `codex` / `gemini` CLI が動作し、`gh` CLI が認証済みであること
- `Agent(subagent_type="general-purpose", ...)` でサブエージェントを起動できること

## 全体フロー

```
                +---------------------------------------+
                | Round N start (current_pr = PR#)      |
                +--------------------+------------------+
                                     |
                  並列バックグラウンド  v
        +----------------------------+----------------------------+
        |                                                         |
   /ndf:review <PR#> codex                          /ndf:review <PR#> gemini
   (codex 自身が gh api で投稿)                     (gemini 自身が gh api で投稿)
   → /tmp/codex-review-pr<#>-result.json            → /tmp/gemini-review-pr<#>-result.json
        |                                                         |
        +----------------------------+----------------------------+
                                     |
                                     v
                +---------------------------------------+
                | 判定                                  |
                | - 両方 APPROVE → 終了                |
                | - どちらか REQUEST_CHANGES → 修正へ  |
                +--------------------+------------------+
                                     |
                                     v
                +---------------------------------------+
                | Agent(subagent_type="general-purpose")     |
                |   prompt="/ndf:fix <PR#> --defer-nit" |
                | → /tmp/fix-pr<#>-result.json         |
                +--------------------+------------------+
                                     |
                                     v
                +---------------------------------------+
                | 収束チェック                         |
                | - max-rounds 到達 → 中断             |
                | - 振動検知 → 中断                    |
                | - round_in_pr >= rotate_after        |
                |   → PR ローテーション                |
                +--------------------+------------------+
                                     |
                                     v
                              Round N+1 へ
                                     |
            (最後に1回) nit deferred 一覧をユーザに問い合わせ
```

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

## 詳細手順

### Step 0: 準備 + 既存 state 引き継ぎ

```bash
PR=<引数 or 直前PR>
MAX_ROUNDS=6     # 既定
ROTATE_AFTER=2   # 既定
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

### Step 1: Round 開始判定

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
  # → 終了報告へ
  exit 1
fi

echo "=== Round $ROUND / $MAX_ROUNDS (PR #$PR, round_in_pr=$ROUND_IN_PR) ==="
```

### Step 2: codex / gemini を並列レビュー（AI 直接投稿）

**実装の要点**:
- メインは `/ndf:review <PR> codex` / `/ndf:review <PR> gemini` 相当のフローを **並列バックグラウンド** で起動するだけ
- 各 AI が `gh api` で投稿し、`/tmp/<agent>-review-pr<PR>-result.json` にサマリを書き出す
- メインはそのサマリを読むだけ。**ペイロード本体はメイン context に載せない**

```bash
# round エントリ追加
jq --arg ts "$(date -Iseconds)" --argjson r $ROUND --argjson p $PR \
   '.rounds += [{"round": $r, "pr": $p, "started_at": $ts}]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

# codex 並列起動（詳細は /ndf:review + /ndf:codex skill 参照）
if [ "$ONLY" != "gemini" ]; then
  ( /tmp/launch-codex-review.sh $PR ) &
  CODEX_PID=$!
fi

# gemini 並列起動（詳細は /ndf:review + /ndf:gemini skill 参照）
if [ "$ONLY" != "codex" ]; then
  ( /tmp/launch-gemini-review.sh $PR ) &
  GEMINI_PID=$!
fi

# 完了待ち（codex: ^tokens used$ sentinel / gemini: process exit）
[ "$ONLY" != "gemini" ] && wait $CODEX_PID
[ "$ONLY" != "codex" ]  && wait $GEMINI_PID

# 各 AI の result.json を読み込んで state に記録
read_result() {
  local agent=$1
  local file=/tmp/$agent-review-pr$PR-result.json
  [ ! -s "$file" ] && { echo "❌ $agent: result 未生成" >&2; return 1; }

  local status=$(jq -r '.status' "$file")
  if [ "$status" = "failed" ]; then
    echo "⚠️ $agent: AI 投稿失敗 → メインがフォールバック投稿（/ndf:review 参照）"
    # フォールバック投稿 ... (省略)
  fi

  jq --slurpfile r "$file" --arg agent "$agent" \
    ".rounds[-1].$agent = {event: \$r[0].event, comments: \$r[0].comments_count, review_url: \$r[0].review_url}" \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
}

[ "$ONLY" != "gemini" ] && read_result codex
[ "$ONLY" != "codex" ]  && read_result gemini
```

### Step 3: 判定

```bash
CODEX_EVENT=$(jq -r ".rounds[-1].codex.event // \"SKIP\"" "$STATE")
GEMINI_EVENT=$(jq -r ".rounds[-1].gemini.event // \"SKIP\"" "$STATE")

is_pass() { [ "$1" = "APPROVE" ] || [ "$1" = "SKIP" ] || [ "$1" = "COMMENT" ]; }

if is_pass "$CODEX_EVENT" && is_pass "$GEMINI_EVENT"; then
  jq '.final = "approved" | .ended_at = "'$(date -Iseconds)'"' "$STATE" > "$STATE.tmp"
  mv "$STATE.tmp" "$STATE"
  echo "✅ 両方 APPROVE。収束。"
  # → 終了報告（nit deferred 一覧をユーザ提示）
  exit 0
fi

echo "→ codex=$CODEX_EVENT gemini=$GEMINI_EVENT。修正へ。"
```

### Step 4: 振動検知

`/tmp/<agent>-review-pr<PR>-payload.json`（前ラウンドのもの含めて）から `path:line` を抽出して比較。
50%以上重複なら中断:

```bash
if [ "$ROUND_IN_PR" -ge 2 ]; then
  # ... (前ラウンドと現ラウンドの payload.path:line を取って comm -12 で重複検出)
  # ROUND_IN_PR を使う点に注意（PR ローテーション後はリセット）
  :
fi
```

（詳細省略。前バージョンと同等）

### Step 5: 修正 — **必ずサブエージェント経由**

**メインセッションでは修正コードを書かない。** `/ndf:fix` を `general-purpose` サブエージェントで起動:

```python
# 擬似コード（メインエージェントから）
result = Agent(
    subagent_type="general-purpose",
    description=f"Fix PR #{PR} (round {ROUND})",
    prompt=f"""
/ndf:fix {PR} --defer-nit を実行してください。

## コンテキスト
- リポジトリ: {OWNER_REPO}
- PR: #{PR} (round {ROUND_IN_PR}/{ROTATE_AFTER})
- 前ラウンドのレビュー結果:
  - codex review: {CODEX_REVIEW_URL} (event={CODEX_EVENT}, {CODEX_COMMENT_COUNT}件)
  - gemini review: {GEMINI_REVIEW_URL} (event={GEMINI_EVENT}, {GEMINI_COMMENT_COUNT}件)

## ポリシー
- critical / major / minor は自動修正
- nit は deferred として記録のみ（修正しない）
- bot 指摘が誤読していたら修正せず reply で説明（rejected として記録）

## 戻り値
- /tmp/fix-pr{PR}-result.json に書き出すこと
- メインへの戻り値は: 修正件数 / deferred 件数 / rejected 件数 / commit SHA / CI 状態
""",
)
```

サブエージェント完了後、メインは `/tmp/fix-pr$PR-result.json` を読んで state を更新:

```bash
FIX=/tmp/fix-pr$PR-result.json
[ ! -s "$FIX" ] && { echo "❌ fix サブエージェントが戻り値ファイルを生成しなかった" >&2; exit 3; }

jq --slurpfile f "$FIX" \
   '.rounds[-1].fix = {
      commit: $f[0].fix_commit,
      fixed: $f[0].fixed_count,
      deferred: ($f[0].deferred | length),
      rejected: ($f[0].rejected | length),
      ci: $f[0].ci_status
    }
    | .rounds[-1].ended_at = "'$(date -Iseconds)'"
    | .deferred_nits += [
        $f[0].deferred[] | . + {pr: '$PR', round: '$ROUND'}
      ]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

CI=$(jq -r ".rounds[-1].fix.ci" "$STATE")
if [ "$CI" = "FAILURE" ]; then
  jq '.final = "error"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "❌ CI 失敗。中断。"
  exit 3
fi
```

### Step 6: PR ローテーション判定

```bash
ROUND_IN_PR=$(jq --argjson p $PR '[.rounds[] | select(.pr == $p)] | length' "$STATE")

if [ "$ROUND_IN_PR" -ge "$ROTATE_AFTER" ] && [ "$TOTAL_ROUNDS" -lt "$MAX_ROUNDS" ]; then
  echo "🔄 PR #$PR が $ROUND_IN_PR round 経過。ローテーション実施。"
  rotate_pr
fi
```

#### `rotate_pr` の実装

```bash
rotate_pr() {
  local old_pr=$PR
  local branch=$(git branch --show-current)
  local base=$(gh pr view "$old_pr" --json baseRefName -q .baseRefName)
  local title=$(gh pr view "$old_pr" --json title -q .title)
  local new_branch="${branch}-r$(date +%H%M%S)"

  # 1. 既存ブランチを squash して新ブランチに
  git checkout -b "$new_branch"
  git reset --soft "origin/$base"
  git commit -m "$(cat <<EOF
$title

(cross-review rotation: PR #$old_pr を squash 統合)
EOF
)"
  git push -u origin "$new_branch"

  # 2. 旧 PR を close（コメント残し）
  gh pr comment "$old_pr" --body "🔄 cross-review ループ進行中のため、本 PR を close し新規 PR #(後述) に巻き直します。 round_in_pr=$ROUND_IN_PR で長尺化を回避。"
  gh pr close "$old_pr"

  # 3. 新 PR 作成
  local new_pr_url=$(gh pr create --base "$base" --title "$title (rotated)" --body "$(cat <<EOF
## Summary
旧 PR #$old_pr をベースに、cross-review クロスレビューループの継続。
旧 PR は round_in_pr=$ROUND_IN_PR で巻き直しのため close 済み。

旧 PR の resolved スレッドは既に修正済み事項。残った指摘はこの PR で再評価する。

<!-- I want to review in Japanese. -->
EOF
)")
  local new_pr=$(echo "$new_pr_url" | grep -oP '/pull/\K\d+')

  # 4. state 更新
  jq --argjson old "$old_pr" --argjson new "$new_pr" --arg ts "$(date -Iseconds)" \
    '.pr_history[-1].closed_at = $ts
     | .pr_history[-1].rounds = (.rounds | map(select(.pr == $old)) | length)
     | .pr_history += [{"pr": $new, "opened_at": $ts, "closed_at": null, "rounds": 0}]
     | .current_pr = $new' \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

  PR=$new_pr
  echo "✅ 新 PR #$new_pr に移行: $new_pr_url"
}
```

### Step 7: 次ラウンドへ

Step 1 に戻る。

### Step 8: 終了処理 — deferred nit のバッチ問い合わせ

ループ終了時（`final` 確定後）、`deferred_nits` が残っていれば **1 回だけ** ユーザに問い合わせる:

```bash
DEFERRED_COUNT=$(jq '.deferred_nits | length' "$STATE")
if [ "$DEFERRED_COUNT" -gt 0 ]; then
  echo "=== 残った nit 指摘 ($DEFERRED_COUNT 件) ==="
  jq -r '.deferred_nits[] | "- [\(.severity)] \(.path):\(.line) — \(.summary)"' "$STATE"
  echo ""
  echo "これらの nit を一括対応する場合は再度 /ndf:fix <PR#> を起動してください。"
fi
```

UI 上は **AskUserQuestion で 1 回だけ** 「nit 一括対応する / しない / 個別選択」を選ばせるのが望ましい。

## アンチパターン

- ❌ **修正をメインセッション内で行う** — context が一気に膨れる。必ずサブエージェント
- ❌ **AI に Markdown だけ返させる** — メインがパース・投稿する設計は禁物。AI 直接投稿
- ❌ **nit を都度ユーザに問う** — 必ずバッチ集約して最後に 1 回
- ❌ **`max-rounds` なしで回す** — 無限ループの温床
- ❌ **PR ローテーションを忘れる** — 100+ コメントの巨大 PR になる
- ❌ **CI 失敗を無視して次ラウンド** — 即中断してユーザ判断

## メイン context 節約の工夫

1. **大きいファイルはメイン context に載せない**: payload / err.log / diff はすべて `/tmp/` に置き、メインは state.json と result.json だけ読む
2. **サブエージェント分離**: 修正は別 context window で実行
3. **PR ローテーション**: 1 PR あたりの会話履歴を抑える
4. **AI 直接投稿**: 中間ペイロードがメインを通らない
5. **state.json で再開可能**: メインが落ちても次回起動時に続きから

## 作業完了報告（必須）

ループ終了後、メインからユーザへの報告:

- **最終ステータス**: `approved` / `max_rounds` / `oscillation` / `error`
- **総ラウンド数 / PR 数**: 例: `5 rounds / 2 PRs (rotated 1 回)`
- **PR 履歴**: 各 PR 番号 + closed/open 状態 + round 数
- **各ラウンドのサマリ表**:
  | round | PR | codex | gemini | fix | CI |
  |---|---|---|---|---|---|
  | 1 | #123 | REQ (5) | REQ (3) | abc123 (5 fixed, 2 deferred) | ✅ |
  | 2 | #123 | REQ (2) | APP | def456 (2 fixed) | ✅ |
  | 3 | #145 | APP | APP | — | — |
- **残 deferred nit リスト**（ユーザ判断要）
- **rejected 件数**（bot 誤指摘で却下したもの）
- **最終 PR URL**

詳細は PR 上のインラインコメントと state.json に残っているため、本報告では繰り返さない。

## 関連

- `/ndf:review` — 単発レビュー（AI 直接投稿対応）
- `/ndf:fix` — 修正対応（サブエージェント起動対応）
- `/ndf:codex` — codex CLI 呼び出し手順
- `/ndf:gemini` — gemini CLI 呼び出し手順
- `/ndf:resolve-pr-comments` — Resolve Conversation の詳細
- `general-purpose` エージェント — fix 実行用サブエージェント
