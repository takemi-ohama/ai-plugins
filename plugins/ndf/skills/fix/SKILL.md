---
name: fix
description: "PRのレビューコメントを確認し、修正対応を実行する。サブエージェント (general-purpose) 起動にも対応"
argument-hint: "[PR番号] [--defer-nit] [--severity-min critical|major|minor]"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

# PR修正コマンド

直前PR、または引数で指定されたPRのreview comment確認・修正対応実行。

## 起動モード

このスキルは **メインセッション直接実行** と **サブエージェント (`general-purpose`) 起動** の両方に対応する。
長丁場のクロスレビューループ（`/ndf:cross-review`）からは **必ずサブエージェント経由で起動** されることを想定:

```python
# メインからの起動例（cross-review が内部でこれを行う）
Agent(
    subagent_type="general-purpose",
    description="Fix PR review comments (sub-agent)",
    prompt="""
/ndf:fix <PR番号> --defer-nit を実行してください。

PR: <PR番号>
リポジトリ: <owner/repo>
重要度ポリシー: critical/major/minor は修正、nit は deferred として残す
完了後の戻り値: 件数サマリ + 修正コミット SHA + 残 nit リスト
"""
)
```

サブエージェント側ではこの SKILL.md を読み込んで、自己完結で
**修正 → コミット → push → reply → Resolve Conversation** まで実行する。
メインへの戻り値は最小限のサマリのみ。

## 引数

| 引数 | 意味 | 既定 |
|---|---|---|
| `[PR番号]` | 対象 PR | 直前 PR |
| `--defer-nit` | nit 指摘は修正せず deferred としてリスト出力 | OFF |
| `--severity-min LEVEL` | 指定重要度未満は無視（`critical` / `major` / `minor`） | `minor` (= minor 以上を修正) |

## 重要度ベースの自動修正ポリシー

`[重要度 / カテゴリ]` プレフィックス（`/ndf:review` 出力規約）で分類:

| 重要度 | 動作 | ユーザ問い合わせ |
|---|---|---|
| `critical` | **必ず自動修正** | なし |
| `major` | **必ず自動修正** | なし |
| `minor` | 自動修正（明らかな改善のみ）。判断が割れるなら `nit` として deferred 扱い | なし |
| `nit` | `--defer-nit` 指定時は **修正せず deferred リスト** に追加。最後にまとめてユーザ問い合わせ | あり（最後に1回） |

**指摘の正否判断**:
- ロジック・仕様逸脱・セキュリティ: コード/仕様を確認してから修正可否判断
- bot 指摘で **明らかに誤読** している場合（例: 意図的な変数展開を「クオート不足」と指摘する等）: 修正しない、reply で理由説明
- 仕様判断が必要な指摘（API 変更、互換性破壊など）: ユーザ問い合わせ対象（critical でもエスカレーション）

**自動判断できない場合の取り扱い** （context 節約のため安易に user に投げない）:
- 仕様文書（docs/, README）を読んで判断する
- 既存テストを読んで挙動を確認する
- 関連する他コードの慣例を確認する
- それでも不明なら deferred リストに「要ユーザ判断」として記録、最後にまとめて問い合わせ

## 手順

1. review comment取得 + 重要度別に振り分け（`[critical/major/minor/nit]` プレフィックス）
2. **CIエラー確認**（`gh pr checks <PR>` で失敗ジョブを検出）
   - 実行中(PENDING/IN_PROGRESS)のチェックが残っている場合は次ステップに進まず完了を待つ
3. 修正対象を確定:
   - `critical` / `major` → 全件修正対象
   - `minor` → 修正対象（明らかでないものは `deferred[]` へ）
   - `nit` (`--defer-nit` 時) → `deferred[]` のみ、修正しない
   - CIエラー → 全件修正対象
4. 問題点修正
5. **コミット前の再確認**（修正作業中に状況が変わっている可能性への対応）
   - **review comment再取得**: 作業中に新しいコメントが追加されていないか確認
   - **CI状態再確認**: 実行中があれば完了を待つ。新しい失敗が出ていないか確認
   - 新しい指摘/失敗があれば手順3に戻る
6. コミット・プッシュ
7. **CI再実行結果の確認**（push後、CIが通るまで待機 or 失敗したら追加修正）
8. PRにSummaryコメントを追加（対応した件数 + deferred 件数を明記）
9. 対応したコードコメントに個別に返信
10. **deferred スレッドには `[deferred / nit]` のラベル付き返信** を投稿（resolve はしない）
11. reviewerに再レビューを依頼
12. 対応完了したコードコメントを「Resolve Conversation」にする
13. **戻り値ファイルを書き出す**: `/tmp/fix-pr<番号>-result.json` （後述「戻り値フォーマット」参照）

- 4〜6はgit、1〜2/5と8以降はgithub mcpまたはghを利用

## CIエラーチェック

### 失敗ジョブの検出

```bash
# PRの全チェック状態を確認（FAIL/PASS/PENDING）
gh pr checks <PR番号>

# JSON形式で詳細取得
gh pr checks <PR番号> --json name,state,link,completedAt

# 失敗ジョブのみ抽出
gh pr checks <PR番号> --json name,state | \
  python3 -c "import json,sys; [print(c['name']) for c in json.load(sys.stdin) if c['state']=='FAILURE']"

# 実行中ジョブのみ抽出（完了待ちに使用）
gh pr checks <PR番号> --json name,state | \
  python3 -c "import json,sys; [print(c['name']) for c in json.load(sys.stdin) if c['state'] in ('PENDING','IN_PROGRESS','QUEUED')]"
```

### CI完了を待つ

`gh pr checks --watch` で全チェックの完了までブロック待機できる:

```bash
# 完了まで待機（全部PASSでexit 0、失敗があればexit 1）
gh pr checks <PR番号> --watch

# タイムアウト付きで待つ（例: 最大10分）
timeout 600 gh pr checks <PR番号> --watch || echo "timed out or failed"
```

修正作業の途中や、コミット直前の再確認で活用する。

### 失敗ログの取得

```bash
# ワークフロー実行ID取得
RUN_ID=$(gh run list --branch <branch-name> --limit 1 --json databaseId --jq '.[0].databaseId // empty')
[ -z "$RUN_ID" ] && { echo "No CI run found for this branch"; exit 0; }

# 失敗ステップのログだけ表示（効率的）
gh run view $RUN_ID --log-failed

# 特定ジョブのログ
gh run view $RUN_ID --job <job-id> --log
```

### CIエラーの分類と対応方針

| エラー種別 | 対応方針 |
|---|---|
| **lint/format** | 自動修正ツール実行（`ruff`, `prettier`, `eslint --fix` 等）→ コミット |
| **型チェック** | 型定義・アノテーションを修正。無視コメントは原則禁止（根本対応） |
| **テスト失敗** | 失敗テストを読み、実装/テストどちらが正しいか判断してから修正。テスト側の問題なら仕様確認 |
| **ビルドエラー** | 依存関係・構文・設定ファイルを確認 |
| **依存脆弱性** | 可能ならバージョン更新、無理なら除外ルール追加（理由明記） |
| **タイムアウト/flaky** | retry設定、テスト分割、リトライ追加 |
| **インフラ一時障害** | 再実行で解消することがあるため `gh run rerun $RUN_ID` を先に試す |

### review指摘との統合

review指摘とCIエラーは**同じPRで一緒に修正**する:
- 同じファイル・機能に関する指摘とCIエラーは1コミットにまとめる
- 独立しているなら別コミットに分離（git log で追いやすい）

## ghコマンド例

### コメントへの返信

```bash
# PRのレビューコメント一覧を取得
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments

# 特定のコメントに返信（in_reply_to にコメントIDを指定）
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  -f body="修正しました。" \
  -F in_reply_to={comment_id}
```

### Resolve Conversation

```bash
# GraphQL APIでスレッドをresolveする
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "{thread_node_id}"}) {
      thread { isResolved }
    }
  }
'
```

### thread_node_idの取得方法

```bash
# PRのレビュースレッド一覧を取得（node_id含む）
gh api graphql -f query='
  query {
    repository(owner: "{owner}", name: "{repo}") {
      pullRequest(number: {pr_number}) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { body }
            }
          }
        }
      }
    }
  }
'
```

**方針**:
- 品質・可読性・セキュリティ向上、既存機能影響なし
- 指摘がすべて正しいとは限らない。修正前に仕様を調査し、実施の可否を判断すること
- 未対応の場合はその理由をコメントに書き込む

## 戻り値フォーマット（必須）

サブエージェント呼び出し時の context 節約のため、**実行結果は `/tmp/fix-pr<番号>-result.json` に書き出す**:

```json
{
  "pr": 67,
  "fix_commit": "abc1234",
  "ci_status": "SUCCESS" | "FAILURE" | "PENDING" | "NONE",
  "fixed_count": 5,
  "by_severity": {"critical": 1, "major": 2, "minor": 2, "nit": 0},
  "deferred": [
    {
      "comment_id": 3222849090,
      "thread_id": "PRRT_...",
      "path": "src/foo.py",
      "line": 42,
      "severity": "nit",
      "category": "style",
      "summary": "末尾セミコロンの有無",
      "reason_for_deferral": "好みの範囲。プロジェクト規約と齟齬なし"
    }
  ],
  "rejected": [
    {
      "comment_id": 3222849090,
      "summary": "heredoc を <<'JSON' にせよ",
      "reason_for_rejection": "$SHA を意図的に展開する必要があり、クオート化すると逆に壊れる"
    }
  ],
  "summary_comment_url": "https://github.com/.../pull/67#issuecomment-..."
}
```

サブエージェントとして起動された場合は、この JSON をメインに返すサマリの基礎とする。

## 作業完了報告（必須）

メイン or PR への報告内容（戻り値ファイルから抽出）:
- 対応した指摘の件数（重要度別: critical/major/minor）
- **deferred 件数**（主に nit、最後にユーザ問い合わせ予定）
- **rejected 件数**（bot 指摘が不適切で修正しなかった件、各々理由付き）
- **対応したCIエラーの一覧**（ジョブ名、エラー内容、修正方法）
- **CI再実行結果**（全チェックPASSの確認）
- 修正コミット SHA / 修正ファイル一覧
- 戻り値ファイルパス: `/tmp/fix-pr<番号>-result.json`
