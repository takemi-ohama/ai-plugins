#!/usr/bin/env node

/**
 * SessionStart Hook: Inject NDF Plugin Guide to project's CLAUDE.md or AGENT.md
 *
 * This script:
 * 1. Finds project's CLAUDE.md or AGENT.md (prioritize root, then .claude/)
 * 2. Checks if latest version is already injected
 * 3. Removes old version if exists
 * 4. Appends latest version to the end of file
 */

const fs = require('fs');
const path = require('path');

// Markers for version management (固定マーカー)
const START_MARKER = '<!-- NDF_PLUGIN_GUIDE_START_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->';
const END_MARKER = '<!-- NDF_PLUGIN_GUIDE_END_8k3jf9s2n4m5p7q1w6e8r0t2y4u6i8o -->';

// Get current working directory (project root)
const projectRoot = process.cwd();
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;

if (!pluginRoot) {
  console.error('Error: CLAUDE_PLUGIN_ROOT environment variable not set');
  process.exit(1);
}

// Path to plugin guide source
const pluginGuidePath = path.join(pluginRoot, 'CLAUDE_plugin.md');

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

// Extract version from content
function extractVersion(content) {
  const versionMatch = content.match(/<!-- VERSION: (\d+) -->/);
  return versionMatch ? parseInt(versionMatch[1], 10) : null;
}

// Read plugin guide
function readPluginGuide() {
  if (!fs.existsSync(pluginGuidePath)) {
    console.error(`Error: Plugin guide not found at ${pluginGuidePath}`);
    process.exit(1);
  }
  return fs.readFileSync(pluginGuidePath, 'utf8');
}

// Remove old version from content
function removeOldVersion(content) {
  const startIdx = content.indexOf(START_MARKER);
  const endIdx = content.indexOf(END_MARKER);

  if (startIdx === -1 || endIdx === -1) {
    return content; // No old version found
  }

  // Remove old version (including markers and trailing newlines)
  const before = content.substring(0, startIdx).trimEnd();
  const after = content.substring(endIdx + END_MARKER.length).trimStart();

  return before + (after ? '\n\n' + after : '');
}

// Main function
function main() {
  // Find target file
  const targetFile = findTargetFile();

  if (!targetFile) {
    console.log('No CLAUDE.md or AGENT.md found in project. Skipping injection.');
    return;
  }

  console.log(`Target file: ${targetFile}`);

  // Read plugin guide
  const pluginGuide = readPluginGuide();
  const pluginVersion = extractVersion(pluginGuide);

  if (!pluginVersion) {
    console.error('Error: Cannot extract version from plugin guide');
    process.exit(1);
  }

  console.log(`Plugin guide version: ${pluginVersion}`);

  // Read target file
  let targetContent = fs.existsSync(targetFile)
    ? fs.readFileSync(targetFile, 'utf8')
    : '';

  // Check if already injected with same version
  const existingVersion = extractVersion(targetContent);
  if (existingVersion === pluginVersion) {
    console.log(`Plugin guide v${pluginVersion} already injected. Skipping.`);
    return;
  }

  // Remove old version if exists
  if (existingVersion) {
    console.log(`Removing old version v${existingVersion}...`);
    targetContent = removeOldVersion(targetContent);
  }

  // Append new version
  console.log(`Injecting plugin guide v${pluginVersion}...`);
  const newContent = targetContent.trimEnd() + '\n\n' + pluginGuide.trim() + '\n';

  // Write back
  fs.writeFileSync(targetFile, newContent, 'utf8');
  console.log(`Successfully injected plugin guide to ${targetFile}`);
}

// Run
try {
  main();
} catch (error) {
  console.error('Error:', error.message);
  process.exit(1);
}
