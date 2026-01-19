# 開発履歴と知見 (2026-01-18)

## 期間
2025-11-15 〜 2026-01-18

## 主要な開発内容

### 1. NDF v2.0.0: 公式プラグインとの機能重複解消 (PR #66)

**課題:**
GitHub MCP、Serena MCP、Context7 MCPが`anthropics/claude-plugins-official`公式プラグインと重複。

**実施内容:**
- 重複する3つのMCPサーバーをNDFから削除
- 公式プラグインへの移行を推奨
- MCP: 10個→7個に削減

**コミット:**
- 1aab6ab: feat(ndf): v2.0.0 - 公式プラグインと重複する機能を削除

**重要な学び:**
1. **公式プラグインを優先**: Claude Code公式プラグインが提供する機能は重複しないように削除
2. **移行ガイダンス**: ユーザーに公式プラグインのインストール方法を明記

### 2. NDF v2.1.0: directorエージェント追加とSlack通知簡略化 (PR #68)

**課題:**
- 複雑なマルチステップタスクでMain Agentのコンテキストが肥大化
- Slack通知のセッションサマリー生成が複雑

**実施内容:**
- **directorサブエージェント追加**: 複雑なタスクを統括するオーケストレーター
- **Slack通知の簡略化**: Claude CLIによる要約生成を標準化
- **エージェントのプロアクティブ利用**: 各エージェントの説明にプロアクティブトリガーを追加

**コミット:**
- e7e2eac: feat(ndf): v2.1.0 - directorエージェント追加とslack-notify簡略化
- 2bc3d2b: fix: レビュー指摘対応 - slack-notify.jsのエラーハンドリング改善
- 383d808: fix: README.mdのセッションログ説明を明確化

**重要な学び:**
1. **director = オーケストレーター**: Main Agentは最小限に、directorがタスク全体を統括
2. **サブエージェント間の直接呼び出し禁止**: メモリエラー防止のためMain Agentが中継
3. **プロアクティブ利用**: エージェント説明に「Use proactively for:」を追加して自動委譲を促進

### 3. Slack通知の要約生成問題と解決 (PR #71-#74)

**課題:**
Slack通知の要約生成で複数の問題が発生：
1. transcript解析の不安定さ
2. Claude CLI呼び出しのタイムアウト
3. メモリ使用量の増大

**試行錯誤の履歴:**

#### PR #71: セッション要約生成の修正
- 要約生成ロジックのバグ修正
- **コミット:** c1f3681

#### PR #72: 常にCLIで日本語生成
- transcript解析をやめ、常にClaude CLIで要約を生成
- 日本語の品質向上
- **コミット:** 38a654a

#### PR #73: 要約抽出ロジックの改善とリファクタリング
- 要約抽出ロジックを全面リファクタ
- メモリ/タイムアウト問題の修正
- **コミット:** 30db505, 55921bf

#### PR #74: spawnタイムアウト処理の修正とエージェントのプロアクティブ利用促進
- Node.js spawnのタイムアウト処理を改善
- 各エージェント定義にプロアクティブトリガーを追加
- **コミット:** 40b66da, e53a821

**最終推奨実装（Node.js spawn with timeout）:**
```javascript
const { spawn } = require('child_process');

function runClaudeWithTimeout(prompt, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const claude = spawn('claude', [
      '-p',
      '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}',
      '--output-format', 'text'
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: timeoutMs
    });

    let output = '';
    let errorOutput = '';

    claude.stdout.on('data', (data) => {
      output += data.toString();
    });

    claude.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    claude.on('close', (code) => {
      if (code === 0) {
        resolve(output.trim());
      } else {
        reject(new Error(`Claude exited with code ${code}: ${errorOutput}`));
      }
    });

    claude.on('error', (err) => {
      reject(err);
    });

    // タイムアウト処理
    setTimeout(() => {
      if (!claude.killed) {
        claude.kill('SIGTERM');
        reject(new Error('Claude CLI timeout'));
      }
    }, timeoutMs);

    // プロンプトを送信
    claude.stdin.write(prompt);
    claude.stdin.end();
  });
}
```

**重要な学び:**
1. **常にCLI生成を優先**: transcript解析は不安定なため、Claude CLIで要約を生成
2. **タイムアウト処理は必須**: spawnにtimeoutオプションを設定し、手動でもタイムアウト処理を実装
3. **メモリ管理**: 大きなtranscriptファイルを全読み込みしない
4. **エラーハンドリング**: spawnのエラーイベントを適切に処理

### 4. エージェントのプロアクティブ利用促進

**課題:**
サブエージェントが適切なタイミングで呼び出されない。

**実施内容:**
各エージェント定義に「Use proactively for:」セクションを追加：

```markdown
**Available subagent_type (with proactive triggers):**
- `ndf:director` - **Orchestrator** | Use proactively for: complex multi-step tasks, planning/design decisions, multi-agent coordination
- `ndf:corder` - Coding expert | Use proactively for: code implementation, refactoring, code review, design patterns
- `ndf:data-analyst` - Data analysis expert | Use proactively for: SQL queries, BigQuery, data analysis, data export
- `ndf:researcher` - Research expert | Use proactively for: AWS docs research, technical investigation, web scraping
- `ndf:scanner` - File reading expert | Use proactively for: PDF reading, image OCR, Office file extraction
- `ndf:qa` - QA expert | Use proactively for: security review (OWASP), code quality, performance testing
```

**コミット:**
- e53a821: fix: Slack通知の要約生成を修正し、エージェントのプロアクティブ利用を促進

**重要な学び:**
1. **明示的なトリガー条件**: 「Use proactively for:」で具体的な条件を列挙
2. **Main Agent側のガイドライン**: CLAUDE.ndf.mdにサブエージェント活用フローを明記
3. **director優先**: 複雑なタスクはdirectorに委譲し、directorが他のエージェントを統括

## 重要な教訓

### 1. Slack通知実装時のポイント

- **常にClaude CLIで要約生成**（transcript解析は不安定）
- **タイムアウト処理は二重に実装**（spawnオプション + setTimeout）
- **hooksとpluginsを無効化**（`--settings '{"disableAllHooks": true, "disableAllPlugins": true}'`）
- **メモリ管理に注意**（大きなファイルの全読み込みを避ける）

### 2. サブエージェント設計のポイント

- **director = オーケストレーター**として複雑なタスクを統括
- **サブエージェント間の直接呼び出し禁止**（Main Agentが中継）
- **プロアクティブトリガーを明示**（「Use proactively for:」）
- **Claude Code組み込み機能を活用**（Plan Mode、Explore Agent）

### 3. 公式プラグインとの共存

- **重複機能は削除**して公式プラグインを推奨
- **移行ガイダンスを提供**（インストールコマンドを明記）
- **NDF固有の価値に集中**（専門エージェント、Slack通知、ワークフローコマンド）

## 次回開発時の注意点

1. **Slack通知実装時:**
   - Claude CLIで要約生成を優先
   - タイムアウト処理を必ず実装
   - spawnの二重タイムアウト（オプション + setTimeout）

2. **エージェント追加時:**
   - 「Use proactively for:」を必ず追加
   - CLAUDE.ndf.mdのAvailable subagent_typeセクションを更新
   - 他のサブエージェントを直接呼び出さない設計

3. **MCP追加時:**
   - 公式プラグインと重複しないか確認
   - 重複する場合は公式プラグインを推奨

4. **ドキュメント更新時:**
   - CLAUDE.ndf.mdのVERSIONコメントを更新
   - plugin.jsonのバージョンをインクリメント
   - Serenaメモリーを更新

## 関連ファイル

- `plugins/ndf/CLAUDE.ndf.md` - プラグイン利用者向けガイドライン（v2.1.3）
- `plugins/ndf/CLAUDE.md` - 開発者向けガイドライン
- `plugins/ndf/scripts/slack-notify.js` - Slack通知スクリプト（Node.js）
- `plugins/ndf/agents/*.md` - 6つの専門エージェント定義
- `plugins/ndf/.claude-plugin/plugin.json` - プラグインメタデータ

## 参考リンク

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [Claude Plugins Official](https://github.com/anthropics/claude-plugins-official)
- [Slack API Documentation](https://api.slack.com/)

## 統計

**期間:** 2025-11-15 〜 2026-01-18
**PRマージ数:** 9件（PR #66-#74）
**主要な変更:**
- NDF v2.0.0: 公式プラグインとの重複解消
- NDF v2.1.0: directorエージェント追加
- NDF v2.1.3: Slack通知の安定化とエージェントのプロアクティブ利用促進
