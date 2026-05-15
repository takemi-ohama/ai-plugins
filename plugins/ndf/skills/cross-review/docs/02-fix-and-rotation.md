# 02: 修正 (Step 5) + PR ローテーション (Step 6)

## Step 5: 修正 — **必ずサブエージェント経由**

**メインセッションでは修正コードを書かない。** `/ndf:fix` を
`general-purpose` サブエージェントで起動する。

**サブエージェントの責務（必須 5 点）**:

1. critical / major / minor の修正コミット
2. 修正テストの追加・実行
3. 修正対象の thread に **reply 投稿** + **`resolveReviewThread` で Resolve**
4. nit / 判断が割れる minor は **修正せず deferred 記録**（reply は `[deferred / nit]` ラベル付き、Resolve しない）
5. 戻り値ファイル `/tmp/fix-pr<PR>-result.json` を必ず書き出す

### サブエージェント起動例

```python
Agent(
    subagent_type="general-purpose",
    description=f"Fix PR #{PR} (round {ROUND})",
    prompt=f"""
/ndf:fix {PR} --defer-nit を実行してください。

**作業ディレクトリ厳守**: cd {WORKTREE_PATH} で作業すること。
別セッションが /work/<repo-root> 側で並行作業している可能性があり、
worktree 外を触ると競合します。

## コンテキスト
- リポジトリ: {OWNER_REPO}
- PR: #{PR} (round {ROUND_IN_PR}/{ROTATE_AFTER})
- worktree: {WORKTREE_PATH}
- ブランチ: {HEAD_BRANCH}
- ベース: {BASE_BRANCH}
- headRefOid: {HEAD_OID}
- 前ラウンドのレビュー結果:
  - codex review: {CODEX_REVIEW_URL}
    (intent={CODEX_INTENT}, posted_as={CODEX_POSTED_AS}, {CODEX_COMMENT_COUNT}件)
  - gemini review: {GEMINI_REVIEW_URL}
    (intent={GEMINI_INTENT}, posted_as={GEMINI_POSTED_AS}, {GEMINI_COMMENT_COUNT}件)
- 既存コメントスナップショット: /tmp/cross-review-pr{PR}-existing-comments.txt

## ポリシー
- critical / major / minor は自動修正
- nit は deferred として記録のみ（修正しない、Resolve しない）
- bot 指摘が誤読していたら修正せず reply で説明（rejected として記録、Resolve しない）
- **重複指摘（codex/gemini が同じ箇所を別 thread で指摘）は全 thread に reply + Resolve**

## 必須実行手順（順序厳守）

1. PR コメント取得: `gh api "repos/{OWNER_REPO}/pulls/{PR}/comments" --paginate`
2. 重要度で分類（[critical/major/minor/nit] プレフィックス）
3. CI 状態確認: `gh pr checks {PR}` （PENDING があれば完了まで待つ）
4. critical/major/minor の修正コミット（worktree 内のみ）
5. `./pint-changed.sh && ./larastan-changed.sh` 等の品質チェック
6. push: `git push origin {HEAD_BRANCH}` （--force / --no-verify 禁止）
7. CI 再実行待ち: `gh pr checks {PR} --watch` （最大 10 分）
8. **各 thread に reply 投稿**:
   - 修正済み: 「対応しました — <ファイル>:<行> で〇〇 (commit <SHA>)」
   - deferred: 「[deferred / nit] 後続 PR で対応予定」
   - rejected: 「bot 指摘は誤読です — 理由: ...」
9. **修正済み thread を `resolveReviewThread` で Resolve**:
   ```bash
   # thread_id は GraphQL で取得
   gh api graphql -f query='
     query {{ repository(owner:"...", name:"...") {{
       pullRequest(number: {PR}) {{ reviewThreads(first:100) {{
         nodes {{ id isResolved path line }}
       }} }}
     }} }}'
   # 修正済みのみ resolve
   gh api graphql -f query='
     mutation($id: ID!) {{
       resolveReviewThread(input: {{threadId: $id}}) {{ thread {{ isResolved }} }}
     }}' -f id="$THREAD_ID"
   ```
   - deferred / rejected の thread は **Resolve しない**
10. 戻り値ファイル書き出し（下記フォーマット）

## 戻り値ファイル /tmp/fix-pr{PR}-result.json

```json
{{
  "pr": {PR},
  "fix_commit": "abc1234",
  "ci_status": "SUCCESS" | "FAILURE" | "PENDING",
  "ci_failed_checks": [],
  "fixed_count": 6,
  "by_severity": {{"critical": 0, "major": 4, "minor": 2, "nit": 0}},
  "resolved_threads": [
    {{"thread_id": "PRRT_...", "comment_id": 123, "path": "...", "line": 42}}
  ],
  "deferred": [
    {{"thread_id": "...", "path": "...", "line": 31, "severity": "nit",
      "summary": "...", "comment_url": "..."}}
  ],
  "rejected": [
    {{"thread_id": "...", "summary": "...", "reason_for_rejection": "..."}}
  ]
}}
```
""",
)
```

サブエージェント完了後、メインは `/tmp/fix-pr$PR-result.json` を読んで
state を更新:

```bash
FIX=/tmp/fix-pr$PR-result.json
[ ! -s "$FIX" ] && { echo "❌ fix サブエージェントが戻り値ファイルを生成しなかった" >&2; exit 3; }

jq --slurpfile f "$FIX" \
   '.rounds[-1].fix = {
      commit:           $f[0].fix_commit,
      fixed:            $f[0].fixed_count,
      deferred:         ($f[0].deferred | length),
      rejected:         ($f[0].rejected | length),
      resolved_threads: ($f[0].resolved_threads | length),
      ci:               $f[0].ci_status,
      ci_failed_checks: ($f[0].ci_failed_checks // []),
      ci_note:          ($f[0].ci_note // null)
    }
    | .rounds[-1].ended_at = "'$(date -Iseconds)'"
    | .deferred_nits += [
        $f[0].deferred[] | . + {pr: '$PR', round: '$ROUND'}
      ]' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
```

### CI failure の分類（誤中断防止）

`ci_status = FAILURE` のとき、**code-related か meta-only かを判定** してから中断する:

```bash
CI=$(jq -r ".rounds[-1].fix.ci" "$STATE")
if [ "$CI" = "FAILURE" ]; then
  FAILED=$(jq -r '.rounds[-1].fix.ci_failed_checks[]' "$STATE")
  CODE_FAIL=0; META_FAIL=0
  for name in $FAILED; do
    case "$name" in
      *pint*|*larastan*|*phpstan*|*test*|*lint*|*type*|*build*|*ruff*|*eslint*|*tsc*|*mypy*)
        CODE_FAIL=1 ;;
      check_pr_requirements|*assignees*|*reviewers*|*labels*|*meta*)
        META_FAIL=1 ;;
      *)
        CODE_FAIL=1 ;;  # 不明は code-fail（保守的）
    esac
  done

  if [ "$CODE_FAIL" -eq 1 ]; then
    jq '.final = "error"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
    echo "❌ コード関連 CI 失敗。中断: $FAILED"
    exit 3
  else
    # meta-only: ci_note に記録して継続
    jq --arg failed "$FAILED" \
      '.rounds[-1].fix.ci_note = "メタチェックのみ失敗: " + $failed + " — コードと無関係のため継続"' \
      "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
    echo "⚠ メタチェックのみ失敗 ($FAILED) — 継続"
  fi
fi
```

**例**: `check_pr_requirements`（Assignees 未設定）はループ継続、
`laravel/pint` や `phpstan` の失敗は即中断してユーザ判断。

## Step 6: PR ローテーション判定

```bash
ROUND_IN_PR=$(jq --argjson p $PR '[.rounds[] | select(.pr == $p)] | length' "$STATE")

if [ "$ROUND_IN_PR" -ge "$ROTATE_AFTER" ] && [ "$TOTAL_ROUNDS" -lt "$MAX_ROUNDS" ]; then
  echo "🔄 PR #$PR が $ROUND_IN_PR round 経過。ローテーション実施。"
  rotate_pr
fi
```

### `rotate_pr` の実装

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
  gh pr comment "$old_pr" --body "🔄 cross-review ループ進行中のため、本 PR を close し新規 PR に巻き直します。 round_in_pr=$ROUND_IN_PR で長尺化を回避。"
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

## Step 7: 次ラウンドへ

Step 1 に戻る。

## Step 8: 終了処理 — deferred nit のバッチ問い合わせ

ループ終了時（`final` 確定後）、`deferred_nits` が残っていれば
**1 回だけ** ユーザに問い合わせる:

```bash
DEFERRED_COUNT=$(jq '.deferred_nits | length' "$STATE")
if [ "$DEFERRED_COUNT" -gt 0 ]; then
  echo "=== 残った nit 指摘 ($DEFERRED_COUNT 件) ==="
  jq -r '.deferred_nits[] | "- [\(.severity)] \(.path):\(.line) — \(.summary)"' "$STATE"
  echo ""
  echo "これらの nit を一括対応する場合は再度 /ndf:fix <PR#> を起動してください。"
fi
```

UI 上は **AskUserQuestion で 1 回だけ** 「nit 一括対応する / しない /
個別選択」を選ばせるのが望ましい。
