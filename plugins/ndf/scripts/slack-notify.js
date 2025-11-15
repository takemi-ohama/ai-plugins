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
      const claude = spawn('claude', ['-p', '--settings', '{"disableAllHooks": true, "disableAllPlugins": true}', '--output-format', 'text'], {
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
          let summary = output.trim();

          // Remove common greeting/filler phrases
          summary = summary
            .replace(/^ユーザーさん、?/i, '')
            .replace(/^調査結果をまとめます：?/i, '')
            .replace(/^以下の要約です：?/i, '')
            .replace(/^要約：?/i, '')
            .replace(/^作業内容：?/i, '')
            .replace(/^実施した作業：?/i, '')
            .trim();

          // Get first line only
          summary = summary.split('\n')[0].trim();

          // Validate summary is meaningful (at least 5 chars)
          if (summary.length >= 5) {
            resolve(summary);
          } else {
            resolve(null);
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

// Generate summary from transcript file (fallback method)
function generateSummaryFromTranscript(transcriptPath) {
  if (!fs.existsSync(transcriptPath)) {
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

    // Extract last user request
    const userMessages = recentMessages.filter(m => m.role === 'user').map(m => m.text);
    const assistantMessages = recentMessages.filter(m => m.role === 'assistant').map(m => m.text);

    let summary = null;

    if (userMessages.length > 0) {
      let userRequest = userMessages[userMessages.length - 1];

      // Remove noise patterns
      userRequest = userRequest
        .replace(/^\/[^\s]*\s*/, '')           // Command prefixes
        .replace(/^[Hh]ooks*\s*/, '')          // "hooks"
        .replace(/^[Ee]xit code.*/i, '')       // "Exit code"
        .replace(/^error:.*/i, '')             // "error:"
        .replace(/^already.*/i, '')            // "already"
        .replace(/^#+\s*/gm, '')               // Markdown headers (##, ###)
        .replace(/\n#+\s*$/g, '')              // Trailing markdown headers
        .trim();

      // Extract only the first meaningful line
      const firstLine = userRequest.split('\n')[0].trim();
      summary = firstLine;
    }

    // Fallback to assistant message
    if (!summary || summary.length < 5) {
      if (assistantMessages.length > 0) {
        const assistantText = assistantMessages[assistantMessages.length - 1];
        const firstLine = assistantText.split('\n')[0].trim();
        summary = firstLine;
      }
    }

    return summary && summary.length >= 5 ? summary : null;

  } catch (error) {
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

  // Priority 1: Generate summary using Claude CLI (highest quality)
  if (transcriptPath) {
    workSummary = await generateSummaryWithClaude(transcriptPath);
  }

  // Priority 2: Fallback to transcript text parsing
  if (!workSummary && transcriptPath) {
    workSummary = generateSummaryFromTranscript(transcriptPath);
  }

  // Priority 3: Fallback to git diff
  if (!workSummary) {
    workSummary = await generateSummaryFromGit();
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

  // Create detailed message with line break
  let detailedMessage;
  if (workSummary) {
    detailedMessage = `[${repoName}] ${message}\n作業内容: ${workSummary}`;
  } else {
    detailedMessage = `[${repoName}] ${message}`;
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
