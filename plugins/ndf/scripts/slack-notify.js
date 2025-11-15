#!/usr/bin/env node
/**
 * Slack notification script for Claude Code completion
 * Reads transcript_path from stdin (hook input JSON) and generates summary
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { spawn } = require('child_process');

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

// Generate summary using Claude CLI
function generateSummaryWithClaude(transcriptPath) {
  return new Promise((resolve) => {
    if (!fs.existsSync(transcriptPath)) {
      resolve(null);
      return;
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

      // Build conversation context for Claude
      const conversationText = recentMessages
        .map(m => `${m.role === 'user' ? 'ユーザー' : 'アシスタント'}: ${m.text}`)
        .join('\n\n');

      if (!conversationText || conversationText.length < 10) {
        resolve(null);
        return;
      }

      // Create summarization prompt
      const prompt = `以下の会話から実施した作業を40文字以内で要約してください。

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

      // Call claude CLI with -p flag and disable hooks & plugins to prevent infinite loop
      const claude = spawn('claude', ['-p', '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}', '--output-format', 'json'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let output = '';
      let errorOutput = '';

      claude.stdout.on('data', (data) => {
        output += data.toString();
      });

      claude.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      claude.on('close', (code) => {
        if (code === 0 && output.trim()) {
          try {
            // Parse JSON response from Claude CLI
            const response = JSON.parse(output.trim());

            // Claude CLI may return summary in either result or content field
            const summary = (response.result || response.content || '').trim();

            // Validate summary is meaningful (at least 5 chars)
            if (summary.length >= 5) {
              resolve(summary);
            } else {
              resolve(null);
            }
          } catch (e) {
            // If JSON parsing fails, fallback to raw text
            const summary = output.trim().split('\n')[0].trim();
            if (summary.length >= 5) {
              resolve(summary);
            } else {
              resolve(null);
            }
          }
        } else {
          resolve(null);
        }
      });

      claude.on('error', (error) => {
        resolve(null);
      });

      // Send prompt to stdin
      claude.stdin.write(prompt);
      claude.stdin.end();

    } catch (error) {
      resolve(null);
    }
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
            resolve(result);  // Return full result object (includes ts)
          } else {
            resolve(null);
          }
        } catch (e) {
          resolve(null);
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(data);
    req.end();
  });
}

// Delete Slack message
function deleteSlackMessage(channelId, token, messageTs) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      channel: channelId,
      ts: messageTs
    });

    const options = {
      hostname: 'slack.com',
      port: 443,
      path: '/api/chat.delete',
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
            resolve(true);
          } else {
            resolve(false);
          }
        } catch (e) {
          resolve(false);
        }
      });
    });

    req.on('error', (error) => {
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

  // Get configuration from environment
  const channelId = process.env.SLACK_CHANNEL_ID;
  const token = process.env.SLACK_BOT_TOKEN;
  const userMention = process.env.SLACK_USER_MENTION;

  // Exit silently if required variables are not set
  if (!channelId || !token) {
    process.exit(0);
  }

  // Read hook input from stdin
  let hookInput = '';
  if (!process.stdin.isTTY) {
    for await (const chunk of process.stdin) {
      hookInput += chunk;
    }
  }

  // Extract transcript_path from JSON input
  let transcriptPath = null;
  if (hookInput) {
    try {
      const hookData = JSON.parse(hookInput);
      if (hookData.transcript_path) {
        transcriptPath = hookData.transcript_path;
      }
    } catch (e) {
      // Continue silently
    }
  }

  // Step 1: Send message with mention to trigger notification
  const mentionMessage = userMention ? `${userMention} Claude Codeの作業が完了しました` : 'Claude Codeの作業が完了しました';

  let mentionResult;
  try {
    mentionResult = await sendSlackMessage(channelId, token, mentionMessage);
    if (!mentionResult) {
      process.exit(1);
    }
  } catch (error) {
    process.exit(1);
  }

  // Step 2: Generate work summary
  let workSummary = null;

  // Generate summary using Claude CLI
  if (transcriptPath) {
    workSummary = await generateSummaryWithClaude(transcriptPath);
  }

  // Step 3: Delete mention message (right before sending detailed message)
  if (mentionResult && mentionResult.ts) {
    try {
      await deleteSlackMessage(channelId, token, mentionResult.ts);
    } catch (error) {
      // Continue even if deletion fails
    }
  }

  // Step 4: Send detailed message with repository name and work summary
  const repoName = await getRepositoryName();

  // Create detailed message (1 line format)
  let detailedMessage;
  if (workSummary) {
    detailedMessage = `[${repoName}] ${workSummary}`;
  } else {
    detailedMessage = `[${repoName}] Claude Codeのセッションが終了しました(要約なし)`;
  }

  try {
    await sendSlackMessage(channelId, token, detailedMessage);
  } catch (error) {
    // Exit silently even on error
  }

  // Exit silently - Stop hook will continue normally
}

main().catch((error) => {
  // Exit silently even on error
  process.exit(1);
});
