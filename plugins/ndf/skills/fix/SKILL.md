---
name: fix
description: "PRのレビューコメントを確認し、修正対応を実行する"
argument-hint: "[PR番号]"
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

## 手順

1. review comment確認
2. **CIエラー確認**（`gh pr checks <PR>` で失敗ジョブを検出）
   - 実行中(PENDING/IN_PROGRESS)のチェックが残っている場合は次ステップに進まず完了を待つ
3. 修正可否判断（review指摘 + CIエラー両方）
4. 問題点修正
5. **コミット前のCI状態再確認**（修正作業中にCIが完了して新しい失敗が出ているかも）
   - 実行中があればさらに完了を待つ
   - 新しい失敗が出ていれば手順3に戻る
6. コミット・プッシュ
7. **CI再実行結果の確認**（push後、CIが通るまで待機 or 失敗したら追加修正）
8. PRにSummaryコメントを追加
9. 対応したコードコメントに個別に返信
10. reviewerに再レビューを依頼
11. 対応完了したコードコメントを「Resolve Conversation」にする

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
RUN_ID=$(gh run list --branch <branch-name> --limit 1 --json databaseId --jq '.[0].databaseId')

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

## 作業完了報告（必須）

PRにSummaryコメントを追加:
- 対応した指摘の一覧（優先度、ファイル、指摘内容、対応状況）
- **対応したCIエラーの一覧**（ジョブ名、エラー内容、修正方法）
- 各修正の問題点と修正内容
- **CI再実行結果**（全チェックPASSの確認）
- 修正ファイル一覧
