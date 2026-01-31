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
   - **ベースブランチ**:
     - オプション引数が渡された場合: そのブランチ名をPRの向き先（base branch）に指定
     - オプション引数がない場合: デフォルトブランチ（main/master）をPRの向き先に指定
   - タイトル・説明: 日本語、body: Summary+Test plan
   - **⚠️セキュリティ注意**: 機密情報（トークン、パスワード、API キー等）を含めないこと
   - body末尾に <!-- I want to review in Japanese. --> を入れる

## 命名規則
- ブランチ: 英語（例: update-config）
- github flow
- コミット・PR: 日本語

## 作業完了報告（必須）

作業完了時は以下の情報を必ず報告すること：

### 報告テンプレート

```
PR作成が完了しました。

## 基本情報

| 項目 | 値 |
|------|-----|
| PRタイトル | [PRのタイトル] |
| ベースブランチ | `main` / `develop` / その他 |
| ソースブランチ | `feature-branch-name` |
| 作成日時 | YYYY-MM-DD HH:MM:SS |

## 変更サマリー

| 項目 | 値 |
|------|-----|
| コミット数 | N個 |
| 変更ファイル数 | M個 |
| 変更行数 | +追加行, -削除行 |

**主な変更内容**:
- [変更内容1]
- [変更内容2]
- [変更内容3]

## コミット履歴

| コミットハッシュ | メッセージ |
|------------------|------------|
| `abc1234` | コミットメッセージ1 |
| `def5678` | コミットメッセージ2 |

## PR本文の概要

**Summary**:
[変更の概要を2-3行で]

**Test plan**:
- [ ] テスト項目1
- [ ] テスト項目2

## 次のアクション

| 項目 | 状態 |
|------|------|
| レビュー依頼 | GitHub Copilot / 特定のレビュアー |
| CI/CDチェック | 実行中 / 完了 / 失敗 |

---

## 📎 リンク

**PR URL**: https://github.com/owner/repo/pull/123
```

### 報告例

```
PR作成が完了しました。

## 基本情報

| 項目 | 値 |
|------|-----|
| PRタイトル | feat: affaan-mプラグインのフックスクリプトをClaude Code仕様に実装 |
| ベースブランチ | `main` |
| ソースブランチ | `implement-affaan-m-hooks-scripts` |
| 作成日時 | 2026-01-31 07:00:00 |

## 変更サマリー

| 項目 | 値 |
|------|-----|
| コミット数 | 3個 |
| 変更ファイル数 | 7個 |
| 変更行数 | +275, -497 |

**主な変更内容**:
- 7つのフックスクリプトをClaude Code Hooks仕様に完全準拠
- secret-scan、typescript-check、detect-package-managerに実機能実装
- 4つのフックは情報メッセージ表示（API制限のため）
- コード削減: 497行 → 275行（45%削減）

## コミット履歴

| コミットハッシュ | メッセージ |
|------------------|------------|
| `6ff32b6` | feat: affaan-mプラグインのフックスクリプトをClaude Code仕様に実装 |
| `8d013a2` | fix: affaan-mプラグインのhooks.json構造をClaude Code仕様に修正 |

## PR本文の概要

**Summary**:
affaan-mプラグインの7つのフックスクリプトをClaude Code Hooks仕様に完全準拠するよう実装・修正しました。secret-scan、typescript-check、detect-package-managerは実機能を持ち、その他は情報メッセージを表示します。

**Test plan**:
- [ ] affaan-mプラグインを再インストールできること
- [ ] 各フックスクリプトが個別実行できること
- [ ] secret-scanがシークレットを検出できること

## 次のアクション

| 項目 | 状態 |
|------|------|
| レビュー依頼 | ✅ GitHub Copilot |
| CI/CDチェック | ⏳ 実行中 |

---

## 📎 リンク

**PR URL**: https://github.com/takemi-ohama/ai-plugins/pull/13
```

