#!/usr/bin/env node

/**
 * detect-console-log.js
 * console.log や debugger の使用を検出して警告
 */

const fs = require('fs');

async function main(hookContext) {
  const { config, toolName, modifiedFiles } = hookContext;
  const patterns = config.patterns || ['console.log', 'console.debug', 'debugger'];

  if (!['Edit', 'Write'].includes(toolName)) {
    return { success: true };
  }

  try {
    const detectedIssues = [];

    for (const file of modifiedFiles || []) {
      if (!file.match(/\.(js|jsx|ts|tsx)$/)) continue;

      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');

      patterns.forEach(pattern => {
        lines.forEach((line, index) => {
          if (line.includes(pattern)) {
            detectedIssues.push({ file, line: index + 1, pattern });
          }
        });
      });
    }

    if (detectedIssues.length > 0) {
      console.warn('\n⚠️  [affaan-m] デバッグコードを検出しました:');
      detectedIssues.forEach(issue => {
        console.warn(`  ${issue.file}:${issue.line} - ${issue.pattern}`);
      });
      console.warn('  推奨: 本番コードからデバッグコードを削除してください\n');
    }

    return { success: true, detectedIssues };
  } catch (error) {
    console.error('[affaan-m] detect-console-log エラー:', error.message);
    return { success: false, error: error.message };
  }
}

module.exports = main;

if (require.main === module) {
  main({
    config: { patterns: ['console.log', 'console.debug', 'debugger'] },
    toolName: 'Edit',
    modifiedFiles: process.argv.slice(2),
  }).then(result => process.exit(result.success ? 0 : 1));
}
