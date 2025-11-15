#!/usr/bin/env node
/**
 * Slack notification script for Claude Code completion
 * Reads transcript_path from stdin (hook input JSON) and generates summary
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { spawn } = require('child_process');

// Setup logging
const logDir = path.join(process.env.HOME || '/tmp', '.claude', 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}
const logFile = path.join(logDir, 'slack-notify-debug.log');

function logDebug(message) {
  const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
  fs.appendFileSync(logFile, `[${timestamp}] ${message}\n`);
}

logDebug('=== Slack notification script started (Node.js) ===');
logDebug(`Script invoked with args: ${process.argv.slice(2).join(' ')}`);
logDebug(`Working directory: ${process.cwd()}`);

// Load .env file from project root
function loadEnvFile() {
  let currentDir = __dirname;

  while (currentDir !== path.dirname(currentDir)) {
    currentDir = path.dirname(currentDir);
    const envFile = path.join(currentDir, '.env');

    if (fs.existsSync(envFile)) {
      const content = fs.readFileSync(envFile, 'utf8');
      content.split('\n').forEach(line => {
        line = line.trim();
        // Skip empty lines and comments
        if (!line || line.startsWith('#')) return;

        const match = line.match(/^([^=]+)=(.*)$/);
        if (match) {
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
        }
      });
      break;
    }

    // Stop at git repository root
    if (fs.existsSync(path.join(currentDir, '.git'))) {
      break;
    }
  }
}

// Extract text from content (string or array format)
function extractTextFromContent(content) {
  if (typeof content === 'string') {
    return content;
  } else if (Array.isArray(content)) {
    // Extract text from array format: [{"type": "text", "text": "..."}]
    for (const item of content) {
      if (item && typeof item === 'object' && item.type === 'text' && item.text) {
        return item.text;
      }
    }
  }
  return null;
}

// Generate summary from transcript file
function generateSummaryFromTranscript(transcriptPath) {
  if (!fs.existsSync(transcriptPath)) {
    logDebug(`Transcript file not found: ${transcriptPath}`);
    return null;
  }

  try {
    // Read last 30 lines of JSONL file
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const allLines = content.trim().split('\n');
    const lines = allLines.slice(-30);

    // Extract user and assistant messages
    const messages = [];
    for (const line of lines) {
      try {
        const data = JSON.parse(line);
        if (data.message && data.message.role) {
          const role = data.message.role;
          if (role === 'user' || role === 'assistant') {
            const text = extractTextFromContent(data.message.content);
            if (text) {
              messages.push({ role, text });
            }
          }
        }
      } catch (e) {
        // Skip invalid JSON lines
      }
    }

    // Get last 10 messages
    const recentMessages = messages.slice(-10);
    logDebug(`Extracted ${recentMessages.length} recent messages`);

    // Extract last user request
    const userMessages = recentMessages.filter(m => m.role === 'user').map(m => m.text);
    const assistantMessages = recentMessages.filter(m => m.role === 'assistant').map(m => m.text);

    let summary = null;

    if (userMessages.length > 0) {
      let userRequest = userMessages[userMessages.length - 1];
      logDebug(`Last user message (raw): ${userRequest.substring(0, 100)}`);

      // Remove noise patterns
      userRequest = userRequest
        .replace(/^\/[^\s]*\s*/, '')           // Command prefixes
        .replace(/^[Hh]ooks*\s*/, '')          // "hooks"
        .replace(/^[Ee]xit code.*/i, '')       // "Exit code"
        .replace(/^error:.*/i, '')             // "error:"
        .replace(/^already.*/i, '')            // "already"
        .trim();

      logDebug(`After noise removal: ${userRequest.substring(0, 100)}`);

      // Truncate to 40 chars
      summary = userRequest.substring(0, 40);
    }

    // Fallback to assistant message
    if (!summary || summary.length < 5) {
      if (assistantMessages.length > 0) {
        summary = assistantMessages[assistantMessages.length - 1].substring(0, 40);
      }
    }

    logDebug(`Generated summary: ${summary || 'empty'}`);
    return summary && summary.length >= 5 ? summary : null;

  } catch (error) {
    logDebug(`Error parsing transcript: ${error.message}`);
    return null;
  }
}

// Generate summary from git diff as fallback
function generateSummaryFromGit() {
  return new Promise((resolve) => {
    // Check if in git repository
    const gitCheck = spawn('git', ['rev-parse', '--git-dir']);

    gitCheck.on('close', (code) => {
      if (code !== 0) {
        resolve(null);
        return;
      }

      // Get changed files
      const gitDiff = spawn('git', ['diff', '--name-only']);
      let output = '';

      gitDiff.stdout.on('data', (data) => {
        output += data.toString();
      });

      gitDiff.on('close', (code) => {
        if (code === 0 && output.trim()) {
          const files = output.trim().split('\n');
          const count = files.length;
          const mainFile = path.basename(files[0]);

          if (count === 1) {
            resolve(`${mainFile}を更新`);
          } else {
            resolve(`${mainFile}等${count}件を更新`);
          }
        } else {
          resolve(null);
        }
      });

      gitDiff.on('error', () => resolve(null));
    });

    gitCheck.on('error', () => resolve(null));
  });
}

// Send message to Slack
function sendSlackMessage(channelId, token, text) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      channel: channelId,
      text: text
    });

    const options = {
      hostname: 'slack.com',
      port: 443,
      path: '/api/chat.postMessage',
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': Buffer.byteLength(data)
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
          if (result.ok) {
            logDebug('Slack message sent successfully');
            resolve(true);
          } else {
            logDebug(`Slack API error: ${JSON.stringify(result)}`);
            resolve(false);
          }
        } catch (e) {
          logDebug(`Failed to parse Slack response: ${e.message}`);
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
      logDebug(`Failed to send Slack message: ${error.message}`);
      reject(error);
    });

    req.write(data);
    req.end();
  });
}

// Get repository name
function getRepositoryName() {
  return new Promise((resolve) => {
    const gitShow = spawn('git', ['rev-parse', '--show-toplevel']);
    let output = '';

    gitShow.stdout.on('data', (data) => {
      output += data.toString();
    });

    gitShow.on('close', (code) => {
      if (code === 0 && output.trim()) {
        const repoPath = output.trim();
        resolve(path.basename(repoPath));
      } else {
        resolve(process.env.GIT_REPO || 'unknown');
      }
    });

    gitShow.on('error', () => resolve(process.env.GIT_REPO || 'unknown'));
  });
}

// Main function
async function main() {
  // Load environment variables
  loadEnvFile();
  logDebug('Environment variables loaded');

  // Get configuration from environment
  const channelId = process.env.SLACK_CHANNEL_ID;
  const token = process.env.SLACK_BOT_TOKEN;
  const userMention = process.env.SLACK_USER_MENTION;

  logDebug(`SLACK_BOT_TOKEN set: ${token ? 'yes' : 'no'}`);
  logDebug(`SLACK_CHANNEL_ID: ${channelId || 'not set'}`);
  logDebug(`SLACK_USER_MENTION: ${userMention || 'not set'}`);

  // Exit silently if required variables are not set
  if (!channelId || !token) {
    logDebug('Required environment variables not set. Exiting.');
    process.exit(0);
  }

  // Read hook input from stdin
  let hookInput = '';
  if (!process.stdin.isTTY) {
    for await (const chunk of process.stdin) {
      hookInput += chunk;
    }
    logDebug(`Hook input received from stdin (length: ${hookInput.length} chars)`);
    logDebug(`Hook input preview: ${hookInput.substring(0, 200)}`);
  } else {
    logDebug('No stdin available (terminal)');
  }

  // Extract transcript_path from JSON input
  let transcriptPath = null;
  if (hookInput) {
    try {
      const hookData = JSON.parse(hookInput);
      if (hookData.transcript_path) {
        transcriptPath = hookData.transcript_path;
        logDebug(`Extracted transcript_path: ${transcriptPath}`);
      }
    } catch (e) {
      logDebug(`Failed to parse hook input JSON: ${e.message}`);
    }
  }

  // Get message type from arguments
  const messageType = process.argv[2] || 'session_end';

  // Create base message
  let message;
  if (messageType === 'error') {
    message = 'Claude Codeでエラーが発生しました';
  } else if (messageType === 'session_end') {
    message = 'Claude Codeのセッションが終了しました';
  } else {
    message = 'Claude Codeの作業が完了しました';
  }

  // Step 1: Send message with mention to trigger notification
  const mentionMessage = userMention ? `${userMention} ${message}` : message;

  try {
    await sendSlackMessage(channelId, token, mentionMessage);
  } catch (error) {
    logDebug('Failed to send initial message');
    process.exit(1);
  }

  // Step 2: Generate work summary
  let workSummary = null;

  // Priority 1: Generate from transcript
  if (transcriptPath) {
    logDebug('Attempting to generate summary from transcript');
    workSummary = generateSummaryFromTranscript(transcriptPath);
    logDebug(`Transcript summary: ${workSummary || 'empty'}`);
  }

  // Priority 2: Fallback to git diff
  if (!workSummary) {
    logDebug('Generating summary from git diff');
    workSummary = await generateSummaryFromGit();
    logDebug(`Git diff summary: ${workSummary || 'empty'}`);
  }

  // Truncate to 40 chars
  if (workSummary) {
    workSummary = workSummary.substring(0, 40);
  }

  logDebug(`Final work summary: ${workSummary || 'empty'}`);

  // Step 3: Send detailed message with repository name and work summary
  const repoName = await getRepositoryName();

  // Create detailed message with line break
  let detailedMessage;
  if (workSummary) {
    detailedMessage = `[${repoName}] ${message}\n作業内容: ${workSummary}`;
  } else {
    detailedMessage = `[${repoName}] ${message}`;
  }

  logDebug('Sending final Slack message');
  logDebug(`Repository: ${repoName}`);
  logDebug(`Message: ${message}`);
  logDebug(`Work summary: ${workSummary || 'none'}`);

  try {
    await sendSlackMessage(channelId, token, detailedMessage);
    logDebug('Slack notification sent successfully');
  } catch (error) {
    logDebug('Slack notification failed');
  }

  logDebug('=== Slack notification script completed ===');
}

main().catch((error) => {
  logDebug(`Unhandled error: ${error.message}`);
  process.exit(1);
});
