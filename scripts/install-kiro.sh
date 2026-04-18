#!/bin/bash
# NDF Plugin Installer for Kiro CLI
# Usage: bash scripts/install-kiro.sh [--with-slack] [--with-codex]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$PROJECT_ROOT/plugins/ndf"
KIRO_DIR="$PROJECT_ROOT/.kiro"
AGENT_FILE="$KIRO_DIR/agents/default.json"
PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"

# Parse options
WITH_SLACK=false
WITH_CODEX=false
for arg in "$@"; do
  case "$arg" in
    --with-slack) WITH_SLACK=true ;;
    --with-codex) WITH_CODEX=true ;;
    --help|-h)
      echo "Usage: bash scripts/install-kiro.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --with-slack   stopフックにSlack通知を追加"
      echo "  --with-codex   Codex CLI MCPサーバーを追加"
      echo "  -h, --help     このヘルプを表示"
      exit 0
      ;;
  esac
done

echo "=== NDF Plugin Installer for Kiro CLI ==="

# Validate plugin.json exists
if [ ! -f "$PLUGIN_JSON" ]; then
  echo "ERROR: $PLUGIN_JSON が見つかりません" >&2
  exit 1
fi

# Create .kiro/agents/ if needed
mkdir -p "$KIRO_DIR/agents"

# Build resources array from plugin.json skills
echo "Skills を検出中..."
RESOURCES='"file://AGENTS.md"'
RESOURCES="$RESOURCES, \"file://README.md\""

# Read skills from plugin.json and generate skill:// entries
while IFS= read -r skill_path; do
  # Remove ./  prefix and quotes
  skill_path="${skill_path#./}"
  skill_md="plugins/ndf/${skill_path}/SKILL.md"

  if [ ! -f "$PROJECT_ROOT/$skill_md" ]; then
    echo "  SKIP: $skill_md (ファイルなし)"
    continue
  fi

  # ndf-policies is always-on (file://), others are on-demand (skill://)
  if [[ "$skill_path" == *"ndf-policies"* ]]; then
    RESOURCES="$RESOURCES, \"file://$skill_md\""
    echo "  常時: $skill_path"
  else
    RESOURCES="$RESOURCES, \"skill://$skill_md\""
    echo "  登録: $skill_path"
  fi
done < <(grep -oP '"\.\/skills\/[^"]+' "$PLUGIN_JSON" | sed 's/"//g')

# Build hooks
HOOKS=""
# agentSpawn: CLAUDE.ndf.md deprecation warning
AGENTSPAWN_CMD='if [ -f \"${PWD}/CLAUDE.ndf.md\" ] || [ -f \"$HOME/.claude/CLAUDE.ndf.md\" ]; then echo \"[NDF] CLAUDE.ndf.md が検出されました。廃止済みです。cleanup を実行して削除してください。\"; fi'
HOOKS="\"agentSpawn\": [{\"command\": \"$AGENTSPAWN_CMD\"}]"

if [ "$WITH_SLACK" = true ]; then
  HOOKS="$HOOKS, \"stop\": [{\"command\": \"node plugins/ndf/scripts/slack-notify.js session_end\", \"timeout_ms\": 70000}]"
  echo "Slack通知: 有効"
else
  echo "Slack通知: 無効 (--with-slack で有効化)"
fi

# Build mcpServers
MCP=""
if [ "$WITH_CODEX" = true ]; then
  MCP="\"mcpServers\": {\"codex\": {\"command\": \"codex\", \"args\": [\"mcp-server\"], \"env\": {}}}"
  echo "Codex MCP: 有効"
else
  echo "Codex MCP: 無効 (--with-codex で有効化)"
fi

# Backup existing config
if [ -f "$AGENT_FILE" ]; then
  cp "$AGENT_FILE" "${AGENT_FILE}.bak"
  echo "既存設定をバックアップ: ${AGENT_FILE}.bak"
fi

# Generate agent JSON
{
  echo "{"
  echo "  \"name\": \"default\","
  echo "  \"description\": \"NDF統合開発エージェント（Kiro CLI用）\","
  echo "  \"resources\": [$RESOURCES],"
  echo "  \"hooks\": {$HOOKS}"
  [ -n "$MCP" ] && echo "  , $MCP"
  echo "}"
} > "$AGENT_FILE"

# Pretty-print with python if available, otherwise leave as-is
if command -v python3 &>/dev/null; then
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); json.dump(d,open(sys.argv[1],'w'),indent=2,ensure_ascii=False)" "$AGENT_FILE" 2>/dev/null || true
fi

SKILL_COUNT=$(grep -c 'skill://' "$AGENT_FILE" || echo 0)
echo ""
echo "=== インストール完了 ==="
echo "  エージェント設定: $AGENT_FILE"
echo "  登録Skills数: $SKILL_COUNT"
echo ""
echo "Kiro CLIを起動して動作確認してください:"
echo "  kiro-cli chat"
