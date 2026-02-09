---
name: pr
description: "commit, push, PR作成を一括実行するワークフローコマンド"
argument-hint: "[base-branch]"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# PR作成

このプロジェクトのコードをcommit, pushし、GitHubでPull Requestを作成する。

**制約**: デフォルトブランチ(main, masterなど)で直接コミット禁止

## 手順

0. **PR確認**
   - `git branch --show-current`で現在ブランチ確認
   - github mcpまたはghで現在のbranchから作成されているPRを確認
   - 既にPRが存在しOPEN状態なら`git add` → `git commit` → `git push`して終了（日本語メッセージ）
     - 上位階層含むすべての変更をcommit
   - PRがない、またはmerge/close済みなら次へ

1. **ブランチ確認・切り替え**
   - デフォルトブランチの場合: 新featureブランチ作成→切り替え
   - デフォルトブランチ以外: git stash → git pull origin [デフォルトブランチ]（コンフリクト時は停止しユーザに報告） → stash復帰

2. **変更コミット**
   - `git status`→`git add`→`git commit`（日本語メッセージ）
   - 上位階層含むすべての変更をcommit

3. **プッシュ**
   - `git push -u origin <branch-name>`

4. **PR作成**
   - **ベースブランチ**: $ARGUMENTS が渡された場合はそのブランチ、なければデフォルトブランチ
   - タイトル・説明: 日本語、body: Summary+Test plan
   - 機密情報（トークン、パスワード、APIキー等）を含めないこと
   - body末尾に `<!-- I want to review in Japanese. -->` を入れる
   - **bodyは必ずHEREDOC形式で渡すこと**（`\n`リテラル混入防止）:
     ```bash
     gh pr create --title "タイトル" --body "$(cat <<'EOF'
     ## Summary
     - 変更内容

     ## Test plan
     - [ ] テスト項目

     <!-- I want to review in Japanese. -->
     EOF
     )"
     ```

## 命名規則

- ブランチ: 英語（github flow）
- コミット・PR: 日本語

## 作業完了報告（必須）

PR作成完了後、以下を報告:
- 基本情報（PRタイトル、ベース/ソースブランチ）
- 変更サマリー（コミット数、変更ファイル数、変更行数、主な変更内容）
- コミット履歴
- PR本文の概要（Summary、Test plan）
- PR URL
