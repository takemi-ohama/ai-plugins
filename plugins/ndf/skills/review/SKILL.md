---
name: review
description: "PRを専門家としてレビューし、Approve/Request Changesを判定する。第二引数で外部AI（codex / gemini）への委譲も可能"
argument-hint: "[PR番号] [AIエージェント(codex|gemini)]"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# PRレビューコマンド

直前PR、または引数で指定されたPRを専門家としてレビュー。

## 引数

- 第一引数 `[PR番号]`: レビュー対象のPR番号（省略時は直前のPR）
- 第二引数 `[AIエージェント]`: レビュー実行者（任意）
  - 省略時: Claude（自身）でレビュー
  - `codex`: Codex CLI に委譲
  - `gemini`: Gemini CLI に委譲

## 実行

- 問題点・改善点あり → 「Request Changes」
- 指摘なし → 「Approve」
- **レビュー結果は必ず GitHub PR 上に投稿する**（後述「レビュー結果の投稿」参照）
  - 指摘は可能な限り **コード行に紐付くインラインコメント** として書く
  - ファイル横断・設計レベルの所見のみ review body（総評）に書く

## 観点

言語慣用性（Idiomatic）・可読性・コード品質・保守性・セキュリティ・テストカバレッジ
- 上から順に優先して指摘

### 具体的なチェックポイント

- **その言語らしい記述方式**: イディオム・標準ライブラリ・言語機能の活用
- **メモリ効率・演算性能を意識したコード**
  - キャッシュ利用
  - Python: numpy 利用、内包表記、ジェネレータ
  - PHP: switch 文の map（連想配列）化
  - 不要なループ・コピーの排除
- **関数・メソッド・ファイル行数の適正化**
  - 目安: 関数/メソッド 50 行、ファイル 300 行
  - ただしプロジェクトの慣例に従う
- **重複・冗長コードの排除**
  - PR 範囲にこだわらず積極的にまとめるよう指摘
- **柔軟性を損なう定数化の排除**
  - 数字をそのまま定数にするような硬直化を避ける
  - 定数よりも DB の master テーブル、または json/yaml による外部化を検討

## レビュー結果の投稿

レビュー結果は **GitHub の PR レビュー機能** を使って必ず PR 上に書き込む。
個別指摘は **コード行に紐付くインラインコメント** が原則。総評（review body）にだけ書くのは避ける。

### 指摘の振り分け

| 指摘の種類 | 投稿先 |
|---|---|
| 特定ファイル・特定行への指摘 | **インラインコメント** (`comments[].path` + `line`) |
| 複数ファイルにまたがる設計指摘 | 代表箇所にインラインコメント + review body に補足 |
| 設計レベル・PR全体の所見 | review body（総評） |
| ファイル単位の指摘（行を絞れない） | そのファイルの代表行にインラインコメント |

### 投稿フロー（推奨: 1 リクエストで一括投稿）

`gh api` の Reviews API を使い、**総評 + 複数のインラインコメント + 判定（event）を 1 回で送信** する。

```bash
PR=<PR番号>
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)

# 1. インラインコメントを JSON 配列で組み立て
#    （path / line / side / body の 4 つが必須。複数行レンジは start_line を併用）
cat > /tmp/review-payload.json <<JSON
{
  "commit_id": "$SHA",
  "event": "REQUEST_CHANGES",
  "body": "## 総評\n\n... 全体所見をここに ...",
  "comments": [
    {
      "path": "src/foo.py",
      "line": 42,
      "side": "RIGHT",
      "body": "[major / 可読性] この関数は 70 行ある。〇〇 と △△ に分割を推奨。"
    },
    {
      "path": "src/bar.py",
      "start_line": 10,
      "line": 25,
      "side": "RIGHT",
      "body": "[minor / 性能] このループは内包表記化できる。"
    }
  ]
}
JSON

# 2. Reviews API に POST
gh api -X POST "repos/$OWNER_REPO/pulls/$PR/reviews" --input /tmp/review-payload.json
```

**`event` の値**:
- `APPROVE` — 指摘なし
- `REQUEST_CHANGES` — 修正必須の指摘あり
- `COMMENT` — 任意の指摘のみ（マージブロックしない）

### インラインコメント本文の書式

各 `comments[].body` の先頭に **`[重要度 / カテゴリ]`** を付けて視認性を上げる:

```
[critical / セキュリティ] SQL がエスケープなしで連結されている。プレースホルダ必須。
[major / 可読性] 70 行関数。〇〇 と △△ に分割を推奨。
[minor / 言語慣用性] Python なら内包表記で 1 行化可能。
[nit / スタイル] スペースが揃っていない。
```

重要度の目安:
- `critical` — セキュリティ・データ破損・本番障害につながる
- `major` — 保守性 / 性能 / 仕様逸脱の重要問題
- `minor` — 改善推奨だがブロッカーではない
- `nit` — 好み・スタイル

### 既存コメントがある場合の重複防止

同じ箇所への二重指摘を避けるため、投稿前に既存コメントを確認する:

```bash
# 既存のレビューコメント一覧
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --paginate \
  | jq -r '.[] | "\(.path):\(.line) \(.body | split("\n")[0])"'
```

すでに同種の指摘があれば、その指摘は省くか、reply（既存コメントへの返信）にする。

### 補助コマンド

```bash
# review body 単体（インラインなし）で投稿したい場合
gh pr review "$PR" --request-changes --body "..."
gh pr review "$PR" --approve --body "..."

# 会話タブへの普通のコメント（行に紐付かない）
gh pr comment "$PR" --body "..."

# 1 件だけインラインコメントを追加（既存 review に含めない）
gh api -X POST "repos/$OWNER_REPO/pulls/$PR/comments" \
  -F commit_id="$SHA" \
  -F path="src/foo.py" \
  -F line=42 -F side=RIGHT \
  -F body="..."
```

## 外部AIへの委譲手順

第二引数が指定された場合、上記「観点」「具体的なチェックポイント」「レビュー結果の投稿」の内容を **レビュー指示プロンプト** として組み立て、指定された CLI に渡す。

### 共通: プロンプト組み立て

1. `gh pr view <PR番号> --json title,body,baseRefName,headRefName,url,headRefOid` で PR メタ情報を取得
2. `gh pr diff <PR番号>` で差分を取得（または変更ファイル一覧 + 必要箇所を `gh pr view <PR番号> --json files` 経由で抽出）
3. 上記「観点」「具体的なチェックポイント」「レビュー結果の投稿」セクションをそのままプロンプトに転記
4. PR タイトル・URL・差分を **対象情報** として明記
5. **出力は GitHub Reviews API のペイロード形式（JSON）で出させる**（後述「外部AIに必須化する出力形式」参照）

### 外部AIに必須化する出力形式

外部AIが Markdown だけを返すと、メインエージェントが行番号を抽出する工数が発生し、誤投稿の元になる。
**プロンプト末尾に以下の指示を必ず含めて、Reviews API ペイロード（JSON）をファイルへ書き出させる**。

```markdown
## 出力形式（必須）

レビュー結果は以下の JSON 構造で
`/tmp/<agent>-review-pr<番号>-payload.json` に書き出してください
（codex なら `apply_patch`、gemini なら `write_file` を使用）。

\`\`\`json
{
  "commit_id": "<headRefOid>",
  "event": "REQUEST_CHANGES" | "APPROVE" | "COMMENT",
  "body": "## 総評\n\n...(設計レベル・PR全体所見のみ)...",
  "comments": [
    {
      "path": "src/foo.py",
      "line": 42,
      "side": "RIGHT",
      "body": "[major / 可読性] ..."
    }
  ]
}
\`\`\`

ルール:
- 個別指摘は必ず `comments[]` のインラインコメントにすること（行を絞れない場合はファイル代表行）
- `body` (総評) には設計・横断的な所見のみ書く。個別指摘の繰り返しは禁止
- 各 `comments[].body` の先頭に `[重要度 / カテゴリ]` を付ける（critical/major/minor/nit）
- `path` は **PR差分に登場するファイルのみ**。存在しないパスを書かないこと
- `line` は **差分に含まれる行**（追加行・コンテキスト行）に限る。`side=RIGHT` がデフォルト
- stdout にも JSON と同じ内容を念のため出力すること
```

### `codex` 指定時

呼び出し手順の詳細は `/ndf:codex` skill（`plugins/ndf/skills/codex/SKILL.md`）に従う。要点:

- プロンプトを `/tmp/codex-review-pr<番号>-prompt.md` に書き出し
- 出力先ファイルを `/tmp/codex-output-review-pr<番号>.md` として **プロンプト内で `apply_patch` 書き出しを必須化**
- `codex exec --dangerously-bypass-approvals-and-sandbox --config reasoning.effort=medium -C "$PWD" < prompt > stdout 2> err &` でバックグラウンド起動
- `grep -q '^tokens used$' err` で完了検知
- 「ファイル → stdout → stderr」三段フォールバックで成果物を回収

### `gemini` 指定時

呼び出し手順の詳細は `/ndf:gemini` skill（`plugins/ndf/skills/gemini/SKILL.md`）に従う。要点:

- プロンプトを `/tmp/gemini-review-pr<番号>-prompt.md` に書き出し
- レビュー用途のため **`--approval-mode plan`**（読み取り専用）+ `--output-format text` で起動
- `gemini --approval-mode plan --output-format text -p "$(cat prompt.md)" > stdout 2> err &` でバックグラウンド起動
- `kill -0 $PID` ポーリングで完了検知（Codex と異なり sentinel 不要 / プロセス exit を見る）
- 成果物は stdout 優先で `/tmp/gemini-review-pr<番号>-output.md` から回収

### 委譲結果の投稿

外部AIが書き出した JSON ペイロードを **メインエージェントが** `gh api` で投稿する。
外部AI に直接 `gh` を叩かせない（コミットSHA・パス検証・既存コメント重複チェックを集約するため）:

```bash
PAYLOAD=/tmp/codex-review-pr$PR-payload.json   # or gemini-...
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# 1. commit_id が空 or 古い場合は最新 SHA で上書き
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)
jq --arg sha "$SHA" '.commit_id = $sha' "$PAYLOAD" > /tmp/review-payload.json

# 2. パスが PR 差分に存在するか軽くチェック（任意）
gh pr diff "$PR" --name-only > /tmp/pr-files.txt
jq -r '.comments[].path' /tmp/review-payload.json | while read -r p; do
  grep -qxF "$p" /tmp/pr-files.txt || echo "WARN: $p は PR 差分に含まれない" >&2
done

# 3. Reviews API に POST
gh api -X POST "repos/$OWNER_REPO/pulls/$PR/reviews" --input /tmp/review-payload.json
```

**Claude 自身による追加判定は行わず**、外部AIの判定（`event`）と指摘内容をそのまま採用する。
投稿後、外部AIの `body`（総評）と件数サマリをユーザーへ報告する。

## 作業完了報告（必須）

レビュー結果は **PR 上に投稿済み** であることが前提。ユーザーへの報告は以下に絞る:

- 利用エージェント（claude / codex / gemini のいずれか）
- 投稿結果（review URL、event = APPROVE / REQUEST_CHANGES / COMMENT）
- 件数サマリ（インラインコメント数、重要度別内訳）
- 総評（review body）の要約
- PR URL

詳細な指摘内容は PR 上のインラインコメントに残っているため、ユーザー宛報告では繰り返さない。
