#!/usr/bin/env bash
# Pull latest main on the mini-PC via SSH.
# Requires config/mini-pc.env (see config/mini-pc.env.example).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${MINI_PC_ENV:-$ROOT/config/mini-pc.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  echo "Copy config/mini-pc.env.example to config/mini-pc.env and set MINI_PC_HOST + MINI_PC_REPO_PATH"
  exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

: "${MINI_PC_HOST:?Set MINI_PC_HOST in $ENV_FILE}"
: "${MINI_PC_REPO_PATH:?Set MINI_PC_REPO_PATH in $ENV_FILE}"

echo "Syncing mini-PC: $MINI_PC_HOST:$MINI_PC_REPO_PATH"

ssh "$MINI_PC_HOST" "cd $MINI_PC_REPO_PATH && git fetch origin && git pull --ff-only origin main"

echo "Done. Mini-PC is on latest main."
