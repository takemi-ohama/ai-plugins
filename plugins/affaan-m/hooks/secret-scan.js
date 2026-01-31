#!/usr/bin/env node

/**
 * secret-scan.js
 * コミット前にシークレット混入をチェック
 */

const fs = require('fs');
const path = require('path');

async function main(hookContext) {
  const { config, stagedFiles } = hookContext;
  const patterns = config.patterns || [];
  const blockCommit = config.blockCommit !== false; // デフォルトtrue

  try {
    const detectedSecrets = [];

    for (const file of stagedFiles || []) {
      // バイナリファイルやnode_modulesはスキップ
      if (shouldSkipFile(file)) continue;

      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');

      // 各パターンでスキャン
      for (const pattern of patterns) {
        const regex = createRegex(pattern);
        lines.forEach((line, index) => {
          if (regex.test(line)) {
            detectedSecrets.push({
              file,
              line: index + 1,
              pattern,
              content: line.trim().substring(0, 100), // 最初の100文字のみ
            });
          }
        });
      }
    }

    if (detectedSecrets.length > 0) {
      console.error('\n🚨 [affaan-m] シークレット混入を検出しました:\n');
      detectedSecrets.forEach(secret => {
        console.error(`  ファイル: ${secret.file}:${secret.line}`);
        console.error(`  パターン: ${secret.pattern}`);
        console.error(`  内容: ${secret.content}`);
        console.error('');
      });

      if (blockCommit) {
        console.error('❌ コミットをブロックしました');
        console.error('   修正後に再度コミットしてください\n');
        return { success: false, blocked: true, detectedSecrets };
      } else {
        console.warn('⚠️  警告のみ（コミットは継続）\n');
        return { success: true, warned: true, detectedSecrets };
      }
    }

    return { success: true };
  } catch (error) {
    console.error('[affaan-m] secret-scan エラー:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * パターンから正規表現を作成
 */
function createRegex(pattern) {
  // パターンマッピング
  const regexMap = {
    'AWS_ACCESS_KEY_ID': /AKIA[0-9A-Z]{16}/,
    'AWS_SECRET_ACCESS_KEY': /(AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*[:=]\s*['"]?[A-Za-z0-9/+=]{40}['"]?/,
    'GITHUB_TOKEN': /ghp_[A-Za-z0-9]{36}/,
    'SLACK_TOKEN': /xox[baprs]-[0-9a-zA-Z-]+/,
    '-----BEGIN PRIVATE KEY-----': /-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----/,
  };

  return regexMap[pattern] || new RegExp(pattern);
}

/**
 * スキップすべきファイルか判定
 */
function shouldSkipFile(file) {
  const skipPatterns = [
    'node_modules/',
    '.git/',
    'dist/',
    'build/',
    'coverage/',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.svg',
    '.ico',
    '.pdf',
    '.zip',
    '.tar',
    '.gz',
  ];

  return skipPatterns.some(pattern => file.includes(pattern));
}

module.exports = main;

// CLIから直接実行された場合
if (require.main === module) {
  const hookContext = {
    config: {
      patterns: [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'GITHUB_TOKEN',
        'SLACK_TOKEN',
        '-----BEGIN PRIVATE KEY-----',
      ],
      blockCommit: true,
    },
    stagedFiles: process.argv.slice(2),
  };
  main(hookContext).then(result => {
    process.exit(result.success ? 0 : 1);
  });
}
