#!/usr/bin/env node

/**
 * typescript-check.js
 * TypeScript型チェックを自動実行
 */

const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

async function main(hookContext) {
  const { config, toolName, modifiedFiles } = hookContext;

  if (!['Edit', 'Write'].includes(toolName)) {
    return { success: true };
  }

  const tsFiles = (modifiedFiles || []).filter(f => f.match(/\.(ts|tsx)$/));
  if (tsFiles.length === 0) {
    return { success: true };
  }

  try {
    // TypeScriptがインストールされているか確認
    try {
      await execAsync('npx tsc --version');
    } catch {
      return { success: true }; // TypeScript未導入プロジェクトはスキップ
    }

    // 型チェック実行
    const { stdout, stderr } = await execAsync('npx tsc --noEmit');

    return { success: true };
  } catch (error) {
    console.warn('\n⚠️  [affaan-m] TypeScript型エラーを検出しました:');
    console.warn(error.stdout || error.message);
    console.warn('  推奨: 型エラーを修正してください\n');
    return { success: true, hasTypeErrors: true }; // 警告のみ
  }
}

module.exports = main;

if (require.main === module) {
  main({
    config: {},
    toolName: 'Edit',
    modifiedFiles: process.argv.slice(2),
  }).then(result => process.exit(result.success ? 0 : 1));
}
