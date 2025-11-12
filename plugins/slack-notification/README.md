# Slack Notification Hook Plugin

Automatic Slack notifications when Claude Code work is completed with repository name and work summary in Japanese.

## Features

- 🔔 **Smart Notifications**: Mention-delete-repost pattern triggers notification sound without cluttering the channel
- 📝 **Japanese Summaries**: Automatically generates work summaries in Japanese from git changes
- 🏷️ **Repository Context**: Includes repository name in notifications
- ⚙️ **Portable Configuration**: Works from any subdirectory in your project

## Installation

### Via Claude Code Plugin System

1. Add the marketplace to your Claude Code settings:

```json
{
  "extraKnownMarketplaces": {
    "ai-agent-marketplace": {
      "source": {
        "source": "github",
        "repo": "takemi-ohama/ai-agent-marketplace"
      }
    }
  }
}
```

2. Restart Claude Code
3. Install the `slack-notification` plugin when prompted

### Manual Installation

1. Copy `.claude/` directory to your project root
2. Set environment variables
3. Restart Claude Code

## Configuration

### Required Environment Variables

```bash
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_CHANNEL_ID="YOUR_CHANNEL_ID"
export SLACK_USER_MENTION="<@YOUR_USER_ID>"  # Optional

### Slack App Setup

1. Create a Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write` (required)
   - `channels:read` (optional)
3. Install app to workspace
4. Add bot to target channel
5. Copy Bot User OAuth Token

## Usage

Once configured, notifications are sent automatically when you exit Claude Code:

```
[repository-name] Claude Codeの作業が完了しました (2025-11-12 00:17:58)
作業内容: slack-notify.shを更新
```

## Testing

```bash
# Test notification from any directory
.claude/slack-notify.sh complete
```

## Notification Flow

1. Claude Code exits → Stop hook triggers
2. Script searches for `.claude` directory upwards
3. Posts with mention → notification sound
4. Deletes message
5. Reposts without mention → clean history

## Files

- `.claude/settings.json`: Hook configuration
- `.claude/slack-notify.sh`: Notification script

## Troubleshooting

### No notification sound
- Verify `SLACK_USER_MENTION` is set
- Check bot has `chat:write` scope

### Script not found
- Ensure `.claude/slack-notify.sh` is executable
- Verify you're in a git repository

## License

MIT
