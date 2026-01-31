#!/usr/bin/env node

/**
 * detect-package-manager.js
 * プロジェクトのパッケージマネージャーを自動検出（npm/pnpm/yarn/bun）
 */

const fs = require('fs');
const path = require('path');

async function main(hookContext) {
  const { config } = hookContext;
  const priority = config.priority || ['environment', 'projectFiles', 'lockFiles'];

  try {
    const projectRoot = process.cwd();
    let detectedPM = null;

    // 検出優先順位に従って実行
    for (const method of priority) {
      if (method === 'environment') {
        detectedPM = detectFromEnvironment();
      } else if (method === 'projectFiles') {
        detectedPM = detectFromProjectFiles(projectRoot);
      } else if (method === 'lockFiles') {
        detectedPM = detectFromLockFiles(projectRoot);
      }

      if (detectedPM) break;
    }

    if (!detectedPM) {
      detectedPM = 'npm'; // デフォルト
    }

    // 環境変数に設定（他のHooksやスクリプトで参照可能）
    process.env.PACKAGE_MANAGER = detectedPM;

    return { success: true, packageManager: detectedPM };
  } catch (error) {
    console.error('[affaan-m] detect-package-manager エラー:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * 環境変数から検出
 */
function detectFromEnvironment() {
  return process.env.npm_execpath?.includes('pnpm') ? 'pnpm' :
         process.env.npm_execpath?.includes('yarn') ? 'yarn' :
         process.env.npm_execpath?.includes('bun') ? 'bun' : null;
}

/**
 * プロジェクト設定ファイルから検出
 */
function detectFromProjectFiles(projectRoot) {
  const packageJsonPath = path.join(projectRoot, 'package.json');
  if (fs.existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    if (packageJson.packageManager) {
      return packageJson.packageManager.split('@')[0];
    }
  }
  return null;
}

/**
 * lockファイルから検出
 */
function detectFromLockFiles(projectRoot) {
  if (fs.existsSync(path.join(projectRoot, 'pnpm-lock.yaml'))) {
    return 'pnpm';
  }
  if (fs.existsSync(path.join(projectRoot, 'yarn.lock'))) {
    return 'yarn';
  }
  if (fs.existsSync(path.join(projectRoot, 'bun.lockb'))) {
    return 'bun';
  }
  if (fs.existsSync(path.join(projectRoot, 'package-lock.json'))) {
    return 'npm';
  }
  return null;
}

module.exports = main;

if (require.main === module) {
  main({
    config: { priority: ['environment', 'projectFiles', 'lockFiles'] },
  }).then(result => {
    console.log(`Detected package manager: ${result.packageManager}`);
    process.exit(result.success ? 0 : 1);
  });
}
