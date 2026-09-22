#!/usr/bin/env bash
# Run on the mini-PC for first-time clone.
# Usage: bash clone-on-mini-pc.sh [target_dir]

set -euo pipefail

REPO_URL="https://github.com/Merxius2/news-trader-advisor.git"
TARGET="${1:-$HOME/news-trader-advisor}"

if [[ -d "$TARGET/.git" ]]; then
  echo "Already cloned at $TARGET — run: cd $TARGET && git pull origin main"
  exit 0
fi

git clone "$REPO_URL" "$TARGET"
echo "Cloned to $TARGET"
echo "Next: cd $TARGET"
