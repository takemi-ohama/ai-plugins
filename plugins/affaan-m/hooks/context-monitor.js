#!/usr/bin/env node

/**
 * context-monitor.js
 * コンテキスト使用率を監視し、閾値を超えたら警告を表示
 */

const fs = require('fs');
const path = require('path');

async function main(hookContext) {
  const { config } = hookContext;
  const threshold = config.threshold || 60;

  try {
    // ⚠️ 警告: getContextUsage()は仮想実装（Math.random()）です
    // 実際のClaude Code APIが利用可能になるまで、このHookは正確なモニタリングを提供しません
    // 実運用環境ではこのHookを無効化することを推奨します
    const contextUsage = getContextUsage();

    if (contextUsage >= threshold) {
      const severity = contextUsage >= 80 ? 'CRITICAL' : 'WARNING';
      const emoji = contextUsage >= 80 ? '🚨' : '⚠️';

      console.warn(`\n${emoji} [affaan-m] コンテキスト使用率: ${contextUsage}% (${severity})`);

      if (contextUsage >= 80) {
        console.warn('  推奨: 即座に /compact を実行してください');
      } else {
        console.warn('  推奨: /compact でコンテキストを圧縮してください');
      }

      // MCP数の確認
      const mcpCount = getMCPCount();
      if (mcpCount > 10) {
        console.warn(`  ⚠️  アクティブMCPサーバー: ${mcpCount}個（推奨: 10個以下）`);
        console.warn('  推奨: 未使用のMCPサーバーを無効化してください');
      }

      console.warn('');
    }

    return { success: true };
  } catch (error) {
    console.error('[affaan-m] context-monitor エラー:', error.message);
    // Hookが失敗してもメイン処理は継続
    return { success: true, skipped: true, error: error.message };
  }
}

/**
 * コンテキスト使用率を取得（仮想実装）
 * 実際の実装では Claude Code の内部APIを使用
 */
function getContextUsage() {
  // 仮想的な実装
  // 実際には Claude Code の内部状態から取得
  return Math.floor(Math.random() * 100);
}

/**
 * アクティブなMCPサーバー数を取得（仮想実装）
 */
function getMCPCount() {
  try {
    const mcpConfigPath = path.join(process.env.HOME || process.env.USERPROFILE, '.config', 'claude-code', 'mcp.json');
    if (fs.existsSync(mcpConfigPath)) {
      const mcpConfig = JSON.parse(fs.readFileSync(mcpConfigPath, 'utf-8'));
      return Object.keys(mcpConfig.mcpServers || {}).length;
    }
  } catch (error) {
    // エラーは無視
  }
  return 0;
}

module.exports = main;

// CLIから直接実行された場合
if (require.main === module) {
  const hookContext = {
    config: { threshold: 60, autoWarn: true },
    toolName: process.argv[2] || 'unknown',
    args: process.argv.slice(3),
  };
  main(hookContext).then(result => {
    process.exit(result.success ? 0 : 1);
  });
}
