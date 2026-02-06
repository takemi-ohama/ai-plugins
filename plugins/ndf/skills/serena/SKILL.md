---
name: serena
description: "開発の履歴や知見をSerena MCPメモリーに記録する"
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Edit
---

# 記憶コマンド

開発の履歴や得られた知見を記録する。
特に*Agentの推論や操作の失敗、コマンドの誤り、指示の誤解*などについて記録しておくことで*再発を防止*する。

## 手順

1. AI Agentの履歴から何を行ったかを収集
   - 特に操作の失敗やユーザからの追加指示、誤解の修正について重点的にまとめる
2. CLAUDE.mdの記憶の更新日時以降のgit logやファイル変更内容、セッション履歴をもとに知見を収集
   - 更新日時が記録されていない場合は直近のPR作成日時以降を対象
3. Serena MCPに上記の知見を記憶
4. Serena MCPの記憶をチェックし、誤りがあれば修正、古くなっていれば削除
5. AGENTS.mdのSerenaの利用方法を更新
6. 記憶の更新日時をCLAUDE.mdに記録

## 作業完了報告（必須）

- 対象期間
- 記録した知見（件数、カテゴリ別、主なトピック）
- 更新したSerenaメモリー
- 関連するPR/コミット
- CLAUDE.mdの更新確認
