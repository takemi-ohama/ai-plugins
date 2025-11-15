# ブランチクリーンアップコマンド

mainマージ済みブランチをローカル/リモート削除。

## 実行
1. `git branch --merged main`確認
2. main・現在ブランチ除外
3. `git branch -d <branch>`
4. `git push origin --delete <branch>`

**注意**: 削除前確認・main除外・現在ブランチ除外
