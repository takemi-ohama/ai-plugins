#!/usr/bin/env node
/**
 * Slack notification script for Claude Code completion
 * Reads transcript_path from stdin (hook input JSON) and generates summary
 *
 * Uses Claude CLI with --no-session-persistence for summarization
 * (inherits Claude Code's authentication settings automatically)
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { spawn } = require('child_process');

// ============================================================================
// Environment Management
// ============================================================================

/**
 * Load .env file from project root by traversing up directory tree
 */
function loadEnvFile() {
  let currentDir = __dirname;

  while (currentDir !== path.dirname(currentDir)) {
    currentDir = path.dirname(currentDir);
    const envFile = path.join(currentDir, '.env');

    if (fs.existsSync(envFile)) {
      parseEnvFile(envFile);
      break;
    }

    // Stop at git repository root
    if (fs.existsSync(path.join(currentDir, '.git'))) break;
  }
}

/**
 * Parse .env file and set environment variables
 */
function parseEnvFile(envFile) {
  const content = fs.readFileSync(envFile, 'utf8');

  content.split('\n').forEach(line => {
    line = line.trim();
    if (!line || line.startsWith('#')) return;

    const match = line.match(/^([^=]+)=(.*)$/);
    if (!match) return;

    const key = match[1].trim();
    let value = match[2].trim();

    // Remove quotes
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    // Only set if not already in environment
    if (!process.env[key]) {
      process.env[key] = value;
    }
  });
}

// ============================================================================
// Transcript Processing
// ============================================================================

/**
 * Extract text from content (string or array format)
 */
function extractTextFromContent(content) {
  if (typeof content === 'string') {
    return content;
  }

  if (Array.isArray(content)) {
    const textItem = content.find(item =>
      item && typeof item === 'object' && item.type === 'text' && item.text
    );
    return textItem?.text || null;
  }

  return null;
}

/**
 * Read latest summary from transcript file
 * Claude Code automatically generates summaries during the session
 */
function readLatestSummary(transcriptPath) {
  if (!fs.existsSync(transcriptPath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const lines = content.trim().split('\n');

    // Search from the end to find the latest summary
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const data = JSON.parse(lines[i]);
        if (data.type === 'summary' && data.summary) {
          return data.summary;
        }
      } catch (e) {
        // Skip invalid JSON lines
      }
    }
    return null;
  } catch (error) {
    return null;
  }
}

/**
 * Read and parse recent messages from transcript
 */
function readTranscriptMessages(transcriptPath, lineCount = 30, messageCount = 10) {
  if (!fs.existsSync(transcriptPath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const allLines = content.trim().split('\n');
    const recentLines = allLines.slice(-lineCount);

    // Extract user and assistant messages
    const messages = [];
    for (const line of recentLines) {
      try {
        const data = JSON.parse(line);
        if (data.message?.role && ['user', 'assistant'].includes(data.message.role)) {
          const text = extractTextFromContent(data.message.content);
          if (text) {
            messages.push({ role: data.message.role, text });
          }
        }
      } catch (e) {
        // Skip invalid JSON lines
      }
    }

    return messages.slice(-messageCount);
  } catch (error) {
    return null;
  }
}

/**
 * Format messages for Claude summarization
 */
function formatConversationForSummary(messages) {
  if (!messages || messages.length === 0) {
    return null;
  }

  const conversationText = messages
    .map(m => `${m.role === 'user' ? 'ユーザー' : 'アシスタント'}: ${m.text}`)
    .join('\n\n');

  return conversationText.length >= 10 ? conversationText : null;
}

/**
 * Create summarization prompt for Claude
 */
function createSummarizationPrompt(conversationText) {
  return `以下の会話から実施した作業を40文字以内で要約してください。

出力形式: 要約文のみ（1行、40文字以内）

禁止事項:
- 「ユーザーさん」「調査結果」などの前置き
- 「要約：」「作業内容：」などのラベル
- 挨拶文や説明文
- 複数行の出力

良い例:
- Claude Code MCPサーバーを追加
- 要約生成プロンプトを改善
- PRマージ後のクリーンアップを実行

悪い例:
- ユーザーさん、調査結果をまとめます：
- 要約：〜を実施しました
- 以下の要約です

会話内容:
${conversationText.substring(0, 2000)}

要約:`;
}

// ============================================================================
// Claude CLI Integration
// ============================================================================

/**
 * Call Claude CLI with --no-session-persistence to generate summary
 * This inherits Claude Code's authentication (API key or Bedrock) automatically
 */
function callClaudeCLI(prompt) {
  return new Promise((resolve) => {
    const args = [
      '--print',
      '--no-session-persistence',
      '--model', 'haiku',
      '--tools', '',  // ツールを無効化（要約生成のみのため）
      prompt
    ];

    const claude = spawn('claude', args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env
    });

    let output = '';
    let errorOutput = '';
    let resolved = false;

    claude.stdout.on('data', (data) => {
      output += data.toString();
    });

    claude.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    claude.on('close', (code) => {
      if (resolved) return;
      resolved = true;

      if (code === 0 && output.trim()) {
        resolve(output.trim());
      } else {
        // Log error output for debugging if available
        if (errorOutput && process.env.DEBUG_SLACK_NOTIFY === 'true') {
          console.error('Claude CLI stderr:', errorOutput);
        }
        resolve(null);
      }
    });

    claude.on('error', (err) => {
      if (resolved) return;
      resolved = true;
      if (process.env.DEBUG_SLACK_NOTIFY === 'true') {
        console.error('Claude CLI error:', err.message);
      }
      resolve(null);
    });

    // Set timeout (30 seconds)
    setTimeout(() => {
      if (resolved) return;
      resolved = true;
      claude.kill();
      if (process.env.DEBUG_SLACK_NOTIFY === 'true') {
        console.error('Claude CLI timeout after 30 seconds');
      }
      resolve(null);
    }, 30000);
  });
}

/**
 * Parse summary response and clean it up
 */
function parseSummaryResponse(summary) {
  if (!summary) return null;

  // Clean up the summary - remove any prefixes/labels
  let cleaned = summary
    .replace(/^(要約[:：]?\s*|作業内容[:：]?\s*)/i, '')
    .replace(/^[\s\n]+/, '')
    .split('\n')[0]
    .trim();

  return cleaned.length >= 5 ? cleaned : null;
}

/**
 * Generate summary - first tries transcript summary, then falls back to Claude CLI
 */
async function generateSummary(transcriptPath) {
  // First, try to get the latest summary from the transcript
  // Claude Code automatically generates these during the session
  const existingSummary = readLatestSummary(transcriptPath);
  if (existingSummary) {
    if (process.env.DEBUG_SLACK_NOTIFY === 'true') {
      console.error('Using existing transcript summary:', existingSummary);
    }
    return existingSummary;
  }

  // Fallback: Generate summary using Claude CLI
  if (process.env.DEBUG_SLACK_NOTIFY === 'true') {
    console.error('No transcript summary found, trying Claude CLI...');
  }

  const messages = readTranscriptMessages(transcriptPath);
  if (!messages) return null;

  const conversationText = formatConversationForSummary(messages);
  if (!conversationText) return null;

  const prompt = createSummarizationPrompt(conversationText);
  const output = await callClaudeCLI(prompt);

  return parseSummaryResponse(output);
}

// ============================================================================
// Slack API Integration
// ============================================================================

/**
 * Make HTTPS request to Slack API
 */
function makeSlackApiRequest(apiPath, data, token) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(data);

    const options = {
      hostname: 'slack.com',
      port: 443,
      path: apiPath,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(payload)
      }
    };

    const req = https.request(options, (res) => {
      let body = '';

      res.on('data', (chunk) => {
        body += chunk;
      });

      res.on('end', () => {
        try {
          const result = JSON.parse(body);
          resolve(result.ok ? result : null);
        } catch (e) {
          resolve(null);
        }
      });
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

/**
 * Send message to Slack
 */
function sendSlackMessage(channelId, token, text) {
  return makeSlackApiRequest('/api/chat.postMessage', {
    channel: channelId,
    text: text
  }, token);
}

/**
 * Delete Slack message
 */
function deleteSlackMessage(channelId, token, messageTs) {
  return makeSlackApiRequest('/api/chat.delete', {
    channel: channelId,
    ts: messageTs
  }, token).then(result => result !== null);
}

// ============================================================================
// Git Integration
// ============================================================================

/**
 * Get repository name from git
 */
function getRepositoryName() {
  return new Promise((resolve) => {
    const gitShow = spawn('git', ['rev-parse', '--show-toplevel']);
    let output = '';

    gitShow.stdout.on('data', (data) => {
      output += data.toString();
    });

    gitShow.on('close', (code) => {
      if (code === 0 && output.trim()) {
        resolve(path.basename(output.trim()));
      } else {
        resolve(process.env.GIT_REPO || 'unknown');
      }
    });

    gitShow.on('error', () => resolve(process.env.GIT_REPO || 'unknown'));
  });
}

// ============================================================================
// Hook Input Processing
// ============================================================================

/**
 * Read and parse hook input from stdin
 */
async function readHookInput() {
  if (process.stdin.isTTY) {
    return null;
  }

  let hookInput = '';
  for await (const chunk of process.stdin) {
    hookInput += chunk;
  }

  try {
    const hookData = JSON.parse(hookInput);
    return hookData.transcript_path || null;
  } catch (e) {
    return null;
  }
}

// ============================================================================
// Main Flow
// ============================================================================

/**
 * Main notification flow
 */
async function main() {
  // Load environment variables
  loadEnvFile();

  // Get configuration from environment
  const channelId = process.env.SLACK_CHANNEL_ID;
  const token = process.env.SLACK_BOT_TOKEN;
  const userMention = process.env.SLACK_USER_MENTION;

  // Exit silently if required variables are not set
  if (!channelId || !token) {
    process.exit(0);
  }

  // Read transcript path from hook input
  const transcriptPath = await readHookInput();

  // Step 1: Generate work summary
  const workSummary = transcriptPath
    ? await generateSummary(transcriptPath)
    : null;

  const repoName = await getRepositoryName();

  // Step 2: Send message with mention and summary to trigger notification
  const mentionMessage = workSummary
    ? (userMention
        ? `${userMention} [${repoName}] ${workSummary}`
        : `[${repoName}] ${workSummary}`)
    : (userMention
        ? `${userMention} [${repoName}] Claude Codeのセッションが終了しました(要約なし)`
        : `[${repoName}] Claude Codeのセッションが終了しました(要約なし)`);

  const mentionResult = await sendSlackMessage(channelId, token, mentionMessage);
  if (!mentionResult) {
    process.exit(1);
  }

  // Step 3: Send message without mention but with summary
  const detailedMessage = workSummary
    ? `[${repoName}] ${workSummary}`
    : `[${repoName}] Claude Codeのセッションが終了しました(要約なし)`;

  try {
    await sendSlackMessage(channelId, token, detailedMessage);
  } catch (error) {
    // Continue even if second message fails
  }

  // Step 4: Delete mention message
  if (mentionResult.ts) {
    try {
      await deleteSlackMessage(channelId, token, mentionResult.ts);
    } catch (error) {
      // Continue even if deletion fails
    }
  }
}

main().catch(() => {
  // Exit silently even on error
  process.exit(1);
});
