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

// ============================================================================
// Constants
// ============================================================================

const CONFIG = {
  CLI_TIMEOUT_MS: 30000,
  MAX_RESPONSES: 5,
  MIN_TEXT_LENGTH: 5,
  MIN_RESPONSE_LENGTH: 10,
  MAX_CONTENT_LENGTH: 500,
  MAX_CONTEXT_LENGTH: 2500,
  FALLBACK_REPO_NAME: 'unknown',
  NO_SUMMARY_MESSAGE: 'Claude Codeのセッションが終了しました(要約なし)'
};

const META_CONTENT_PREFIXES = ['Caveat:', '<local-command', '<command-name>'];

// ============================================================================
// Utilities
// ============================================================================

const isDebugMode = () => process.env.DEBUG_SLACK_NOTIFY === 'true';

const debugLog = (message, ...args) => {
  if (isDebugMode()) {
    console.error(message, ...args);
  }
};

const safeJsonParse = (str) => {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
};

const readFileLines = (filePath) => {
  if (!fs.existsSync(filePath)) return null;
  try {
    return fs.readFileSync(filePath, 'utf8').trim().split('\n');
  } catch {
    return null;
  }
};

// ============================================================================
// Environment Management
// ============================================================================

function loadEnvFile() {
  let currentDir = __dirname;

  while (currentDir !== path.dirname(currentDir)) {
    currentDir = path.dirname(currentDir);
    const envFile = path.join(currentDir, '.env');

    if (fs.existsSync(envFile)) {
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
  const lines = readFileLines(transcriptPath);
  if (!lines) return { firstRequest: null, assistantResponses: [] };

  let firstRequest = null;
  const assistantResponses = [];

  for (const line of lines) {
    const data = safeJsonParse(line);
    if (!data?.message?.role) continue;

    const { role, content } = data.message;
    const text = extractTextFromContent(content);

    // Get first valid user request
    if (!firstRequest &&
        role === 'user' &&
        data.type === 'user' &&
        !data.isMeta &&
        text?.length >= CONFIG.MIN_TEXT_LENGTH) {
      firstRequest = text;
    }

    // Collect assistant responses
    if (role === 'assistant' && text?.length >= CONFIG.MIN_RESPONSE_LENGTH) {
      assistantResponses.push(text);
    }
  }

  return {
    firstRequest,
    assistantResponses: assistantResponses.slice(-CONFIG.MAX_RESPONSES)
  };
}

function formatContextForSummary({ firstRequest, assistantResponses }) {
  if (!firstRequest && assistantResponses.length === 0) return null;

  const parts = [];
  if (firstRequest) {
    parts.push(`【ユーザーのリクエスト】\n${firstRequest}`);
  }
  if (assistantResponses.length > 0) {
    parts.push(`【アシスタントの応答】\n${assistantResponses.join('\n\n')}`);
  }

  const context = parts.join('\n\n');
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
// Claude CLI Integration
// ============================================================================

function callClaudeCLI(prompt) {
  return new Promise((resolve) => {
    const claude = spawn('claude', [
      '--print',
      '--no-session-persistence',
      '--model', 'haiku',
      '--tools', '',
      prompt
    ], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env
    });

    let stdout = '';
    let stderr = '';
    let resolved = false;

    const finish = (result) => {
      if (resolved) return;
      resolved = true;
      resolve(result);
    };

    claude.stdout.on('data', (data) => { stdout += data; });
    claude.stderr.on('data', (data) => { stderr += data; });

    claude.on('close', (code) => {
      if (code === 0 && stdout.trim()) {
        finish(stdout.trim());
      } else {
        debugLog('Claude CLI failed:', stderr || `exit code ${code}`);
        finish(null);
      }
    });

    claude.on('error', (err) => {
      debugLog('Claude CLI error:', err.message);
      finish(null);
    });

    setTimeout(() => {
      debugLog('Claude CLI timeout after', CONFIG.CLI_TIMEOUT_MS, 'ms');
      claude.kill();
      finish(null);
    }, CONFIG.CLI_TIMEOUT_MS);
  });
}

function cleanSummaryResponse(summary) {
  if (!summary) return null;

  const cleaned = summary
    .replace(/^(要約[:：]?\s*|作業内容[:：]?\s*)/i, '')
    .replace(/^[\s\n]+/, '')
    .split('\n')[0]
    .trim();

  return cleaned.length >= CONFIG.MIN_TEXT_LENGTH ? cleaned : null;
}

async function generateSummary(transcriptPath) {
  debugLog('Generating summary using Claude CLI...');

  const transcriptData = parseTranscriptData(transcriptPath);
  const context = formatContextForSummary(transcriptData);
  if (!context) return null;

  const prompt = createSummarizationPrompt(context);
  const output = await callClaudeCLI(prompt);

  return cleanSummaryResponse(output);
}

// ============================================================================
// Slack API Integration
// ============================================================================

function makeSlackApiRequest(apiPath, data, token) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(data);

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
        resolve(result?.ok ? result : null);
      });
    });

    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

const sendSlackMessage = (channelId, token, text) =>
  makeSlackApiRequest('/api/chat.postMessage', { channel: channelId, text }, token);

const deleteSlackMessage = (channelId, token, ts) =>
  makeSlackApiRequest('/api/chat.delete', { channel: channelId, ts }, token)
    .then(result => result !== null);

// ============================================================================
// Git Integration
// ============================================================================

function getRepositoryName() {
  return new Promise((resolve) => {
    const git = spawn('git', ['rev-parse', '--show-toplevel']);
    let output = '';

    git.stdout.on('data', (data) => { output += data; });
    git.on('close', (code) => {
      resolve(code === 0 && output.trim()
        ? path.basename(output.trim())
        : process.env.GIT_REPO || CONFIG.FALLBACK_REPO_NAME);
    });
    git.on('error', () => resolve(process.env.GIT_REPO || CONFIG.FALLBACK_REPO_NAME));
  });
}

// ============================================================================
// Hook Input Processing
// ============================================================================

async function readHookInput() {
  if (process.stdin.isTTY) return null;

  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }

  return safeJsonParse(input)?.transcript_path ?? null;
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
  loadEnvFile();

  const { SLACK_CHANNEL_ID: channelId, SLACK_BOT_TOKEN: token } = process.env;
  if (!channelId || !token) {
    process.exit(0);
  }

  const [transcriptPath, repoName] = await Promise.all([
    readHookInput(),
    getRepositoryName()
  ]);

  const summary = transcriptPath ? await generateSummary(transcriptPath) : null;

  // Send message with mention to trigger notification
  const mentionMessage = formatNotificationMessage(repoName, summary, true);
  const mentionResult = await sendSlackMessage(channelId, token, mentionMessage);
  if (!mentionResult) {
    process.exit(1);
  }

  // Send clean message without mention, then delete the mention message
  const cleanMessage = formatNotificationMessage(repoName, summary, false);
  await sendSlackMessage(channelId, token, cleanMessage).catch(() => {});

  if (mentionResult.ts) {
    await deleteSlackMessage(channelId, token, mentionResult.ts).catch(() => {});
  }
}

main().catch(() => process.exit(1));
