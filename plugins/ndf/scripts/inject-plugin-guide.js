#!/usr/bin/env node

/**
 * SessionStart Hook: Copy NDF Plugin Guide and add @import to CLAUDE.md
 *
 * This script:
 * 1. Copies CLAUDE.ndf.md to project root as CLAUDE.ndf.md
 * 2. Adds @CLAUDE.ndf.md import line to CLAUDE.md or AGENT.md
 */

const fs = require('fs');
const path = require('path');

// Get current working directory (project root)
const projectRoot = process.cwd();
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;

if (!pluginRoot) {
  console.error('Error: CLAUDE_PLUGIN_ROOT environment variable not set');
  process.exit(1);
}

// Paths
const pluginGuidePath = path.join(pluginRoot, 'CLAUDE.ndf.md');
const targetGuidePath = path.join(projectRoot, 'CLAUDE.ndf.md');

// Find target file (CLAUDE.md or AGENT.md)
function findTargetFile() {
  // Priority 1: Root CLAUDE.md
  const rootClaude = path.join(projectRoot, 'CLAUDE.md');
  if (fs.existsSync(rootClaude)) return rootClaude;

  // Priority 2: Root AGENT.md
  const rootAgent = path.join(projectRoot, 'AGENT.md');
  if (fs.existsSync(rootAgent)) return rootAgent;

  // Priority 3: .claude/CLAUDE.md
  const claudeDirClaude = path.join(projectRoot, '.claude', 'CLAUDE.md');
  if (fs.existsSync(claudeDirClaude)) return claudeDirClaude;

  // Priority 4: .claude/AGENT.md
  const claudeDirAgent = path.join(projectRoot, '.claude', 'AGENT.md');
  if (fs.existsSync(claudeDirAgent)) return claudeDirAgent;

  return null;
}

// Get import line based on target file location
function getImportLine(targetFile) {
  const targetDir = path.dirname(targetFile);
  const relativePath = path.relative(targetDir, targetGuidePath);
  // Convert to forward slashes for consistency
  const normalizedPath = relativePath.split(path.sep).join('/');
  return `@${normalizedPath}`;
}

// Main function
function main() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📋 NDF Plugin: Inject Plugin Guide');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // Step 1: Copy plugin guide to project root
  if (!fs.existsSync(pluginGuidePath)) {
    console.error(`❌ Error: Plugin guide not found at ${pluginGuidePath}`);
    process.exit(1);
  }

  const pluginGuideContent = fs.readFileSync(pluginGuidePath, 'utf8');

  // Check if CLAUDE.ndf.md needs update
  let shouldCopy = true;
  if (fs.existsSync(targetGuidePath)) {
    const existingContent = fs.readFileSync(targetGuidePath, 'utf8');
    if (existingContent === pluginGuideContent) {
      console.log('✓ CLAUDE.ndf.md is already up to date');
      shouldCopy = false;
    }
  }

  if (shouldCopy) {
    fs.writeFileSync(targetGuidePath, pluginGuideContent, 'utf8');
    console.log(`✓ Copied plugin guide to ${targetGuidePath}`);
  }

  // Step 2: Add @import line to CLAUDE.md or AGENT.md
  const targetFile = findTargetFile();

  if (!targetFile) {
    console.log('⚠ No CLAUDE.md or AGENT.md found in project');
    console.log('  Plugin guide is available at CLAUDE.ndf.md');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    return;
  }

  let targetContent = fs.readFileSync(targetFile, 'utf8');

  // Get correct import line for target file location
  const importLine = getImportLine(targetFile);

  // Check if import line already exists
  if (targetContent.includes(importLine)) {
    console.log(`✓ Import line already exists in ${path.basename(targetFile)}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    return;
  }

  // Add import line at the end
  const newContent = targetContent.trimEnd() + '\n' + importLine + '\n';
  fs.writeFileSync(targetFile, newContent, 'utf8');
  console.log(`✓ Added import line to ${path.basename(targetFile)}: ${importLine}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // Notify Claude Code
  const hookOutput = {
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: "📝 NDFプラグインガイドがCLAUDE.ndf.mdとしてインポートされました。最新のガイドラインを参照できます。"
    }
  };
  console.log(JSON.stringify(hookOutput));
}

// Run
try {
  main();
} catch (error) {
  console.error('❌ Error:', error.message);
  process.exit(1);
}
