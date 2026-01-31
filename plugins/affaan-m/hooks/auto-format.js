#!/usr/bin/env node

/**
 * auto-format.js
 * コード編集後に自動フォーマット（Prettier/ESLint）を実行
 */

const { execFile } = require('child_process');
const util = require('util');
const path = require('path');

const execFileAsync = util.promisify(execFile);

async function main(hookContext) {
  const { config, toolName, args, modifiedFiles } = hookContext;

  // Edit, Write ツールのみ対象
  if (!['Edit', 'Write'].includes(toolName)) {
    return { success: true };
  }

  const files = modifiedFiles || [];
  if (files.length === 0) {
    return { success: true };
  }

  try {
    const formattedFiles = [];

    for (const file of files) {
      // フォーマット対象ファイルかチェック
      if (!isFormattable(file)) continue;

      // Prettierでフォーマット
      if (config.prettier && await hasPrettier()) {
        try {
          await execFileAsync('npx', ['prettier', '--write', file]);
          formattedFiles.push(file);
        } catch (error) {
          console.warn(`[affaan-m] Prettier failed for ${file}: ${error.message}`);
        }
      }

      // ESLintで自動修正
      if (config.eslint && await hasESLint() && isJavaScriptFile(file)) {
        try {
          await execFileAsync('npx', ['eslint', '--fix', file]);
        } catch (error) {
          // ESLintエラーは警告のみ
          console.warn(`[affaan-m] ESLint failed for ${file}: ${error.message}`);
        }
      }
    }

    if (formattedFiles.length > 0) {
      console.log(`✨ [affaan-m] ${formattedFiles.length}個のファイルを自動フォーマットしました`);
    }

    return { success: true, formattedFiles };
  } catch (error) {
    console.error('[affaan-m] auto-format エラー:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Prettierがローカルにインストールされているか確認
 */
async function hasPrettier() {
  try {
    const localPrettierPath = path.join(process.cwd(), 'node_modules', '.bin', 'prettier');
    const fs = require('fs');
    return fs.existsSync(localPrettierPath);
  } catch {
    return false;
  }
}

/**
 * ESLintがローカルにインストールされているか確認
 */
async function hasESLint() {
  try {
    const localESLintPath = path.join(process.cwd(), 'node_modules', '.bin', 'eslint');
    const fs = require('fs');
    return fs.existsSync(localESLintPath);
  } catch {
    return false;
  }
}

/**
 * フォーマット対象ファイルか判定
 */
function isFormattable(file) {
  const formattableExtensions = [
    '.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.scss', '.md', '.html', '.yaml', '.yml'
  ];
  return formattableExtensions.some(ext => file.endsWith(ext));
}

/**
 * JavaScriptファイルか判定
 */
function isJavaScriptFile(file) {
  return /\.(js|jsx|ts|tsx)$/.test(file);
}

module.exports = main;

// CLIから直接実行された場合
if (require.main === module) {
  const hookContext = {
    config: { prettier: true, eslint: true },
    toolName: 'Edit',
    modifiedFiles: process.argv.slice(2),
  };
  main(hookContext).then(result => {
    process.exit(result.success ? 0 : 1);
  });
}
