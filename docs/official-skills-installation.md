# Anthropic公式Skillsのインストール手順

Anthropicは `anthropics/skills` リポジトリで高品質なSkillを公開しています。本ドキュメントはNDFプラグインの利用者向けに、**ライセンス状況別の取り込み方法**をまとめます。

調査日: 2026-04-23
参照: https://github.com/anthropics/skills

## ライセンス別の分類

Anthropic公式Skillは**Skill単位でライセンスが異なる**ため、必ず `skills/<skill>/LICENSE.txt` を確認してください。

### Apache License 2.0（再配布・派生物OK）

これらはNDFプラグインに**バンドル済み** or 自由にコピー可能:

| Skill | 用途 |
|---|---|
| `mcp-builder` | MCPサーバー雛形生成（Python FastMCP / Node TypeScript SDK） |
| `skill-creator` | 新規Skill作成ガイド |

### プロプライエタリ（再配布・派生物禁止）

これらは**各利用者が自分の環境に個別インストール**する必要があります。NDFプラグインに同梱できません。

| Skill | 用途 |
|---|---|
| `docx` | Word文書の作成・編集 |
| `pptx` | PowerPoint作成・編集 |
| `xlsx` | Excel作成・編集 |
| `pdf` | PDF処理（読取・生成） |
| `doc-coauthoring` | 長編ドキュメント共同編集 |
| `web-artifacts-builder` | HTML/Reactアプリ生成 |
| `webapp-testing` | Playwrightでのテスト |
| `frontend-design` | フロントエンド設計 |
| その他 | brand-guidelines, canvas-design, theme-factory, algorithmic-art, slack-gif-creator, internal-comms, claude-api, algorithmic-art 等 |

> **ライセンス表記例**（公式docx/pptx/xlsxに含まれる `LICENSE.txt` より）:
> 「© 2025 Anthropic, PBC. All rights reserved. これらの資料をAnthropicのサービスから抽出または外部に保持すること、複製、派生物作成を禁止する」

## プロプライエタリSkillのインストール方法（個人利用）

各利用者が自分のローカル環境に公式リポジトリをcloneし、Claude Codeから参照する構成:

### 方法1: ユーザー領域に配置（`~/.claude/skills/`）

```bash
# 公式リポジトリをcloneまたはpull
git clone https://github.com/anthropics/skills.git ~/work/anthropic-skills

# 使いたいSkillのみシンボリックリンクを張る
mkdir -p ~/.claude/skills
ln -s ~/work/anthropic-skills/skills/docx ~/.claude/skills/docx
ln -s ~/work/anthropic-skills/skills/pptx ~/.claude/skills/pptx
ln -s ~/work/anthropic-skills/skills/xlsx ~/.claude/skills/xlsx

# Claude Code を再起動 or /plugin reload でSkill反映
```

### 方法2: プロジェクト単位に配置（`.claude/skills/`）

プロジェクトごとに異なるSkillを使いたい場合:

```bash
cd /path/to/your/project
mkdir -p .claude/skills
cp -r ~/work/anthropic-skills/skills/docx .claude/skills/
# pptx, xlsx も同様
```

プロジェクト `.claude/skills/` に配置したSkillは、そのプロジェクト内でのみ有効。

### 注意事項

- 公式Skillは`LICENSE.txt`でAnthropicサービスの利用規約に準拠する必要があると定めているため、**Claude Code / Claude.ai 上での利用に限定**してください
- プロプライエタリSkillを**他者に再配布しない**（リポジトリに含めない、社内共有リポジトリに置かない）
- CIでの自動利用やビルド成果物への取り込みは規約違反になる可能性があります

## NDFプラグインとの関係

### NDFが取り込んでいる公式Skill（Apache-2.0のみ）

- `mcp-builder` → `plugins/ndf/skills/mcp-builder/`（LICENSE.txt同梱）

### NDFが代替を提供しないSkill

以下は公式利用を推奨し、NDFには独自実装を置きません:
- `docx` / `pptx` / `xlsx`: 上記「方法1/2」で個別インストール
- その他プロプライエタリSkill: 同上

## Claude Code側での認識確認

インストール後、Claude Codeで以下で確認できます:

```
/skill list
```

`docx` / `pptx` / `xlsx` などが表示されればOK。Skillが表示されない場合:

- Claude Codeを再起動（`Ctrl+C` → 再度起動）
- `SKILL.md` のYAMLフロントマターが有効か確認
- `.claude/skills/<name>/SKILL.md` のパスが正しいか確認

## 参考

- 公式リポジトリ: https://github.com/anthropics/skills
- Skills公式ドキュメント: https://docs.claude.com/en/docs/claude-code/skills
- NDFでのSkills実装例: `plugins/ndf/skills/`
- Skillフロントマター仕様: [docs/claude-code-skills-official-reference.md](./claude-code-skills-official-reference.md)
