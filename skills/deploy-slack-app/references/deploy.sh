#!/usr/bin/env bash
#
# Deploy a Socket Mode Bolt app to a hosting provider, as a Slack CLI `deploy` hook.
#
# This file is host-agnostic. Everything provider-specific lives in
# .slack/deploy-target.sh, which this script sources and which must define four
# functions:
#
#   target_preflight    read-only checks: provider CLI installed and authenticated
#   target_provision    create the app/project/service, or reuse an existing one
#   target_configure    set SLACK_BOT_TOKEN and SLACK_APP_TOKEN on the service
#   target_deploy       ship the code, then print how to follow the logs
#
# It may also set TARGET_NAME for nicer output. Each function must be safe to run
# repeatedly: a re-deploy runs all four again against an app that already exists.
#
# Wire it up by adding a `deploy` key to the project's .slack/hooks.json:
#
#   {
#     "hooks": {
#       "get-hooks": "npx -q --no-install -p @slack/cli-hooks slack-cli-get-hooks",
#       "deploy": "./deploy.sh"
#     }
#   }
#
# Then run `slack deploy`. The CLI creates and installs the deployed app first,
# which is what puts SLACK_BOT_TOKEN and SLACK_APP_TOKEN in this script's
# environment, and then runs this file through `sh -c` from the project root.
#
# Note the CLI passes nothing explicitly. The tokens arrive because the install
# step runs earlier in the same process and sets them on it, so this script
# inherits them rather than being handed them. That is not a documented contract,
# which is why the checks below exist.
#
# Supported on macOS and Linux. Windows needs a PowerShell port of this file.

set -euo pipefail

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

TARGET_FILE=".slack/deploy-target.sh"

# ---------------------------------------------------------------------------
# 1. Preconditions
# ---------------------------------------------------------------------------

[ -f "${TARGET_FILE}" ] || die \
  "${TARGET_FILE} is missing. It holds the provider-specific half of this deploy and is written when the deploy hook is first set up."

# Both tokens are required. A Socket Mode app cannot open a websocket without an
# app-level token carrying connections:write, so a missing SLACK_APP_TOKEN is a
# hard stop rather than something to warn about and continue past.
[ -n "${SLACK_BOT_TOKEN:-}" ] || die \
  "SLACK_BOT_TOKEN is not set. It is normally supplied by 'slack deploy' during app install. If you are running this script directly, export it first."
[ -n "${SLACK_APP_TOKEN:-}" ] || die \
  "SLACK_APP_TOKEN is not set. Socket Mode needs an app-level token with connections:write. It is normally supplied by 'slack deploy' during app install."

# shellcheck source=/dev/null
. "${TARGET_FILE}"

for fn in target_preflight target_provision target_configure target_deploy; do
  command -v "${fn}" >/dev/null 2>&1 || die \
    "${TARGET_FILE} does not define ${fn}(). All four of target_preflight, target_provision, target_configure, and target_deploy are required."
done

# ---------------------------------------------------------------------------
# 2. Report which app is being deployed
# ---------------------------------------------------------------------------

# The deploy hook receives no app ID, so read it off disk. .slack/apps.json holds
# deployed apps keyed by team ID; .slack/apps.dev.json holds the local dev app and
# is deliberately not touched here.
#
# Parsed with grep and sed rather than a language runtime: this script has to work
# in a Bolt for Python project as readily as a Bolt for JavaScript one.
app_id="unknown"
if [ -f .slack/apps.json ]; then
  found=$(
    tr -d '\n' < .slack/apps.json \
      | grep -o '"app_id"[[:space:]]*:[[:space:]]*"[^"]*"' \
      | sed 's/.*"\([^"]*\)"$/\1/' \
      | paste -sd , - \
      || true
  )
  [ -n "${found}" ] && app_id="${found}"
fi

say "Deploying Slack app ${app_id} to ${TARGET_NAME:-the configured provider}"

# ---------------------------------------------------------------------------
# 3. Hand off to the provider
# ---------------------------------------------------------------------------

target_preflight
target_provision

# The two tokens are the only secrets in play. Providers that accept a value on
# stdin should use that, so the tokens never reach `ps` output or a shell history
# file. Where a provider only accepts them as command-line arguments, its
# reference file says so.
target_configure

target_deploy

say ""
say "Deployed. The app runs in Socket Mode, so it has no public URL by design."
