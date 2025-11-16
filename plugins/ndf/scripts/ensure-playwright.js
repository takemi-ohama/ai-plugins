#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || __dirname;
const FLAG_FILE = path.join(os.homedir(), '.claude-ndf-playwright-installed');
const TIMEOUT_MS = 5 * 60 * 1000; // 5分タイムアウト

// 既にインストール済みかチェック（冪等性）
if (fs.existsSync(FLAG_FILE)) {
  process.exit(0);
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('🎭 NDF Plugin: 初回セットアップ');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('');
console.log('Playwright Chromiumブラウザをインストール中...');
console.log('ネットワーク環境により1-2分かかる場合があります。');
console.log('');

try {
  // npx playwright install chromium を実行
  execSync('npx playwright install chromium', {
    stdio: 'inherit',
    cwd: PLUGIN_ROOT,
    timeout: TIMEOUT_MS,
    env: {
      ...process.env,
      PLAYWRIGHT_SKIP_BROWSER_GC: '1'
    }
  });

  // インストール成功フラグを作成
  const flagData = {
    installed: new Date().toISOString(),
    plugin: 'ndf',
    browser: 'chromium'
  };

  fs.writeFileSync(FLAG_FILE, JSON.stringify(flagData, null, 2));

  console.log('');
  console.log('✅ セットアップ完了！Playwright Chromiumの準備ができました。');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  process.exit(0);

} catch (error) {
  console.error('');
  console.error('❌ Playwright Chromiumのインストールに失敗しました');
  console.error('');
  console.error('エラー:', error.message);
  console.error('');
  console.error('手動でインストールするには以下を実行してください:');
  console.error('  npx playwright install chromium');
  console.error('');
  console.error('トラブルシューティング:');
  console.error('  https://playwright.dev/docs/browsers');
  console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  process.exit(1);
}
