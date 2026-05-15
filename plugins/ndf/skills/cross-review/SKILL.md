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

詳細手順は `docs/` 配下に分割している（このファイルは概要のみ）:

- [docs/01-state-and-review.md](docs/01-state-and-review.md) — Step 0〜4 (state init / round / 並列レビュー / 判定 / 振動検知)
- [docs/02-fix-and-rotation.md](docs/02-fix-and-rotation.md) — Step 5〜8 (サブエージェント修正 / PR ローテーション / 終了処理)

## 設計方針

長丁場が予想されるため **メインセッションの context 消費を最小化** する:

| 観点 | 方針 |
|---|---|
| レビュー投稿 | **AI 自身が `gh api` で PR に直接投稿**。メインはペイロードを保持しない |
| 修正 | **必ずサブエージェント (`general-purpose`) で実行**。メイン context に diff は載せない |
| ユーザ問い合わせ | 自動判断を最大化（`critical`/`major`/`minor` は自動修正、`nit` は最後にまとめて 1 回だけ問い合わせ） |
| 状態の永続化 | `/tmp/cross-review-pr<番号>-state.json` に集約。中断・再開可能 |
| 長尺PR対策 | **`--rotate-after` ラウンドで PR をローテーション**（squash + 新ブランチ + 新 PR） |
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

- `/ndf:review` が **AI 直接投稿**（外部 AI 自身が `gh api` で投稿）に対応
- `/ndf:fix` が **サブエージェント起動 + 重要度ベース自動修正 + Resolve Conversation** に対応
- `codex` / `gemini` CLI が動作し、`gh` CLI が認証済み
- `Agent(subagent_type="general-purpose", ...)` でサブエージェントを起動可能

## 事前確認（Step 0 の前に必ず実行）

ループ開始前に **4 つのプリチェック** を行い、失敗パターンを未然に塞ぐ:

### 1. 自分の PR かどうか判定（必須）

GitHub は **自分の PR には `event: REQUEST_CHANGES` でレビューを投稿できない**
（`HTTP 422: Review Can not request changes on your own pull request`）。
判定が必要:

```bash
PR=<番号>
ME=$(gh api user --jq .login)
AUTHOR=$(gh pr view "$PR" --json author --jq .author.login)
if [ "$ME" = "$AUTHOR" ]; then
  EVENT_DOWNGRADE=1   # 後段で REQUEST_CHANGES → COMMENT に強制ダウングレード
  echo "⚠ 自分の PR — event を COMMENT にダウングレードして投稿"
fi
```

**重要**: state.json には **intent（元の AI 判定）と posted（実際に投稿した event）の両方を保持** すること。
ループ判定は intent ベースで行い、GitHub 投稿は posted ベースに従う:

```json
"codex": {
  "intent": "REQUEST_CHANGES",   // ← AI の本来の判定。ループ収束判定に使う
  "posted_as": "COMMENT",        // ← 422 回避でダウングレードした結果
  "comments": 5, "review_url": "..."
}
```

`is_pass()` は `intent` を見ること。`posted_as` で `COMMENT` でもループは続く。

### 2. worktree 分離（並行セッション対策）

別セッションが同じリポジトリで作業している場合、main checkout を奪い合わないよう
**専用 worktree** を作る:

```bash
mkdir -p /work/worktrees
HEAD_BRANCH=$(gh pr view "$PR" --json headRefName --jq .headRefName)
git fetch origin "$HEAD_BRANCH"
git worktree add "/work/worktrees/pr$PR" "$HEAD_BRANCH"
# 以降の全ステップで cd /work/worktrees/pr$PR を強制
```

state.json に `"worktree_path": "/work/worktrees/pr<PR>"` を記録し、サブエージェント
にも明示すること。

### 3. gemini の trusted directory チェック

worktree のような新規パスは untrusted と判定され、`--yolo` でも
`Approval mode overridden to "default"` で実質無効化される。**必ず以下を併用**:

```bash
GEMINI_CLI_TRUST_WORKSPACE=true gemini --yolo --skip-trust --output-format text -p "..."
```

（`--skip-trust` 単独でも可だが、env var 併用が確実）

### 4. 既存コメント・既存レビューの確認

重複指摘を避けるため、既存レビュー一覧を取得しておく:

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --paginate \
  | jq -r '.[] | "\(.path):\(.line) [\(.user.login)] \(.body | split("\n")[0])"' \
  > /tmp/cross-review-pr$PR-existing-comments.txt
```

これを launcher のプロンプトに添付して「重複指摘禁止」を徹底させる。

## 全体フロー

```
   ┌──────────────────────────────────────────────────┐
   │ 事前確認 (loop 開始前に 1 回だけ)                │
   │  - 自分の PR か判定 → event ダウングレード設定   │
   │  - worktree 作成 (/work/worktrees/pr<PR>)        │
   │  - 既存コメントスナップショット保存              │
   │  - state.json 初期化                             │
   └──────────────────────┬───────────────────────────┘
                          │
                          v
   ┌──────────────────────────────────────────────────┐
   │ Round N start (current_pr = PR#)                 │
   └──────────────────────┬───────────────────────────┘
                          │ 並列バックグラウンド
        ┌─────────────────┴─────────────────┐
        │                                   │
   /ndf:review codex                   /ndf:review gemini
   (--skip-trust 必須)                 (codex の sentinel/pidfile で完了検知)
   body 先頭 prefix:                   body 先頭 prefix:
   "## 🤖 cross-review | round N |     "## 🤖 cross-review | round N |
    codex | <intent>"                   gemini | <intent>"
   → result.json (intent + posted_as)  → result.json (intent + posted_as)
        │                                   │
        └─────────────────┬─────────────────┘
                          v
   ┌──────────────────────────────────────────────────┐
   │ 判定 (intent ベース)                             │
   │  - 両方 APPROVE/SKIP → 終了                     │
   │  - 一方でも REQUEST_CHANGES → 修正へ            │
   └──────────────────────┬───────────────────────────┘
                          v
   ┌──────────────────────────────────────────────────┐
   │ Agent(subagent_type="general-purpose")           │
   │   /ndf:fix <PR#> --defer-nit (worktree 内で実行) │
   │   - critical/major/minor 修正 + push             │
   │   - 修正 thread を reply + resolveReviewThread   │
   │   - deferred/rejected は reply のみ              │
   │ → /tmp/fix-pr<#>-result.json                     │
   └──────────────────────┬───────────────────────────┘
                          v
   ┌──────────────────────────────────────────────────┐
   │ 収束チェック                                     │
   │  - max-rounds 到達 → 中断                       │
   │  - 振動検知 (50%重複) → 中断                    │
   │  - CI failure (code) → 中断                     │
   │  - CI failure (meta only) → 継続 (Assignees 等) │
   │  - round_in_pr >= rotate_after → PR rotation    │
   └──────────────────────┬───────────────────────────┘
                          v
                    Round N+1 へ
                          │
        (最後に 1 回) deferred nit 一覧をユーザに問い合わせ
```

## 実行ステップ概要

各ステップの bash 詳細は `docs/` を参照。

1. **Step 0 — 準備 + state 引き継ぎ**: `/tmp/cross-review-pr<PR>-state.json` を
   初期化 or 再開。詳細: [docs/01](docs/01-state-and-review.md#step-0-準備--既存-state-引き継ぎ)
2. **Step 1 — Round 開始判定**: `max-rounds` 超過チェック。
   詳細: [docs/01](docs/01-state-and-review.md#step-1-round-開始判定)
3. **Step 2 — 並列レビュー**: codex / gemini launcher を並列起動、各 AI が
   `gh api` で投稿。詳細: [docs/01](docs/01-state-and-review.md#step-2-codex--gemini-並列レビューai-直接投稿)
4. **Step 3 — 判定**: 両方 `APPROVE` なら終了、片方でも `REQUEST_CHANGES` なら
   修正へ。詳細: [docs/01](docs/01-state-and-review.md#step-3-判定)
5. **Step 4 — 振動検知**: 前ラウンドと `path:line` 重複 50% 以上で中断。
   詳細: [docs/01](docs/01-state-and-review.md#step-4-振動検知)
6. **Step 5 — サブエージェント修正**: `general-purpose` で `/ndf:fix --defer-nit`
   を実行。詳細: [docs/02](docs/02-fix-and-rotation.md#step-5-修正--必ずサブエージェント経由)
7. **Step 6 — PR ローテーション判定**: `round_in_pr >= rotate-after` なら
   `rotate_pr` 実行。詳細: [docs/02](docs/02-fix-and-rotation.md#step-6-pr-ローテーション判定)
8. **Step 7 — 次ラウンドへ** → Step 1 に戻る
9. **Step 8 — 終了処理**: deferred nit をバッチ問い合わせ（1 回だけ）。
   詳細: [docs/02](docs/02-fix-and-rotation.md#step-8-終了処理--deferred-nit-のバッチ問い合わせ)

## レビュー body の必須 identifier prefix

人間アカウントから AI が投稿するため、**GitHub UI 上では誰のレビューか分からない**。
両 launcher のプロンプトで以下の prefix を **body の先頭に必ず付ける** よう強制する:

```
## 🤖 cross-review | round 1 | codex | REQUEST_CHANGES

(残り `## 総評` 以降は従来通り)
```

書式: `## 🤖 cross-review | round <N> | <agent> | <event>`

- `<agent>`: `codex` / `gemini` のいずれか
- `<event>`: AI の本来の判定（`REQUEST_CHANGES` / `APPROVE` / `COMMENT`）
  `posted_as` ではなく `intent` を書く（ユーザが「本当は REQ だった」を一目で読める）

インラインコメント側は従来通り `[major / 正確性]` などの `[重要度 / カテゴリ]` を維持
（個別指摘単位での agent/round 表示は冗長なので不要、レビュー単位の prefix で十分）。

## CI failure の分類（誤中断防止）

「CI 失敗 → 即 `final=error`」は乱暴。**コード関連 / コード無関係に分類**:

```bash
FAILED=$(gh pr checks "$PR" --json name,state \
  --jq '.[] | select(.state == "FAILURE") | .name')

CODE_FAIL=0
META_FAIL=0
for name in $FAILED; do
  case "$name" in
    *pint*|*larastan*|*phpstan*|*test*|*lint*|*type*|*build*|*ruff*|*eslint*)
      CODE_FAIL=1 ;;
    check_pr_requirements|*assignees*|*reviewers*|*labels*|*meta*)
      META_FAIL=1 ;;
    *)
      CODE_FAIL=1 ;;  # 不明は code-fail 扱い（保守的）
  esac
done

if [ "$CODE_FAIL" -eq 1 ]; then
  jq '.final = "error"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
  echo "❌ コード関連 CI 失敗。中断: $FAILED"; exit 3
elif [ "$META_FAIL" -eq 1 ]; then
  echo "⚠ コード無関係 CI 失敗（Assignees 等）。継続: $FAILED"
  # state.rounds[-1].fix.ci_note に記録するが、ループは続行
fi
```

PR メタデータ系の check（Assignees / Reviewers / Labels）は **継続**、
pint / larastan / test / build などは **中断** を原則とする。

## アンチパターン

- ❌ **修正をメインセッション内で行う** — context が一気に膨れる。必ずサブエージェント
- ❌ **AI に Markdown だけ返させる** — メインがパース・投稿する設計は禁物。AI 直接投稿
- ❌ **nit を都度ユーザに問う** — 必ずバッチ集約して最後に 1 回
- ❌ **`max-rounds` なしで回す** — 無限ループの温床
- ❌ **PR ローテーションを忘れる** — 100+ コメントの巨大 PR になる
- ❌ **CI 失敗を一律で中断** — コード関連／メタチェックを分類（上記参照）
- ❌ **自分の PR に `REQUEST_CHANGES` で投稿** — 必ず 422。事前判定 + COMMENT ダウングレード
- ❌ **`gemini --yolo` だけで起動** — trusted directory で YOLO 無効化。`--skip-trust` 併用
- ❌ **`pgrep -fa <prompt>` で完了判定** — gemini は long prompt が引数に乗り検知失敗。pidfile 必須
- ❌ **fix サブエージェントが Resolve をスキップ** — reply だけでは未対応扱い。Resolve まで実行
- ❌ **review body に identifier prefix を付け忘れる** — GitHub UI 上で誰のレビューか不明になる

## メイン context 節約の工夫

1. **大きいファイルはメイン context に載せない**: payload / err.log / diff は
   すべて `/tmp/` に置き、メインは state.json と result.json だけ読む
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

詳細は PR 上のインラインコメントと state.json に残っているため、本報告では
繰り返さない。

## 関連

- `/ndf:review` — 単発レビュー（AI 直接投稿対応）
- `/ndf:fix` — 修正対応（サブエージェント起動対応）
- `/ndf:codex` — codex CLI 呼び出し手順
- `/ndf:gemini` — gemini CLI 呼び出し手順
- `/ndf:resolve-pr-comments` — Resolve Conversation の詳細
- `general-purpose` エージェント — fix 実行用サブエージェント
