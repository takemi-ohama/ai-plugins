#!/usr/bin/env node

/**
 * SessionStart Hook: NDFプラグインガイドの配置とインポート
 *
 * 【要件】
 * CLAUDE.mdのある場所にCLAUDE.ndf.mdを作成する。
 * CLAUDE.mdがどこにもなければCLAUDE.ndf.mdも作成しない。
 *
 * 【処理フロー】
 * 1. CLAUDE.md/AGENT.mdの場所を探す（プロジェクトルート or ~/.claude/）
 * 2. 見つかった場合、同じディレクトリにCLAUDE.ndf.mdをコピー
 * 3. CLAUDE.md/AGENT.mdに @CLAUDE.ndf.md のインポート行を追加
 */

const fs = require('fs');
const path = require('path');

// ============================================================
// 設定
// ============================================================

const projectRoot = process.cwd();
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;

if (!pluginRoot) {
  console.error('Error: CLAUDE_PLUGIN_ROOT environment variable not set');
  process.exit(1);
}

const PLUGIN_GUIDE_SOURCE = path.join(pluginRoot, 'CLAUDE.ndf.md');
const IMPORT_LINE = '@CLAUDE.ndf.md';

// ============================================================
// CLAUDE.md/AGENT.mdの場所を探す
// ============================================================

/**
 * CLAUDE.md または AGENT.md の場所を探す
 *
 * 優先順位:
 * 1. プロジェクトルート/CLAUDE.md
 * 2. プロジェクトルート/AGENT.md
 * 3. ~/.claude/CLAUDE.md
 * 4. ~/.claude/AGENT.md
 *
 * @returns {string|null} 見つかったファイルのパス、見つからない場合はnull
 */
function findClaudeMdLocation() {
  const candidates = [
    path.join(projectRoot, 'CLAUDE.md'),
    path.join(projectRoot, 'AGENT.md'),
    path.join(projectRoot, '.claude', 'CLAUDE.md'),
    path.join(projectRoot, '.claude', 'AGENT.md')
  ];

  for (const filePath of candidates) {
    if (fs.existsSync(filePath)) {
      return filePath;
    }
  }

  return null;
}

// ============================================================
// CLAUDE.ndf.mdをコピーする
// ============================================================

/**
 * プラグインガイドをターゲットディレクトリにコピーする
 *
 * @param {string} targetDirectory コピー先ディレクトリ
 * @returns {boolean} コピーしたかどうか
 */
function copyPluginGuideToDirectory(targetDirectory) {
  if (!fs.existsSync(PLUGIN_GUIDE_SOURCE)) {
    console.error(`❌ Error: Plugin guide not found at ${PLUGIN_GUIDE_SOURCE}`);
    process.exit(1);
  }

  const sourceContent = fs.readFileSync(PLUGIN_GUIDE_SOURCE, 'utf8');
  const destinationPath = path.join(targetDirectory, 'CLAUDE.ndf.md');

  // 既存ファイルが同じ内容なら何もしない
  if (fs.existsSync(destinationPath)) {
    const existingContent = fs.readFileSync(destinationPath, 'utf8');
    if (existingContent === sourceContent) {
      console.log('✓ CLAUDE.ndf.md is already up to date');
      return false;
    }
  }

  // コピー実行
  fs.writeFileSync(destinationPath, sourceContent, 'utf8');
  console.log(`✓ Copied plugin guide to ${destinationPath}`);
  return true;
}

// ============================================================
// インポート行を追加する
// ============================================================

/**
 * CLAUDE.md/AGENT.mdにインポート行を追加する
 *
 * @param {string} targetFilePath 対象ファイルのパス
 * @returns {boolean} 追加したかどうか
 */
function addImportLineToFile(targetFilePath) {
  const content = fs.readFileSync(targetFilePath, 'utf8');

  // 既にインポート行があれば何もしない
  if (content.includes(IMPORT_LINE)) {
    console.log(`✓ Import line already exists in ${path.basename(targetFilePath)}`);
    return false;
  }

  // ファイル末尾にインポート行を追加
  const newContent = content.trimEnd() + '\n' + IMPORT_LINE + '\n';
  fs.writeFileSync(targetFilePath, newContent, 'utf8');
  console.log(`✓ Added import line to ${path.basename(targetFilePath)}: ${IMPORT_LINE}`);
  return true;
}

// ============================================================
// メイン処理
// ============================================================

function main() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📋 NDF Plugin: Inject Plugin Guide');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // ステップ1: CLAUDE.md/AGENT.mdの場所を探す
  const claudeMdPath = findClaudeMdLocation();

  if (!claudeMdPath) {
    // CLAUDE.mdが見つからない → CLAUDE.ndf.mdも作成しない
    console.log('⚠ No CLAUDE.md or AGENT.md found in project');
    console.log('  CLAUDE.ndf.md will not be created');
    console.log('  (CLAUDE.ndf.md is only created where CLAUDE.md exists)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    return;
  }

  console.log(`✓ Found CLAUDE.md at: ${claudeMdPath}`);

  // ステップ2: CLAUDE.mdと同じディレクトリにCLAUDE.ndf.mdをコピー
  const targetDirectory = path.dirname(claudeMdPath);
  copyPluginGuideToDirectory(targetDirectory);

  // ステップ3: CLAUDE.mdにインポート行を追加
  addImportLineToFile(claudeMdPath);

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // Claude Codeへの通知
  const hookOutput = {
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: "📝 NDFプラグインガイドがCLAUDE.ndf.mdとしてインポートされました。最新のガイドラインを参照できます。"
    }
  };
  console.log(JSON.stringify(hookOutput));
}

// ============================================================
// 実行
// ============================================================

try {
  main();
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
