#!/usr/bin/env node

/**
 * detect-package-manager.js
 * プロジェクトのパッケージマネージャーを自動検出（npm/pnpm/yarn/bun）
 *
 * PreToolUse Hook
 */

const fs = require('fs');
const path = require('path');

function detectFromEnvironment() {
  if (process.env.npm_execpath?.includes('pnpm')) return 'pnpm';
  if (process.env.npm_execpath?.includes('yarn')) return 'yarn';
  if (process.env.npm_execpath?.includes('bun')) return 'bun';
  return null;
}

function detectFromProjectFiles(projectRoot) {
  const packageJsonPath = path.join(projectRoot, 'package.json');
  if (fs.existsSync(packageJsonPath)) {
    try {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
      if (packageJson.packageManager) {
        return packageJson.packageManager.split('@')[0];
      }
    } catch {}
  }
  return null;
}

function detectFromLockFiles(projectRoot) {
  if (fs.existsSync(path.join(projectRoot, 'pnpm-lock.yaml'))) return 'pnpm';
  if (fs.existsSync(path.join(projectRoot, 'yarn.lock'))) return 'yarn';
  if (fs.existsSync(path.join(projectRoot, 'bun.lockb'))) return 'bun';
  if (fs.existsSync(path.join(projectRoot, 'package-lock.json'))) return 'npm';
  return null;
}

async function main() {
  try {
    const projectRoot = process.cwd();
    const detectedPM =
      detectFromEnvironment() ||
      detectFromProjectFiles(projectRoot) ||
      detectFromLockFiles(projectRoot) ||
      'npm';

    process.env.PACKAGE_MANAGER = detectedPM;

    const output = {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        additionalContext: `📦 [affaan-m] パッケージマネージャー: ${detectedPM}`,
        packageManager: detectedPM
      }
    };

    console.log(JSON.stringify(output));
    process.exit(0);
  } catch (error) {
    console.error(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        error: error.message
      }
    }));
    process.exit(1);
  }
}

main();
