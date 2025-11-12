#!/bin/bash

# Slack notification script for Claude Code completion

# Get configuration from environment variables
CHANNEL_ID="${SLACK_CHANNEL_ID}"
USER_MENTION="${SLACK_USER_MENTION}"

# Exit silently if SLACK_CHANNEL_ID is not set
# Exit silently if required environment variables are not set
if [ -z "$CHANNEL_ID" ] || [ -z "$SLACK_BOT_TOKEN" ]; then
  exit 0
fi

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check message type from argument
MESSAGE_TYPE=${1:-"complete"}

# Create message based on type
case "$MESSAGE_TYPE" in
  "error")
    MESSAGE="Claude Codeでエラーが発生しました (${TIMESTAMP})"
    ;;
  "session_end")
    MESSAGE="Claude Codeのセッションが終了しました (${TIMESTAMP})"
    ;;
  *)
    MESSAGE="Claude Codeの作業が完了しました (${TIMESTAMP})"
    ;;
esac

# Step 1: Post message with mention to trigger notification (if USER_MENTION is set)
if [ -n "$USER_MENTION" ]; then
  MENTION_MESSAGE="${USER_MENTION} ${MESSAGE}"
else
  MENTION_MESSAGE="${MESSAGE}"
fi

RESPONSE=$(curl -s -X POST  \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"${CHANNEL_ID}\",
    \"text\": \"${MENTION_MESSAGE}\"
  }")

# Check if the API call was successful
if [ $? -ne 0 ] || echo "$RESPONSE" | grep -q '"ok":false'; then
  exit 1
fi

# Extract timestamp from response
MESSAGE_TS=$(echo $RESPONSE | grep -o '"ts":"[^"]*"' | head -1 | cut -d'"' -f4)

# Step 2: Delete the message with mention
if [ -n "$MESSAGE_TS" ]; then
  curl -s -X POST https://slack.com/api/chat.delete \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"channel\": \"${CHANNEL_ID}\",
      \"ts\": \"${MESSAGE_TS}\"
    }" > /dev/null
fi

# Step 3: Post message without mention with repository name and work summary
# Get repository name from git remote or environment variable
REPO_NAME=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "${GIT_REPO:-unknown}")

# Generate Japanese work summary from git diff
WORK_SUMMARY=""
if git rev-parse --git-dir > /dev/null 2>&1; then
  # Get changed files from last commit
  CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | wc -l)
  MAIN_FILE=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | head -1 | xargs basename 2>/dev/null)

  if [ "$CHANGED_FILES" -gt 0 ] && [ -n "$MAIN_FILE" ]; then
    if [ "$CHANGED_FILES" -eq 1 ]; then
      WORK_SUMMARY="${MAIN_FILE}を更新"
    else
      WORK_SUMMARY="${MAIN_FILE}等${CHANGED_FILES}件のファイルを更新"
    fi
  fi
fi

# Truncate to 40 chars
WORK_SUMMARY=$(echo "$WORK_SUMMARY" | head -c 40)

# Create detailed message
if [ -n "$WORK_SUMMARY" ]; then
  DETAILED_MESSAGE="[${REPO_NAME}] ${MESSAGE}\n作業内容: ${WORK_SUMMARY}"
else
  DETAILED_MESSAGE="[${REPO_NAME}] ${MESSAGE}"
fi

curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"${CHANNEL_ID}\",
    \"text\": \"${DETAILED_MESSAGE}\"
  }"
