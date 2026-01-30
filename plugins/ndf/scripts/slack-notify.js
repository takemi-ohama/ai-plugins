#!/usr/bin/env node
/**
 * Slack notification script for Claude Code session completion
 *
 * Reads transcript_path from stdin (hook input JSON) and generates
 * a session-specific summary using Claude CLI.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { spawn } = require('child_process');
const os = require('os');
const crypto = require('crypto');

// ============================================================================
// Constants
// ============================================================================

const CONFIG = {
  CLI_TIMEOUT_MS: 60000,
  MAX_RESPONSES: 5,
  MAX_TRANSCRIPT_LINES: 100,
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024, // 10MB
  MIN_TEXT_LENGTH: 5,
  MIN_RESPONSE_LENGTH: 10,
  MAX_CONTENT_LENGTH: 500,
  MAX_CONTEXT_LENGTH: 2500,
  FALLBACK_REPO_NAME: 'unknown',
  NO_SUMMARY_MESSAGE: 'Claude Codeのセッションが終了しました(要約なし)',
  LOCK_TIMEOUT_MS: 30000, // Lock expires after 30 seconds
  NOTIFICATION_COOLDOWN_MS: 5000, // Prevent duplicate notifications within 5 seconds
  DELETE_DELAY_MS: 500 // Wait before deleting mention message
};

const META_CONTENT_PREFIXES = ['Caveat:', '<local-command', '<command-name>'];

// ============================================================================
// Utilities
// ============================================================================

const isDebugMode = () => process.env.DEBUG_SLACK_NOTIFY === 'true';

const debugLog = (message, ...args) => {
  if (isDebugMode()) {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] ${message}`, ...args);
  }
};

const safeJsonParse = (str) => {
  try {
    return JSON.parse(str);
  } catch (e) {
    debugLog('JSON parse error:', e.message, 'Input:', str?.substring(0, 100));
    return null;
  }
};

const readFileLines = (filePath) => {
  if (!fs.existsSync(filePath)) {
    debugLog('File does not exist:', filePath);
    return null;
  }
  try {
    const stats = fs.statSync(filePath);
    if (stats.size > CONFIG.MAX_FILE_SIZE_BYTES) {
      debugLog('Transcript file too large:', stats.size, 'bytes');
      return null;
    }
    const content = fs.readFileSync(filePath, 'utf8').trim();
    const lines = content.split('\n');
    debugLog('Read', lines.length, 'lines from transcript');
    return lines;
  } catch (error) {
    debugLog('Error reading transcript file:', error.message);
    return null;
  }
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// ============================================================================
// Lock Management (prevent duplicate execution)
// ============================================================================

function getLockFilePath() {
  // Use working directory hash instead of session ID for robust deduplication
  // This prevents multiple Claude Code instances in the same project from sending duplicate notifications
  const cwd = process.cwd();
  const hash = crypto.createHash('md5').update(cwd).digest('hex').substring(0, 8);
  return path.join(os.tmpdir(), `slack-notify-${hash}.lock`);
}

function acquireLock() {
  const lockFile = getLockFilePath();
  const now = Date.now();

  try {
    // Check if lock exists
    if (fs.existsSync(lockFile)) {
      const lockData = safeJsonParse(fs.readFileSync(lockFile, 'utf8'));
      if (lockData) {
        // Check if notification was sent recently (cooldown period)
        if (lockData.completedAt && (now - lockData.completedAt) < CONFIG.NOTIFICATION_COOLDOWN_MS) {
          debugLog('Notification sent recently at:', lockData.completedAt, '| Cooldown active');
          return false;
        }
        // Check if another process is still holding the lock
        if (!lockData.completedAt && (now - lockData.timestamp) < CONFIG.LOCK_TIMEOUT_MS) {
          debugLog('Lock already held by PID:', lockData.pid, 'acquired at:', lockData.timestamp);
          return false;
        }
      }
      debugLog('Lock expired or cooldown ended, proceeding');
    }

    // Create lock
    fs.writeFileSync(lockFile, JSON.stringify({
      pid: process.pid,
      timestamp: now,
      completedAt: null
    }));
    debugLog('Lock acquired by PID:', process.pid);
    return true;
  } catch (error) {
    debugLog('Lock acquisition error:', error.message);
    return false;
  }
}

function releaseLock() {
  const lockFile = getLockFilePath();
  try {
    if (fs.existsSync(lockFile)) {
      // Update lock with completion time instead of deleting
      // This enables cooldown period to prevent duplicate notifications
      const lockData = safeJsonParse(fs.readFileSync(lockFile, 'utf8')) || {};
      lockData.completedAt = Date.now();
      fs.writeFileSync(lockFile, JSON.stringify(lockData));
      debugLog('Lock released with completion timestamp:', lockData.completedAt);
    }
  } catch (error) {
    debugLog('Lock release error:', error.message);
  }
}

// ============================================================================
// Environment Management
// ============================================================================

function loadEnvFile() {
  let currentDir = __dirname;

  while (currentDir !== path.dirname(currentDir)) {
    currentDir = path.dirname(currentDir);
    const envFile = path.join(currentDir, '.env');

    if (fs.existsSync(envFile)) {
      debugLog('Loading env file:', envFile);
      parseEnvFile(envFile);
      break;
    }
    if (fs.existsSync(path.join(currentDir, '.git'))) break;
  }
}

function parseEnvFile(envFile) {
  const content = fs.readFileSync(envFile, 'utf8');

  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;

    const match = line.match(/^([^=]+)=(.*)$/);
    if (!match) continue;

    const key = match[1].trim();
    let value = match[2].trim();

    // Remove surrounding quotes
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    process.env[key] ??= value;
  }
}

// ============================================================================
// Transcript Processing
// ============================================================================

function isMetaContent(content) {
  return typeof content === 'string' &&
    META_CONTENT_PREFIXES.some(prefix => content.startsWith(prefix));
}

function extractTextFromContent(content) {
  if (typeof content === 'string') {
    return isMetaContent(content) ? null : content.substring(0, CONFIG.MAX_CONTENT_LENGTH);
  }

  if (Array.isArray(content)) {
    const textItem = content.find(item =>
      item?.type === 'text' && typeof item.text === 'string'
    );
    return textItem?.text?.substring(0, CONFIG.MAX_CONTENT_LENGTH) ?? null;
  }

  return null;
}

function parseTranscriptData(transcriptPath) {
  debugLog('Parsing transcript:', transcriptPath);
  const allLines = readFileLines(transcriptPath);
  if (!allLines) {
    debugLog('No lines read from transcript');
    return { firstRequest: null, assistantResponses: [] };
  }

  // Process only recent lines to avoid memory issues with large files
  const lines = allLines.slice(-CONFIG.MAX_TRANSCRIPT_LINES);
  debugLog('Processing', lines.length, 'recent lines');

  let firstRequest = null;
  const assistantResponses = [];
  let parsedCount = 0;
  let userCount = 0;
  let assistantCount = 0;

  for (const line of lines) {
    const data = safeJsonParse(line);
    if (!data?.message?.role) continue;
    parsedCount++;

    const { role, content } = data.message;
    const text = extractTextFromContent(content);

    // Get first valid user request (within recent lines)
    if (!firstRequest &&
        role === 'user' &&
        data.type === 'user' &&
        !data.isMeta &&
        text?.length >= CONFIG.MIN_TEXT_LENGTH) {
      firstRequest = text;
      userCount++;
      debugLog('Found user request:', text.substring(0, 50) + '...');
    }

    // Collect assistant responses
    if (role === 'assistant' && text?.length >= CONFIG.MIN_RESPONSE_LENGTH) {
      assistantResponses.push(text);
      assistantCount++;
    }
  }

  debugLog('Parsed messages:', parsedCount, '| User:', userCount, '| Assistant:', assistantCount);

  return {
    firstRequest,
    assistantResponses: assistantResponses.slice(-CONFIG.MAX_RESPONSES)
  };
}

function formatContextForSummary({ firstRequest, assistantResponses }) {
  if (!firstRequest && assistantResponses.length === 0) {
    debugLog('No content for summary context');
    return null;
  }

  const parts = [];
  if (firstRequest) {
    parts.push(`【ユーザーのリクエスト】\n${firstRequest}`);
  }
  if (assistantResponses.length > 0) {
    parts.push(`【アシスタントの応答】\n${assistantResponses.join('\n\n')}`);
  }

  const context = parts.join('\n\n');
  debugLog('Context length:', context.length);
  return context.length >= CONFIG.MIN_RESPONSE_LENGTH ? context : null;
}

function createSummarizationPrompt(context) {
  return `以下の情報から、**このセッションで実施した作業**を日本語で40文字以内で要約してください。

## 重要
- ユーザーのリクエストとアシスタントの応答から、このセッション固有の作業内容を特定してください
- 「調査」「確認」などの一般的な表現より、具体的な作業内容（例：「Slack通知の要約生成を修正」）を優先してください

## 出力形式
日本語の要約文のみ（1行、40文字以内）

## 必須事項
- 必ず日本語で出力すること
- このセッションで実際に行った具体的な作業を要約すること
- 技術的な作業内容を含めること（ファイル名、機能名など）

## 禁止事項
- 英語での出力
- 「ユーザーさん」「調査結果」などの前置き
- 「要約：」「作業内容：」などのラベル
- 「〜を確認しました」「〜を調査しました」などの曖昧な表現（具体的な結果を書く）
- 挨拶文や説明文
- 複数行の出力

## 良い例
- Slack通知の要約生成ロジックを修正
- BigQueryクエリのパフォーマンスを最適化
- JWT認証のセキュリティレビューを実施
- PRマージ後のブランチクリーンアップを実行

## 悪い例
- Added new MCP server（英語は禁止）
- コードを調査しました（曖昧すぎる）
- ユーザーさん、調査結果をまとめます：
- 要約：〜を実施しました

## セッション情報
${context.substring(0, CONFIG.MAX_CONTEXT_LENGTH)}

## 日本語の要約（40文字以内）:`;
}

// ============================================================================
// Claude CLI Integration (with MCP tools disabled)
// ============================================================================

function callClaudeCLI(prompt) {
  return new Promise((resolve) => {
    debugLog('Calling Claude CLI...');

    const args = [
      '--print',
      '--no-session-persistence',
      '--strict-mcp-config',
      '--mcp-config', '{"mcpServers":{}}',
      '--tools', '',
      '--model', 'haiku',
      '-p', prompt
    ];

    debugLog('CLI args:', args.join(' '));

    const claude = spawn('claude', args, {
      stdio: ['ignore', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';
    let resolved = false;

    const safeResolve = (value, reason) => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timeoutId);
        debugLog('CLI resolved:', reason, '| Output length:', value?.length || 0);
        resolve(value);
      }
    };

    claude.stdout.on('data', (data) => { stdout += data; });
    claude.stderr.on('data', (data) => { stderr += data; });

    const timeoutId = setTimeout(() => {
      debugLog('Claude CLI timeout after', CONFIG.CLI_TIMEOUT_MS, 'ms');
      claude.kill('SIGTERM');
      safeResolve(null, 'timeout');
    }, CONFIG.CLI_TIMEOUT_MS);

    claude.on('close', (code, signal) => {
      if (signal) {
        debugLog('Claude CLI killed by signal:', signal);
        safeResolve(null, 'signal:' + signal);
        return;
      }

      debugLog('Claude CLI exit code:', code);
      debugLog('CLI stdout:', stdout.substring(0, 200));
      debugLog('CLI stderr:', stderr.substring(0, 200));

      if (code === 0 && stdout.trim()) {
        safeResolve(stdout.trim(), 'success');
      } else {
        debugLog('Claude CLI error - code:', code, '| stderr:', stderr || 'none');
        safeResolve(null, 'error:' + code);
      }
    });

    claude.on('error', (err) => {
      debugLog('Claude CLI spawn error:', err.message);
      safeResolve(null, 'spawn-error');
    });
  });
}

function cleanSummaryResponse(summary) {
  if (!summary) {
    debugLog('No summary to clean');
    return null;
  }

  debugLog('Raw summary:', summary);

  const cleaned = summary
    .replace(/^(要約[:：]?\s*|作業内容[:：]?\s*)/i, '')
    .replace(/^[\s\n]+/, '')
    .split('\n')[0]
    .trim();

  debugLog('Cleaned summary:', cleaned);
  return cleaned.length >= CONFIG.MIN_TEXT_LENGTH ? cleaned : null;
}

async function generateSummary(transcriptPath) {
  debugLog('=== Starting summary generation ===');

  const transcriptData = parseTranscriptData(transcriptPath);
  debugLog('Transcript data:', {
    hasFirstRequest: !!transcriptData.firstRequest,
    responseCount: transcriptData.assistantResponses.length
  });

  const context = formatContextForSummary(transcriptData);
  if (!context) {
    debugLog('No context available for summary');
    return null;
  }

  const prompt = createSummarizationPrompt(context);
  debugLog('Prompt length:', prompt.length);

  const output = await callClaudeCLI(prompt);
  const result = cleanSummaryResponse(output);

  debugLog('=== Summary generation complete:', result ? 'SUCCESS' : 'FAILED', '===');
  return result;
}

// ============================================================================
// Slack API Integration
// ============================================================================

function makeSlackApiRequest(apiPath, data, token) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(data);
    debugLog('Slack API request:', apiPath, '| Payload size:', payload.length);

    const req = https.request({
      hostname: 'slack.com',
      port: 443,
      path: apiPath,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => {
        const result = safeJsonParse(body);
        debugLog('Slack API response:', apiPath, '| ok:', result?.ok, '| error:', result?.error || 'none');
        if (result?.ok) {
          resolve(result);
        } else {
          debugLog('Slack API error details:', result);
          resolve(null);
        }
      });
    });

    req.on('error', (error) => {
      debugLog('Slack API network error:', error.message);
      reject(error);
    });
    req.write(payload);
    req.end();
  });
}

const sendSlackMessage = (channelId, token, text) =>
  makeSlackApiRequest('/api/chat.postMessage', { channel: channelId, text }, token);

const deleteSlackMessage = (channelId, token, ts) =>
  makeSlackApiRequest('/api/chat.delete', { channel: channelId, ts }, token);

// ============================================================================
// Git Integration
// ============================================================================

function getRepositoryName() {
  return new Promise((resolve) => {
    const git = spawn('git', ['rev-parse', '--show-toplevel']);
    let output = '';

    git.stdout.on('data', (data) => { output += data; });
    git.on('close', (code) => {
      const repoName = code === 0 && output.trim()
        ? path.basename(output.trim())
        : process.env.GIT_REPO || CONFIG.FALLBACK_REPO_NAME;
      debugLog('Repository name:', repoName);
      resolve(repoName);
    });
    git.on('error', () => resolve(process.env.GIT_REPO || CONFIG.FALLBACK_REPO_NAME));
  });
}

// ============================================================================
// Hook Input Processing
// ============================================================================

async function readHookInput() {
  if (process.stdin.isTTY) {
    debugLog('stdin is TTY, no hook input');
    return { transcriptPath: null, stopHookActive: false };
  }

  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  debugLog('Raw hook input:', input.substring(0, 200));
  const parsed = safeJsonParse(input);
  debugLog('Parsed hook input keys:', parsed ? Object.keys(parsed) : 'null');

  return {
    transcriptPath: parsed?.transcript_path ?? null,
    stopHookActive: parsed?.stop_hook_active === true
  };
}

// ============================================================================
// Message Formatting
// ============================================================================

function formatNotificationMessage(repoName, summary, includeMention = false) {
  const userMention = process.env.SLACK_USER_MENTION;
  const content = summary || CONFIG.NO_SUMMARY_MESSAGE;
  const message = `[${repoName}] ${content}`;

  return includeMention && userMention ? `${userMention} ${message}` : message;
}

// ============================================================================
// Main Flow
// ============================================================================

async function main() {
  debugLog('=== Slack notify script started ===');
  debugLog('PID:', process.pid);
  debugLog('CLAUDE_SESSION_ID:', process.env.CLAUDE_SESSION_ID || 'not set');

  loadEnvFile();

  const { SLACK_CHANNEL_ID: channelId, SLACK_BOT_TOKEN: token } = process.env;
  if (!channelId || !token) {
    debugLog('Missing required env vars - SLACK_CHANNEL_ID:', !!channelId, '| SLACK_BOT_TOKEN:', !!token);
    process.exit(0);
  }

  // Prevent duplicate execution
  if (!acquireLock()) {
    debugLog('Could not acquire lock, another instance may be running. Exiting.');
    process.exit(0);
  }

  try {
    const [hookInput, repoName] = await Promise.all([
      readHookInput(),
      getRepositoryName()
    ]);

    const { transcriptPath, stopHookActive } = hookInput;

    // Skip if this is a recursive hook call (e.g., from internal Claude CLI for summary generation)
    if (stopHookActive) {
      debugLog('stop_hook_active is true, skipping to prevent recursive execution');
      releaseLock();
      process.exit(0);
    }

    debugLog('Transcript path:', transcriptPath);
    debugLog('Repository name:', repoName);

    const summary = transcriptPath ? await generateSummary(transcriptPath) : null;
    debugLog('Final summary:', summary);

    // Send message with mention to trigger notification
    const mentionMessage = formatNotificationMessage(repoName, summary, true);
    debugLog('Sending mention message:', mentionMessage.substring(0, 100));
    const mentionResult = await sendSlackMessage(channelId, token, mentionMessage);
    if (!mentionResult) {
      debugLog('Failed to send mention message');
      process.exit(1);
    }
    debugLog('Mention message sent, ts:', mentionResult.ts);

    // Wait a bit before sending clean message and deleting
    await sleep(CONFIG.DELETE_DELAY_MS);

    // Send clean message without mention
    const cleanMessage = formatNotificationMessage(repoName, summary, false);
    debugLog('Sending clean message:', cleanMessage.substring(0, 100));
    const cleanResult = await sendSlackMessage(channelId, token, cleanMessage);
    if (!cleanResult) {
      debugLog('Failed to send clean message');
    } else {
      debugLog('Clean message sent, ts:', cleanResult.ts);
    }

    // Delete the mention message
    if (mentionResult.ts) {
      debugLog('Deleting mention message, ts:', mentionResult.ts);
      const deleteResult = await deleteSlackMessage(channelId, token, mentionResult.ts);
      if (deleteResult) {
        debugLog('Mention message deleted successfully');
      } else {
        debugLog('Failed to delete mention message');
      }
    }

    debugLog('=== Slack notify script completed successfully ===');
  } finally {
    releaseLock();
  }
}

main().catch((error) => {
  debugLog('Fatal error:', error.message, error.stack);
  releaseLock();
  process.exit(1);
});
