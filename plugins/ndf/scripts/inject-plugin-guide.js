#!/usr/bin/env node

/**
 * SessionStart Hook: NDFプラグインガイドの配置とインポート
 *
 * 【ユーザースコープ（~/.claude/）】
 * - ~/.claude/にCLAUDE.ndf.mdをコピー
 * - CLAUDE.mdが存在しなければ、インポート行のみを含むCLAUDE.mdを作成
 * - CLAUDE.mdが存在すれば、インポート行を追加
 *
 * 【プロジェクトスコープ（プロジェクトルート）】
 * - CLAUDE.md/AGENT.mdの場所を探す
 * - 見つかった場合、同じディレクトリにCLAUDE.ndf.mdをコピーしてインポート行を追加
 * - 見つからない場合は何もしない
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const PROJECT_ROOT = process.cwd();
const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT;
const GUIDE_SOURCE = path.join(PLUGIN_ROOT, 'CLAUDE.ndf.md');
const IMPORT_LINE = '@CLAUDE.ndf.md';
const USER_CLAUDE_DIR = path.join(os.homedir(), '.claude');

if (!PLUGIN_ROOT) {
  console.error('Error: CLAUDE_PLUGIN_ROOT environment variable not set');
  process.exit(1);
}

function isUserScope() {
  return PLUGIN_ROOT.startsWith(USER_CLAUDE_DIR);
}

function copyGuide(targetDir) {
  if (!fs.existsSync(GUIDE_SOURCE)) {
    throw new Error(`Plugin guide not found at ${GUIDE_SOURCE}`);
  }

  const sourceContent = fs.readFileSync(GUIDE_SOURCE, 'utf8');
  const destPath = path.join(targetDir, 'CLAUDE.ndf.md');
  const exists = fs.existsSync(destPath);

  if (exists) {
    const existingContent = fs.readFileSync(destPath, 'utf8');
    if (existingContent === sourceContent) {
      return false;
    }
  }

  fs.writeFileSync(destPath, sourceContent, 'utf8');
  console.log(`✓ ${exists ? 'Updated' : 'Copied'} plugin guide to ${destPath}`);
  return true;
}

function addImportLine(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');

  if (content.includes(IMPORT_LINE)) {
    return false;
  }

  const newContent = content.trimEnd() + '\n' + IMPORT_LINE + '\n';
  fs.writeFileSync(filePath, newContent, 'utf8');
  console.log(`✓ Added import line to ${path.basename(filePath)}`);
  return true;
}

function createMinimalClaudeMd(filePath) {
  const content = `# Claude Project Instructions

このファイルはNDFプラグインによって自動生成されました。

${IMPORT_LINE}
`;
  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`✓ Created minimal CLAUDE.md at: ${filePath}`);
  return true;
}

function findClaudeMd() {
  const candidates = [
    path.join(PROJECT_ROOT, 'CLAUDE.md'),
    path.join(PROJECT_ROOT, 'AGENT.md'),
    path.join(PROJECT_ROOT, '.claude', 'CLAUDE.md'),
    path.join(PROJECT_ROOT, '.claude', 'AGENT.md')
  ];

  return candidates.find(fs.existsSync) || null;
}

function handleUserScope() {
  const claudeMdPath = path.join(USER_CLAUDE_DIR, 'CLAUDE.md');
  let changed = false;

  changed = copyGuide(USER_CLAUDE_DIR) || changed;

  if (fs.existsSync(claudeMdPath)) {
    changed = addImportLine(claudeMdPath) || changed;
  } else {
    changed = createMinimalClaudeMd(claudeMdPath) || changed;
  }

  return changed;
}

function handleProjectScope() {
  const claudeMdPath = findClaudeMd();

  if (!claudeMdPath) {
    return false;
  }

  let changed = false;
  const targetDir = path.dirname(claudeMdPath);

  changed = copyGuide(targetDir) || changed;
  changed = addImportLine(claudeMdPath) || changed;

  return changed;
}

function main() {
  const changed = isUserScope() ? handleUserScope() : handleProjectScope();

  if (changed) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext: "📝 NDFプラグインガイドがCLAUDE.ndf.mdとしてインポートされました。最新のガイドラインを参照できます。"
      }
    }));
  }
}

try {
  main();
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
