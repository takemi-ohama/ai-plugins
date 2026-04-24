#!/usr/bin/env bash
# NDF plugin: ~/.claude/settings.json の cleanupPeriodDays を最低 90 日に保つ。
# - 既存値 >= 90 なら何もしない
# - 既存値 < 90 or 未設定 なら 90 に更新
# - 前回チェックから 7 日経っていなければスキップ (多重実行防止)
set -euo pipefail

MIN_DAYS=90
GUARD_DAYS=7
SETTINGS="$HOME/.claude/settings.json"
FLAG="$HOME/.claude/.ndf-retention-checked"

# jq 必須
if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

# 7 日以内に実行済みならスキップ
if [ -f "$FLAG" ]; then
  if find "$FLAG" -mtime "-${GUARD_DAYS}" -print -quit 2>/dev/null | grep -q .; then
    exit 0
  fi
fi

# settings.json が存在しない場合は新規作成
if [ ! -f "$SETTINGS" ]; then
  mkdir -p "$(dirname "$SETTINGS")"
  echo "{}" > "$SETTINGS"
fi

# 現在値を取得 (null/未設定は 0 として扱う)
CURRENT=$(jq -r '.cleanupPeriodDays // 0' "$SETTINGS" 2>/dev/null || echo 0)
# 数値以外の場合に備えて再度正規化
case "$CURRENT" in
  ''|*[!0-9]*) CURRENT=0 ;;
esac

if [ "$CURRENT" -lt "$MIN_DAYS" ]; then
  tmp="$(mktemp)"
  if jq --argjson v "$MIN_DAYS" '.cleanupPeriodDays = $v' "$SETTINGS" > "$tmp"; then
    mv "$tmp" "$SETTINGS"
    echo "[ndf] cleanupPeriodDays を ${CURRENT} → ${MIN_DAYS} に更新しました (~/.claude/settings.json)"
  else
    rm -f "$tmp"
  fi
fi

touch "$FLAG"
