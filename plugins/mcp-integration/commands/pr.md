# PR作成
このプロジェクトのコードを下記の手順に従ってcommit, pushし、githubでPull Requestを作成してください。

**⚠️重要**: デフォルトブランチ(main, masterなど)で直接コミット禁止

## 手順
0. **PR確認**
   - `git branch --show-current`で現在ブランチ確認
   - github mcpまたはghで現在のbranchから作成されているPRを確認
   - 既にPRが存在し、OPEN状態なら`git add` → `git commit` → `git push`して終了（日本語メッセージ）
      - 上位階層含むすべての変更をcommit
   - PRがない、またはmerge, close済みなら次へ

1. **ブランチ確認・切り替え**
   - デフォルトブランチの場合: 新featureブランチ作成→切り替え
   - デフォルトブランチ以外: git stash(全未コミット) → git pull origin [デフォルトブランチ]（コンフリクト時は停止しユーザに報告） → stash復帰

2. **変更コミット**
   - `git status`→`git add`→`git commit`（日本語メッセージ）
   - 上位階層含むすべての変更をcommit

3. **プッシュ**
   - `git push -u origin <branch-name>`

4. **PR作成**
- タイトル・説明: 日本語、body: Summary+Test plan
   - body末尾に <!-- I want to review in Japanese. --> を入れる

## 命名規則
- ブランチ: 英語（例: update-config）
- github flow
- コミット・PR: 日本語
