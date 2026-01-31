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

## 作業完了報告（必須）

作業完了時は以下の情報を必ず報告すること：

### 報告テンプレート

```
マージ後クリーンアップが完了しました。

## 実行内容

### PRマージ確認
- **PR URL**: https://github.com/owner/repo/pull/123
- **PRタイトル**: [PRのタイトル]
- **マージコミット**: `abc1234`
- **マージ日時**: YYYY-MM-DD HH:MM:SS

### ブランチ情報
- **削除したブランチ**: `feature-branch-name`
- **ベースブランチ**: `main`

### mainブランチの状態
- **最新コミット**: `def5678` - "コミットメッセージ"
- **現在のブランチ**: `main`
- **未コミットの変更**: なし / あり（stash復元済み）

### 実行結果
- ✅ PRマージ確認完了
- ✅ ブランチ削除完了
- ✅ mainブランチ更新完了
- ✅ 作業ディレクトリクリーン
```

### 報告例

```
マージ後クリーンアップが完了しました。

## 実行内容

### PRマージ確認
- **PR URL**: https://github.com/takemi-ohama/ai-plugins/pull/13
- **PRタイトル**: feat: affaan-mプラグインのフックスクリプトをClaude Code仕様に実装
- **マージコミット**: `82b46ab`
- **マージ日時**: 2026-01-31 10:30:45

### ブランチ情報
- **削除したブランチ**: `implement-affaan-m-hooks-scripts`
- **ベースブランチ**: `main`

### mainブランチの状態
- **最新コミット**: `82b46ab` - "Merge pull request #13 from takemi-ohama/implement-affaan-m-hooks-scripts"
- **現在のブランチ**: `main`
- **未コミットの変更**: なし

### 実行結果
- ✅ PRマージ確認完了
- ✅ ブランチ削除完了
- ✅ mainブランチ更新完了
- ✅ 作業ディレクトリクリーン
```

