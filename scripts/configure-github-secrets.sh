#!/usr/bin/env bash

set -euo pipefail

repository="${FOOTBALL_LAB_REPOSITORY:-aniketgiriyalkar/Soccer-Analytics}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required: https://cli.github.com/"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run 'gh auth login' and retry."
  exit 1
fi

set_secret() {
  local name="$1"
  local description="$2"
  local value

  printf "%s (leave blank to skip): " "$description"
  IFS= read -r -s value
  printf "\n"

  if [[ -z "$value" ]]; then
    echo "Skipped $name."
    return
  fi

  printf "%s" "$value" | gh secret set "$name" --repo "$repository"
  unset value
  echo "Configured $name."
}

echo "Configuring GitHub Actions secrets for $repository."
echo "Values are read silently and sent directly to GitHub; no local secret file is created."
echo

set_secret \
  "FOOTBALL_DATA_API_KEY" \
  "football-data.org API key"
set_secret \
  "API_FOOTBALL_KEY" \
  "API-Football key"

echo
echo "Configured secret names:"
gh secret list --repo "$repository" --json name,updatedAt \
  --jq '.[] | select(.name == "FOOTBALL_DATA_API_KEY" or .name == "API_FOOTBALL_KEY") | "\(.name)\t\(.updatedAt)"'
