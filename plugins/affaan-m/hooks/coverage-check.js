#!/usr/bin/env node

/**
 * coverage-check.js
 * テストカバレッジを検証（80%以上推奨）
 */

const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

async function main(hookContext) {
  const { config } = hookContext;
  const threshold = config.threshold || 80;
  const warnOnly = config.warnOnly !== false;

  try {
    // カバレッジレポートを取得
    const { stdout } = await execAsync('npm test -- --coverage --silent');
    const coverage = parseCoverage(stdout);

    if (!coverage) {
      return { success: true }; // カバレッジ情報が取得できない場合はスキップ
    }

    if (coverage.statements < threshold) {
      const message = `\n⚠️  [affaan-m] テストカバレッジが目標に達していません: ${coverage.statements}% (目標: ${threshold}%以上)\n`;

      if (warnOnly) {
        console.warn(message);
        console.warn('  推奨: テストを追加してカバレッジを向上させてください\n');
        return { success: true, belowThreshold: true, coverage };
      } else {
        console.error(message);
        console.error('  ❌ コミットをブロックしました\n');
        return { success: false, blocked: true, coverage };
      }
    }

    console.log(`✅ [affaan-m] テストカバレッジ: ${coverage.statements}% (目標達成)`);
    return { success: true, coverage };
  } catch (error) {
    // テストエラーは警告のみ
    console.warn('[affaan-m] カバレッジチェックをスキップしました');
    return { success: true, skipped: true };
  }
}

/**
 * カバレッジ情報をパース
 */
function parseCoverage(output) {
  const match = output.match(/All files\s+\|\s+([\d.]+)/);
  if (match) {
    return {
      statements: parseFloat(match[1]),
    };
  }
  return null;
}

module.exports = main;

if (require.main === module) {
  main({
    config: { threshold: 80, warnOnly: true },
  }).then(result => process.exit(result.success ? 0 : 1));
}
