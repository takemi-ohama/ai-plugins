---
name: Slack Notification Hook
description: Automatically send Slack notifications when Claude Code work is completed with repository name and work summary in Japanese
---

# Slack Notification Hook

This skill sets up automatic Slack notifications that trigger when you exit Claude Code, providing instant updates about completed work to your team.

## Features

- 🔔 **Smart Notifications**: Mention-delete-repost pattern triggers notification sound without cluttering the channel
- 📝 **Japanese Summaries**: Automatically generates work summaries in Japanese from git changes
- 🏷️ **Repository Context**: Includes repository name in notifications
- ⚙️ **Portable Configuration**: Works from any subdirectory in your project

## When This Skill Is Invoked

This skill activates when you mention:
- Setting up Slack notifications for Claude Code
- Adding work completion alerts
- Integrating Slack with development workflow
- Automating team notifications

## What This Skill Provides

### 1. Stop Hook Configuration

Adds a hook to `.claude/settings.json` that triggers on Claude Code exit:
- Searches for `.claude` directory from current location upwards
- Portable across different project structures
- No hard-coded paths

### 2. Notification Script

`.claude/slack-notify.sh` script that:
- Posts message with user mention (triggers notification)
- Immediately deletes that message
- Reposts without mention (clean history)
- Includes repository name and Japanese work summary

### 3. Environment Configuration

Required environment variables:
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_CHANNEL_ID`: Target channel ID (required)
- `SLACK_USER_MENTION`: User to mention (optional, e.g., `<@U05MS4DBF9V>`)

## Quick Start

### 1. Install the Plugin Files

Copy `.claude/settings.json` and `.claude/slack-notify.sh` to your project's `.claude/` directory.

### 2. Set Environment Variables

Add to your `.env` or shell profile:

```bash
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_CHANNEL_ID="YOUR_CHANNEL_ID"
export SLACK_USER_MENTION="<@YOUR_USER_ID>"  # Optional

### 3. Configure Slack App

1. Create a Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write` (required for posting and deleting messages)
   - `channels:read` (optional, for listing channels)
3. Install app to workspace
4. Add bot to target channel: `/invite @your-bot-name`
5. Copy Bot User OAuth Token to `SLACK_BOT_TOKEN`

### 4. Test the Setup

```bash
# Test from any subdirectory
.claude/slack-notify.sh complete
```

### 5. Restart Claude Code

Restart Claude Code to load the new hook configuration.

## How It Works

### Notification Flow

1. **Claude Code exits** → Stop hook triggers
2. **Script searches** for `.claude` directory upwards from current location
3. **Posts with mention** → `<@USER> Claude Codeの作業が完了しました`
4. **Deletes message** → Removes the mention
5. **Reposts clean** → `[repo-name] Claude Codeの作業が完了しました (timestamp)\n作業内容: [summary]`

### Work Summary Generation

Automatically generates Japanese summaries from git diff:
- Single file: `filename.shを更新`
- Multiple files: `filename.sh等3件のファイルを更新`
- Truncates to 40 characters max

## Notification Message Format

```
[repository-name] Claude Codeの作業が完了しました (2025-11-12 00:17:58)
作業内容: slack-notify.shを更新
```

## Silent Mode

If `SLACK_CHANNEL_ID` is not set, the script exits silently (status 0) without error messages. This allows the hook to work seamlessly in environments where Slack is not configured.

## Files Included

- `.claude/settings.json`: Hook configuration
- `.claude/slack-notify.sh`: Notification script (executable)

## Troubleshooting

### No notification sound
- Verify channel notification settings in Slack
- Check that `SLACK_USER_MENTION` is set correctly
- Ensure bot has `chat:write` scope

### Script not found
- Verify `.claude/slack-notify.sh` exists
- Check file has execute permission: `chmod +x .claude/slack-notify.sh`
- Ensure you're in a git repository

### Message not deleted
- Bot needs `chat:write` scope for deletion
- Check bot token has correct permissions

## Security Notes

- Never commit `SLACK_BOT_TOKEN` to git
- Add `.env` to `.gitignore`
- Use environment variables for sensitive data
- Bot tokens start with `xoxb-`

## Customization

### Change Message Content

Edit the `MESSAGE` variable in `.claude/slack-notify.sh`:

```bash
MESSAGE="Custom message here (${TIMESTAMP})"
```

### Disable User Mention

Unset or leave empty `SLACK_USER_MENTION` environment variable.

### Change Notification Trigger

Modify `.claude/settings.json` to use different hooks:
- `SessionEnd`: Fires on all session endings
- `PostToolUse`: Fires after tool executions
- `Stop`: Fires on normal exit (default)

## Related Documentation

- [Slack API Documentation](https://api.slack.com/docs)
- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [Slack Bot Token Scopes](https://api.slack.com/scopes)
