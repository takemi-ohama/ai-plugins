#!/bin/bash

# Slack notification script for Claude Code completion
# Reads transcript_path from stdin (hook input JSON) and generates summary

# Function to load .env file from project root
load_env_file() {
  # Get the directory where this script is located
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  # Search for .env file in parent directories (up to project root)
  CURRENT_DIR="$SCRIPT_DIR"
  while [ "$CURRENT_DIR" != "/" ]; do
    # Go up one directory
    CURRENT_DIR="$(dirname "$CURRENT_DIR")"

    # Check if .env exists
    if [ -f "$CURRENT_DIR/.env" ]; then
      # Load .env file, but don't override existing environment variables
      while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue

        # Remove leading/trailing whitespace from key and value using parameter expansion
        # This avoids command injection vulnerabilities from xargs
        key="${key#"${key%%[![:space:]]*}"}"
        key="${key%"${key##*[![:space:]]}"}"
        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"

        # Validate key name (only allow alphanumeric and underscore)
        # This prevents code injection through arbitrary variable names
        if [[ ! "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
          continue
        fi

        # Remove surrounding quotes (either single or double)
        if [[ "$value" =~ ^\"(.*)\"$ ]] || [[ "$value" =~ ^\'(.*)\'$ ]]; then
          value="${BASH_REMATCH[1]}"
        fi

        # Only set if the environment variable is not already set
        if [ -z "${!key}" ]; then
          export "$key=$value"
        fi
      done < "$CURRENT_DIR/.env"

      return 0
    fi

    # Stop at git repository root
    if [ -d "$CURRENT_DIR/.git" ]; then
      break
    fi
  done

  return 1
}

# JSON escape function to safely include variables in JSON payloads
json_escape() {
  local value="$1"
  # Escape backslash, double quote, and control characters
  value="${value//\\/\\\\}"      # Escape backslash
  value="${value//\"/\\\"}"      # Escape double quote
  value="${value//$'\n'/\\n}"    # Escape newline
  value="${value//$'\r'/\\r}"    # Escape carriage return
  value="${value//$'\t'/\\t}"    # Escape tab
  echo "$value"
}

# Function to generate summary from transcript
generate_summary_from_transcript() {
  local transcript_path="$1"

  # Check if transcript file exists
  if [ ! -f "$transcript_path" ]; then
    return 1
  fi

  # Extract the last few user and assistant messages from JSONL transcript
  # Get last 5 lines, extract content from user/assistant messages
  local summary=""
  local last_messages=$(tail -20 "$transcript_path" | grep -E '"role":"(user|assistant)"' | tail -5)

  # Try to extract meaningful content
  local user_request=$(echo "$last_messages" | grep '"role":"user"' | tail -1 | grep -o '"content":"[^"]*"' | sed 's/"content":"//;s/"$//' | head -c 100)
  local assistant_action=$(echo "$last_messages" | grep '"role":"assistant"' | tail -1 | grep -o '"content":"[^"]*"' | sed 's/"content":"//;s/"$//' | head -c 100)

  # Generate Japanese summary based on extracted content
  if [ -n "$user_request" ]; then
    summary="ユーザーリクエスト: ${user_request}"
  elif [ -n "$assistant_action" ]; then
    summary="アシスタント作業: ${assistant_action}"
  fi

  # Fallback to file change summary if transcript parsing fails
  if [ -z "$summary" ] && git rev-parse --git-dir > /dev/null 2>&1; then
    local changed_files=$(git diff --name-only 2>/dev/null | wc -l)
    local main_file=$(git diff --name-only 2>/dev/null | head -1)
    main_file="${main_file##*/}"

    if [ "$changed_files" -gt 0 ] && [ -n "$main_file" ]; then
      if [ "$changed_files" -eq 1 ]; then
        summary="${main_file}を更新"
      else
        summary="${main_file}等${changed_files}件のファイルを更新"
      fi
    fi
  fi

  echo "$summary"
}

# Load environment variables from .env file (if exists)
# Existing environment variables take precedence
load_env_file

# Get configuration from environment variables
CHANNEL_ID="${SLACK_CHANNEL_ID}"
USER_MENTION="${SLACK_USER_MENTION}"

# Exit silently if required environment variables are not set
if [ -z "$CHANNEL_ID" ] || [ -z "$SLACK_BOT_TOKEN" ]; then
  exit 0
fi

# Read hook input from stdin (JSON with transcript_path)
HOOK_INPUT=""
if [ -t 0 ]; then
  # No stdin available (manual execution)
  HOOK_INPUT=""
else
  # Read from stdin
  HOOK_INPUT=$(cat)
fi

# Extract transcript_path from JSON input
TRANSCRIPT_PATH=""
if [ -n "$HOOK_INPUT" ]; then
  # Use grep to extract transcript_path (safer than jq dependency)
  TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | grep -o '"transcript_path":"[^"]*"' | cut -d'"' -f4)
fi

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check message type from arguments (for backward compatibility)
MESSAGE_TYPE=${1:-"session_end"}

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

# Escape message for JSON payload
ESCAPED_MENTION_MESSAGE=$(json_escape "$MENTION_MESSAGE")

RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"${CHANNEL_ID}\",
    \"text\": \"${ESCAPED_MENTION_MESSAGE}\"
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
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "${GIT_REPO:-unknown}")

# Generate work summary
WORK_SUMMARY=""

# Priority 1: Generate from transcript if available
if [ -n "$TRANSCRIPT_PATH" ]; then
  WORK_SUMMARY=$(generate_summary_from_transcript "$TRANSCRIPT_PATH")
fi

# Priority 2: Fallback to git diff if transcript summary is empty
if [ -z "$WORK_SUMMARY" ] && git rev-parse --git-dir > /dev/null 2>&1; then
  CHANGED_FILES=$(git diff --name-only 2>/dev/null | wc -l)
  MAIN_FILE=$(git diff --name-only 2>/dev/null | head -1)
  MAIN_FILE="${MAIN_FILE##*/}"

  if [ "$CHANGED_FILES" -gt 0 ] && [ -n "$MAIN_FILE" ]; then
    if [ "$CHANGED_FILES" -eq 1 ]; then
      WORK_SUMMARY="${MAIN_FILE}を更新"
    else
      WORK_SUMMARY="${MAIN_FILE}等${CHANGED_FILES}件のファイルを更新"
    fi
  fi
fi

# Truncate to 150 chars to accommodate transcript-generated summaries
WORK_SUMMARY=$(echo "$WORK_SUMMARY" | head -c 150)

# Create detailed message
if [ -n "$WORK_SUMMARY" ]; then
  DETAILED_MESSAGE="[${REPO_NAME}] ${MESSAGE}\n作業内容: ${WORK_SUMMARY}"
else
  DETAILED_MESSAGE="[${REPO_NAME}] ${MESSAGE}"
fi

# Escape message for JSON payload
ESCAPED_DETAILED_MESSAGE=$(json_escape "$DETAILED_MESSAGE")

curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"${CHANNEL_ID}\",
    \"text\": \"${ESCAPED_DETAILED_MESSAGE}\"
  }"
