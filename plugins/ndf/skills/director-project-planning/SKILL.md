---
name: director-project-planning
description: |
  Create structured project plans with task breakdown, timeline, resource allocation, and risk assessment. Use when starting new features, refactoring, or complex implementations.

  This skill automatically generates comprehensive project plans including:
  - Task decomposition with clear milestones
  - Resource allocation (which sub-agents to use)
  - Parallel execution recommendations
  - Risk identification and mitigation strategies
  - Timeline estimation

  Triggers: "plan", "roadmap", "task breakdown", "project structure", "計画", "プロジェクト構造", "タスク分解"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
---

# Director Project Planning Skill

## 概要

このSkillは、directorエージェントが新機能実装、リファクタリング、複雑な実装タスクを計画する際に使用します。構造化されたプロジェクト計画書を自動生成し、タスク分解、タイムライン設定、リソース配分、リスク評価を支援します。

## 主な機能

1. **プロジェクト計画書の生成**: 標準化されたフォーマットで計画書を作成
2. **タスク分解**: 大きなタスクを実行可能な小タスクに分解
3. **リソース配分**: どのサブエージェント（corder, data-analyst等）を使用するか提案
4. **並列実行判断**: ファイル重複がないタスクを並列実行可能と識別
5. **リスク評価**: 潜在的なリスクと対策を明示

## 使用方法

### 基本的な使い方

1. **プロジェクト概要を入力**:
   - プロジェクト名
   - 目的・目標
   - スコープ（実装範囲）
   - 期限（オプション）

2. **計画書生成スクリプトを実行**:
   ```bash
   node scripts/generate-plan.js
   ```

3. **生成された計画書を確認**:
   - `issues/`ディレクトリに保存されます
   - 必要に応じて手動で調整

### トリガーキーワード

以下のキーワードを含むユーザーリクエストで自動起動されます:
- "plan" / "計画"
- "roadmap" / "ロードマップ"
- "task breakdown" / "タスク分解"
- "project structure" / "プロジェクト構造"

## テンプレート

### project-plan-template.md

プロジェクト計画書の基本テンプレート。以下のセクションを含みます:
- プロジェクト概要（目的、スコープ、期限）
- タスク分解（フェーズごとの詳細タスク）
- リソース配分（サブエージェント割り当て）
- 並列実行推奨（並列可能なタスクの識別）
- リスク評価（リスクと対策）

### task-breakdown-template.md

タスク分解の詳細テンプレート。各タスクについて:
- タスク名と説明
- 担当サブエージェント
- 所要時間見積もり
- 依存関係
- 受入基準

### risk-assessment-template.md

リスク評価テンプレート:
- リスク項目
- 発生確率（高/中/低）
- 影響度（高/中/低）
- 対策方法

## スクリプト

### generate-plan.js

プロジェクト計画書を対話的に生成するスクリプト。

**機能**:
- ユーザーからプロジェクト情報を収集
- テンプレートを読み込み、動的に項目を埋める
- タスク分解を提案（調査→設計→実装→テスト→ドキュメント）
- サブエージェント推奨（コーディング→corder、データ分析→data-analyst等）
- 並列実行可能なタスクを特定
- `issues/`ディレクトリに自動保存

**使用例**:
```bash
cd plugins/ndf/skills/director-project-planning
node scripts/generate-plan.js
```

対話形式でプロジェクト情報を入力すると、計画書が生成されます。

## 実装例

### 例1: 新機能実装の計画

**ユーザーリクエスト**:
"ユーザー認証機能の実装計画を作成してください"

**生成される計画書**:
- フェーズ1: 要件調査（認証方式、セキュリティ要件）
- フェーズ2: 設計（データベーススキーマ、API設計）
- フェーズ3: 実装（バックエンドAPI、フロントエンド）
- フェーズ4: テスト（単体テスト、統合テスト、セキュリティテスト）
- フェーズ5: ドキュメント（API仕様書、README更新）

**サブエージェント配分**:
- フェーズ1: researcher（認証ベストプラクティス調査）
- フェーズ2: data-analyst（DBスキーマ設計）
- フェーズ3: corder（実装）
- フェーズ4: qa（テスト・セキュリティスキャン）
- フェーズ5: corder（ドキュメント生成）

**並列実行推奨**:
- フェーズ3のバックエンドとフロントエンド実装は並列可能
- フェーズ4の単体テストとセキュリティテストは並列可能

### 例2: リファクタリング計画

**ユーザーリクエスト**:
"レガシーコードのリファクタリング計画を作成"

**生成される計画書**:
- フェーズ1: コードベース分析（Serena MCPでシンボル調査）
- フェーズ2: リファクタリング対象の特定
- フェーズ3: テストコード作成（既存動作の保証）
- フェーズ4: リファクタリング実行
- フェーズ5: コードレビュー（品質・セキュリティ確認）

**リスク評価**:
- リスク1: 既存機能の破壊 - 対策: テストカバレッジ100%確保
- リスク2: パフォーマンス劣化 - 対策: ベンチマーク実行
- リスク3: マージコンフリクト - 対策: 小さなPRに分割

## 注意事項

- 計画書は出発点であり、実装中に調整が必要な場合があります
- リスク評価は初期段階での識別であり、定期的に見直しが必要です
- 並列実行推奨は理想的なシナリオであり、実際のリソース状況に応じて調整してください
- 生成されたスクリプトは対話的に実行されるため、非対話環境では動作しない場合があります

## Progressive Disclosure

このSKILL.mdはメインドキュメント（約150行）です。詳細なテンプレート例やスクリプトコードは別ファイル（templates/, scripts/）に分離されており、必要に応じて参照できます。

## 関連リソース

- **テンプレート**: `templates/`ディレクトリ内の各種テンプレート
- **スクリプト**: `scripts/generate-plan.js`
- **関連Skill**: director-github-integration（計画書からGitHub Issue作成）
