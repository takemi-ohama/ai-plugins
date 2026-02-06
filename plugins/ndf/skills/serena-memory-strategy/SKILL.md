---
name: serena-memory-strategy
description: |
  Serena MCPのメモリー機能の利用戦略を定義します。メモリーの分類（中期/長期）、メタデータ要件、コミット数ベースのレビュー戦略、Skill vs Serena Memory の判断基準を提供します。

  このスキルは「Serena MCPメモリーをどう活用するか」のポリシーを提供します：
  - 中期メモリー：10-30コミットベースのレビュー
  - 長期メモリー：プロジェクトライフサイクル全体で有効
  - Skill vs Serena Memory の使い分け判断

  Triggers: "memory strategy", "Serena memory strategy", "Serena memory policy", "Serenaメモリー戦略", "メモリー分類", "メモリーポリシー", "レビュー戦略"
allowed-tools:
  - Read
  - Bash
---

# Skill: Serena MCP メモリー利用戦略

## Purpose

Serena MCPのメモリー機能において、**中期・長期メモリーをどう分類・構造化・メンテナンスするか**を定義するポリシーです。

以下の判断基準を提供します：
- 何をSerena Memoryに保存すべきか
- 何をSkillに留めるべきか
- メモリーをどう維持・更新するか

---

## Serena Memory の分類

### 中期メモリー（Mid-term）
- 数週間〜数ヶ月（または10-30コミット）有効
- 一時的・再検討が必要な判断を記録
- コミット数ベースのレビュー条件を必須とする

典型的な内容：
- フェーズ固有の判断
- PoC制約
- 実験結果
- 暫定的なアーキテクチャ選択

必須メタデータ：
- type: decision | assumption | experiment
- confidence: low | medium | high
- review_after_commits: N（10-30推奨）
- last_reviewed_commit: <hash>
- project: <project-name>

**コミット数ベースのレビュー間隔：**
- confidence: low → 10コミット
- confidence: medium → 20コミット
- confidence: high → 30コミット

---

### 長期メモリー（Long-term）
- プロジェクトライフサイクル全体で安定
- 原則や変更不可の制約を記録

典型的な内容：
- アーキテクチャ原則
- 法的・IP制約
- 組織ポリシー
- 技術思想

必須メタデータ：
- type: principle | constraint | policy
- confidence: high
- expires: none
- review_after_commits: none
- project: <project-name or global>

---

## Skill vs Serena Memory の判断チェックリスト

以下のいずれかに該当する場合、Serena Memoryに保存する：

- 将来のセッションで再利用される
- プロジェクト固有である
- *how*（手順）ではなく*why*（理由）を説明する
- 将来の選択を制約する
- 改訂や失効の可能性がある
- Skillに含めると肥大化する

いずれにも該当しない場合はSkillに留めるか、一時的な情報として扱う。

---

## メモリー粒度ルール

- 1メモリーエントリ = 1判断または1原則
- 事実・仮定・結論を混在させない
- 完全性より明確性を優先
- 手順の埋め込みを避ける

---

## メモリーメンテナンスポリシー

- 中期メモリーはコミット数ベースでレビュー必須
- `/ndf:mem-review` でレビュー期限をチェック
- 陳腐化したメモリーはアーカイブまたは削除
- 長期メモリーの変更は慎重に行う

---

## アンチパターン

- 手順をメモリーに保存する
- 判断をSkill内にエンコードする
- 同じトピックで重複メモリーを作成する
- 実験的な仮定を未レビューのまま放置する
- 日付ベースのレビューを使う（コミット数ベースを使用すること）

---

## コミット数ベースのレビュー戦略

**なぜコミット数ベースか？**
- 実際の開発活動と連動する
- 活発な時期 → 頻繁にレビュー
- 停滞期 → 無駄なレビューを回避
- プロジェクトのペースに自動調整

**仕組み：**
1. メモリーに `review_after_commits: 20` を記録
2. メモリーに `last_reviewed_commit: abc123` を記録
3. レビュー時: `git rev-list --count abc123..HEAD` を計算
4. カウント >= 20 ならレビュー実施

**関連コマンド：**
- `/ndf:mem-review` - レビュー期限のチェックと実施
- `/ndf:mem-capture` - コミット数ベースレビュー付きメモリー記録

---

## 基本原則

> Skillは振る舞いを定義する。
> Serena Memoryは判断と事実を記録する。
