---
name: skill-stats
description: "Claude Codeのtranscriptを集計してSkill利用統計を算出する。呼び出し数、関連話題出現数、ヒット率を出力。特定skillの利用傾向分析や新規skill候補の発見に使う。Triggers: 'skill stats', 'skill統計', 'skill利用分析', 'skill usage', 'skill hit rate'"
disable-model-invocation: false
allowed-tools:
  - Bash
  - Read
---

# Skill 利用統計スキル

Claude Code の transcript JSONL ファイル (`~/.claude/projects/*.jsonl`) を解析し、NDFプラグインのskill利用統計を算出する。

## 用途

- どの skill がよく呼び出されているか把握
- 呼び出されるべきだったのに呼ばれなかった skill を発見
- skill の description / triggers の網羅性改善に役立てる

## 使用方法

```bash
# 過去90日分を集計 (デフォルト、transcript保持期間に合わせる)
/ndf:skill-stats

# 期間指定
/ndf:skill-stats --days 30

# 特定のskillだけ見る
/ndf:skill-stats --skill pr

# JSON出力
/ndf:skill-stats --format json
```

内部的には以下のコマンドを実行する:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-stats/scripts/skill-stats.py "$@"
```

## 集計項目

| 項目 | 定義 |
|---|---|
| **呼び出し数** (invocations) | `assistant` メッセージ内の `tool_use.name=="Skill"` で `input.skill=="ndf:<name>"` の件数 |
| **関連話題数** (triggers) | `user` メッセージのテキストに、skillの `description` / Triggers キーワードが含まれる件数 |
| **ヒット数** (hits) | 関連話題を含むユーザーメッセージの直後 (次のユーザーメッセージまでの間) に該当skillが呼ばれた件数 |
| **ヒット率** (hit_rate) | `hits / triggers` (%) |

### ヒット率の解釈

- **高い (80%+)**: description/triggers が適切で、該当文脈で正しく起動できている
- **低い (< 30%)**: キーワードが広すぎて関係ない話題にマッチしているか、モデルがskillを起動しにくい description になっている可能性
- **triggers が 0**: description のキーワードがユーザー入力に出現していない → 該当用途で使われていないか、triggersの定義見直しが必要

## 出力例 (Markdown)

```
| skill | 呼び出し数 | 関連話題 | ヒット | ヒット率 |
|---|---:|---:|---:|---:|
| ndf:pr | 12 | 25 | 10 | 40.0% |
| ndf:fix | 3 | 8 | 3 | 37.5% |
...
| **合計** | **56** | **142** | **45** | **31.7%** |
```

## 前提条件

- Python 3.8+ (標準ライブラリのみ使用)
- `~/.claude/projects/` に transcript JSONL が存在
- transcript の保持期間は `~/.claude/settings.json` の `cleanupPeriodDays` に依存。NDFプラグインの保持期間フックが 90 日を確保する

## 制限事項

- **モデル起動型以外は関連話題数が計算できない場合がある**: `disable-model-invocation: true` の skill (例: `/ndf:pr` などのワークフロー系) は、ユーザーが明示的にスラッシュコマンドで呼び出すのが通常。triggers キーワードが description に明示されていなければ「関連話題」が 0 となり、ヒット率も計算不能となる
- **ユーザーメッセージのパース**: `<local-command-*>`, `<command-name>`, `<system-reminder>` タグは除外する。tool_result ブロックも除外
- **日本語キーワードマッチ**: 単純な部分一致 (case-insensitive) のため、文脈を考慮した判定ではない

## 関連スキル

- `/ndf:markdown-writing` — 結果を読みやすく整形するためのガイドライン
- `/ndf:python-execution` — Python実行環境の判定
