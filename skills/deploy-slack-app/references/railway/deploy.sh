#!/usr/bin/env bash
#
# Deploy a Socket Mode Bolt app to Railway, as a Slack CLI `deploy` hook.
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
# The CLI passes nothing explicitly. The tokens arrive because the install step
# runs earlier in the same process and sets them on it, so this script inherits
# them rather than being handed them. That is not a documented contract, which
# is why the checks below exist.
#
# Supported on macOS and Linux. Windows needs a PowerShell port of this file.

set -euo pipefail

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

RAILWAY_PROJECT_NAME="${RAILWAY_PROJECT_NAME:-$(basename "$PWD")}"
RAILWAY_SERVICE_NAME="${RAILWAY_SERVICE_NAME:-$(basename "$PWD")}"

# ---------------------------------------------------------------------------
# 1. Preconditions
# ---------------------------------------------------------------------------

# Both tokens are required. A Socket Mode app cannot open a websocket without an
# app-level token carrying connections:write, so a missing SLACK_APP_TOKEN is a
# hard stop rather than something to warn about and continue past.
[ -n "${SLACK_BOT_TOKEN:-}" ] || die \
  "SLACK_BOT_TOKEN is not set. It is normally supplied by 'slack deploy' during app install. If you are running this script directly, export it first."
[ -n "${SLACK_APP_TOKEN:-}" ] || die \
  "SLACK_APP_TOKEN is not set. Socket Mode needs an app-level token with connections:write. It is normally supplied by 'slack deploy' during app install."

command -v railway >/dev/null 2>&1 || die \
  "the railway CLI is not installed. Install it with 'brew install railway' (macOS) or see https://docs.railway.com/guides/cli, then re-run 'slack deploy'."
railway whoami >/dev/null 2>&1 || die \
  "the railway CLI is not authenticated. Run 'railway login' (or set RAILWAY_TOKEN for a project token), then re-run 'slack deploy'."

# ---------------------------------------------------------------------------
# 2. Report which app is being deployed
# ---------------------------------------------------------------------------

# The deploy hook receives no app ID, so read it off disk. .slack/apps.json holds
# deployed apps keyed by team ID; .slack/apps.dev.json holds the local dev app
# and is deliberately not touched here.
#
# Parsed with grep and sed rather than a language runtime: this script has to
# work in a Bolt for Python project as readily as a Bolt for JavaScript one.
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

say "Deploying Slack app ${app_id} to Railway"

# ---------------------------------------------------------------------------
# 3. Provision the Railway project and service
# ---------------------------------------------------------------------------

# `railway status` fails when the directory is not linked to a project. Reusing
# an existing link is what makes a re-deploy update the same service instead of
# creating a second project on every run.
if railway status >/dev/null 2>&1; then
  say "Reusing the Railway project already linked to this directory"
else
  say "No linked Railway project. Creating ${RAILWAY_PROJECT_NAME}"
  railway init -n "${RAILWAY_PROJECT_NAME}"
fi

# A fresh `railway init` leaves the project with no service at all, and every
# variable command fails with "Project has no services" until one exists. So
# create the service explicitly before setting anything on it.
#
# `railway add -s NAME` on its own still prompts ("Enter a variable") and hangs
# in a non-interactive shell even though the name was supplied. Passing
# --variables answers that prompt. The value here is a harmless marker, not a
# secret: the two tokens go over stdin below, never on a command line.
if railway variable list --service "${RAILWAY_SERVICE_NAME}" >/dev/null 2>&1; then
  say "Reusing the Railway service ${RAILWAY_SERVICE_NAME}"
else
  say "Creating the Railway service ${RAILWAY_SERVICE_NAME}"
  railway add --service "${RAILWAY_SERVICE_NAME}" --variables "SLACK_DEPLOY_HOOK=1" >/dev/null
fi

# ---------------------------------------------------------------------------
# 4. Configure secrets
# ---------------------------------------------------------------------------

# --stdin keeps the token values out of the command line, so they never reach
# `ps` output or a shell history file. --skip-deploys stops each set from
# triggering its own build; the single `railway up` below is the deploy.
say "Setting SLACK_BOT_TOKEN and SLACK_APP_TOKEN on ${RAILWAY_SERVICE_NAME}"
printf '%s' "${SLACK_BOT_TOKEN}" \
  | railway variable set SLACK_BOT_TOKEN --service "${RAILWAY_SERVICE_NAME}" --stdin --skip-deploys >/dev/null
printf '%s' "${SLACK_APP_TOKEN}" \
  | railway variable set SLACK_APP_TOKEN --service "${RAILWAY_SERVICE_NAME}" --stdin --skip-deploys >/dev/null

# ---------------------------------------------------------------------------
# 5. Deploy
# ---------------------------------------------------------------------------

say "Uploading and building"
railway up --service "${RAILWAY_SERVICE_NAME}" --detach

say ""
say "Deployed. The app runs in Socket Mode, so it has no public URL by design."
say "Follow the build and the websocket connection with:"
say "  railway logs"
say "Check service health with:"
say "  railway status"
