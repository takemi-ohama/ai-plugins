# マージ後クリーンアップコマンド

PRマージ後のクリーンアップを実行。

## 手順
0. **事前確認**: github mcpで引数の(引数が無ければ自身が作成した最新)のPRがmainにmergeされていることを確認→mergeされていなければ終了
1. **事前確認**: `git status`→変更あればstash
2. **main更新**: `git checkout main`→`git pull`
3. **ブランチ削除**:
   - `git branch -d <feature-branch>`
   - stash復元

**注意**: 冪等性保証・エラー時中断・削除済み無視
