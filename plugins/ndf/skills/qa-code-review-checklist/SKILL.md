---
name: qa-code-review-checklist
description: |
  Comprehensive code review checklist covering readability, maintainability, performance, security, and best practices. Use when reviewing code or conducting quality checks.

  This skill provides systematic code review guidance:
  - Language-specific best practices (JavaScript, Python, Java, etc.)
  - Security checklist (OWASP Top 10)
  - Performance optimization points
  - Maintainability and readability checks
  - Automated review integration (Codex CLI MCP)

  Triggers: "code review", "review checklist", "quality check", "check code", "コードレビュー", "品質チェック", "レビュー観点"
---

# QA Code Review Checklist Skill

## 概要

このSkillは、qaエージェントがコードレビューを実施する際に使用する包括的なチェックリストです。可読性、保守性、パフォーマンス、セキュリティ、ベストプラクティスの観点から体系的にコードを評価します。

## 主な機能

1. **一般的なチェックリスト**: すべてのプログラミング言語に適用可能
2. **言語別チェックリスト**: JavaScript、Python、Java等の特有の観点
3. **セキュリティチェックリスト**: OWASP Top 10対応
4. **パフォーマンスチェックリスト**: 最適化ポイント
5. **レビューレポートテンプレート**: 構造化されたレビュー結果

## 使用方法

### チェックリスト一覧

```
checklists/
├── general-checklist.md        # 一般的なチェックリスト
├── javascript-checklist.md     # JavaScript特有
├── python-checklist.md         # Python特有
├── security-checklist.md       # セキュリティ
└── performance-checklist.md    # パフォーマンス
```

### レビューテンプレート

```
templates/
└── review-report-template.md   # レビューレポート
```

## 一般的なチェックリスト

### 可読性

- [ ] **変数名・関数名は明確か**
  - 単文字変数（i, j以外）を避ける
  - 略語を避ける（`usr` → `user`）
  - 意図が明確な名前（`getData` → `getUserProfile`）

- [ ] **コメントは適切か**
  - 複雑なロジックに説明あり
  - WHYを説明（WHATではなく）
  - 古いコメントは削除済み

- [ ] **ネストは深すぎないか**
  - 最大3レベルまで
  - 早期リターンで浅く
  - 関数分割で簡潔に

- [ ] **関数・メソッドは適切なサイズか**
  - 1関数50行以内が目安
  - 単一責任の原則
  - 引数は3個以内が望ましい

- [ ] **マジックナンバーを避けているか**
  - 定数として定義
  - 意味のある名前
  - ```javascript
    // Bad
    if (age > 18) { ... }

    // Good
    const ADULT_AGE = 18;
    if (age > ADULT_AGE) { ... }
    ```

### 保守性

- [ ] **DRY原則に従っているか**
  - 重複コードはない
  - 共通ロジックは関数化
  - 設定は外部ファイルに

- [ ] **関数は単一責任か**
  - 1つのことだけをする
  - 関数名が動詞+名詞
  - テストしやすい

- [ ] **モジュール分割は適切か**
  - 関連する機能をまとめる
  - 依存関係が明確
  - 循環依存がない

- [ ] **エラーハンドリングがあるか**
  - try-catchで例外処理
  - エラーメッセージは具体的
  - ログ出力

- [ ] **テストコードはあるか**
  - ユニットテスト
  - エッジケースのテスト
  - カバレッジ80%以上

### パフォーマンス

- [ ] **不要なループはないか**
  - O(n²)を避ける
  - 早期終了（break）
  - ループ外で可能な処理

- [ ] **データ構造は適切か**
  - 検索頻度高→Map/Set
  - 順序重要→Array
  - Key-Value→Object/Map

- [ ] **キャッシュを活用しているか**
  - 計算結果のキャッシュ
  - API結果のキャッシュ
  - メモ化

- [ ] **非同期処理は適切か**
  - I/O処理はasync/await
  - 並列実行可能なものはPromise.all
  - エラーハンドリング

### セキュリティ

- [ ] **入力値検証があるか**
  - すべての外部入力を検証
  - ホワイトリスト方式
  - 型チェック

- [ ] **SQLインジェクション対策**
  - パラメータ化クエリ
  - ORMの使用
  - エスケープ処理

- [ ] **XSS対策**
  - HTMLエスケープ
  - Content-Security-Policy
  - DOMPurifyなどのライブラリ

- [ ] **認証・認可は適切か**
  - JWT/セッション管理
  - ロールベースアクセス制御
  - パスワードはハッシュ化

- [ ] **機密情報の扱い**
  - 環境変数で管理
  - ログに出力しない
  - 暗号化

## 言語別チェックリスト

### JavaScript/TypeScript

- [ ] **const/let を使用（var禁止）**
- [ ] **厳密等価演算子（===）を使用**
- [ ] **async/await を使用（コールバック地獄回避）**
- [ ] **アロー関数を適切に使用**
- [ ] **分割代入を活用**
- [ ] **テンプレートリテラルを使用**
- [ ] **Optional Chaining (?.) を活用**
- [ ] **Nullish Coalescing (??) を活用**

**例**:
```javascript
// Good
const user = await fetchUser(id);
const name = user?.profile?.name ?? 'Unknown';

// Bad
var user = fetchUser(id).then(function(user) {
  var name = user && user.profile && user.profile.name || 'Unknown';
});
```

### Python

- [ ] **PEP 8 に従う**
- [ ] **型ヒントを使用（Python 3.5+）**
- [ ] **リスト内包表記を活用**
- [ ] **コンテキストマネージャ（with文）を使用**
- [ ] **f-stringを使用（Python 3.6+）**
- [ ] **pathlib を使用（os.path より推奨）**
- [ ] **dataclass を活用（Python 3.7+）**

**例**:
```python
# Good
from pathlib import Path
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

users = [User(name="Alice", age=30)]
names = [u.name for u in users if u.age >= 18]

# Bad
import os
class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

users = [User("Alice", 30)]
names = []
for u in users:
    if u.age >= 18:
        names.append(u.name)
```

## セキュリティチェックリスト

### OWASP Top 10

1. **インジェクション**
   - [ ] パラメータ化クエリ使用
   - [ ] 入力値検証とエスケープ

2. **認証の不備**
   - [ ] パスワードの安全なハッシュ化（bcrypt等）
   - [ ] 多要素認証の実装検討
   - [ ] セッション管理の適切性

3. **機密データの露出**
   - [ ] HTTPS通信
   - [ ] 機密データの暗号化
   - [ ] ログに機密情報を出力しない

4. **XXE（XML External Entity）**
   - [ ] XML パーサーの安全な設定
   - [ ] DTD処理の無効化

5. **アクセス制御の不備**
   - [ ] 認可チェックの実装
   - [ ] ロールベースアクセス制御（RBAC）

6. **セキュリティ設定ミス**
   - [ ] デフォルトパスワードの変更
   - [ ] 不要なサービスの無効化
   - [ ] セキュリティヘッダーの設定

7. **XSS（クロスサイトスクリプティング）**
   - [ ] HTMLエスケープ
   - [ ] Content-Security-Policy設定
   - [ ] DOMベースXSS対策

8. **安全でないデシリアライゼーション**
   - [ ] 信頼できないデータのデシリアライズ禁止
   - [ ] 署名・検証の実装

9. **既知の脆弱性があるコンポーネント**
   - [ ] 依存ライブラリの最新化
   - [ ] 脆弱性スキャン（npm audit等）

10. **ログとモニタリングの不足**
    - [ ] セキュリティイベントのログ
    - [ ] 異常検知の仕組み

## レビューレポート作成

### テンプレート使用

```markdown
# コードレビューレポート - [ファイル名]

## サマリー
- レビュー日: 2023-12-15
- レビュアー: qa agent
- 評価: ⭐⭐⭐⭐☆ (4/5)

## 問題点

### 重大 🔴
- SQLインジェクションの脆弱性 - Line 45 - パラメータ化クエリに変更
- 認証バイパスの可能性 - Line 78 - 認可チェック追加

### 警告 🟡
- パフォーマンス懸念 - Line 102 - N+1クエリ - JOINに統合
- コードの重複 - Line 150-180 - 関数化を推奨

### 提案 🟢
- 変数名の改善 - Line 23 - `d` → `userData`
- コメント追加 - Line 67 - 複雑なロジックの説明

## 良い点
- 適切なエラーハンドリング
- テストカバレッジが高い（85%）
- 明確な関数名

## 総評

全体的に良好なコードですが、セキュリティの重大な問題が2件あります。修正後に再レビューを推奨します。
```

## Codex CLI MCP統合

Codex CLI MCPを使用して自動レビューを実行:

```javascript
// Codex でセキュリティスキャン
const result = await codex({
  prompt: `
    以下のコードをレビューしてください:
    - セキュリティ脆弱性（OWASP Top 10）
    - コード品質（可読性、保守性）
    - パフォーマンス最適化の余地

    ${codeContent}
  `,
  approvalPolicy: 'on-request'
});

// レビュー結果を構造化
const review = parseReviewResult(result);
```

## ベストプラクティス

### DO（推奨）

✅ **体系的にレビュー**: チェックリストを順番に確認
✅ **自動ツール併用**: Codex、ESLint、Pylint等
✅ **具体的なフィードバック**: 行番号、修正案を明示
✅ **優先順位付け**: 重大 → 警告 → 提案
✅ **良い点も指摘**: モチベーション向上

### DON'T（非推奨）

❌ **主観的な評価**: データ・基準に基づく評価を
❌ **すべてを完璧に**: 重要な問題に集中
❌ **個人攻撃**: コードを批評、人を批評しない
❌ **一方的な指摘**: 対話を重視
❌ **自動ツールに全依存**: 人間の判断も重要

## Progressive Disclosure

このSKILL.mdはメインドキュメント（約350行）です。詳細なチェックリストは `checklists/` ディレクトリ内のファイルを参照してください。

## 関連Skill

- **qa-security-scan**: セキュリティ専門チェック
- **corder-code-templates**: ベストプラクティスに従ったコードテンプレート

## 関連リソース

- **checklists/general-checklist.md**: 一般的なチェックリスト
- **checklists/javascript-checklist.md**: JavaScript特有チェックリスト
- **checklists/python-checklist.md**: Python特有チェックリスト
- **checklists/security-checklist.md**: セキュリティチェックリスト
- **templates/review-report-template.md**: レビューレポートテンプレート
