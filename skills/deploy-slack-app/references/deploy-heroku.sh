#!/usr/bin/env bash
#
# Deploy a Socket Mode Bolt app to Heroku, as a Slack CLI `deploy` hook.
#
# Save it as .slack/deploy-heroku.sh and wire it up by adding a `deploy` key to
# the project's .slack/hooks.json:
#
#   {
#     "hooks": {
#       "get-hooks": "npx -q --no-install -p @slack/cli-hooks slack-cli-get-hooks",
#       "deploy": "./.slack/deploy-heroku.sh"
#     }
#   }
#
# Then run `slack deploy`. The CLI creates and installs the deployed app first,
# which is what puts SLACK_BOT_TOKEN and SLACK_APP_TOKEN in this script's
# environment, and then runs this file through `sh -c` from the project root,
# so relative paths below resolve against the project root, not .slack/.
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

HEROKU_APP_NAME="${HEROKU_APP_NAME:-$(basename "$PWD")}"

# Set HEROKU_TEAM when the app has to belong to a Heroku team rather than to the
# account personally. Some accounts, including enterprise-managed ones, cannot
# own personal apps at all: `apps:create` refuses with "All apps must belong to
# a team. Create the app on a team instead." Leave empty for a personal app.
HEROKU_TEAM="${HEROKU_TEAM:-}"

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

command -v heroku >/dev/null 2>&1 || die \
  "the heroku CLI is not installed. Install it with 'brew tap heroku/brew && brew install heroku' (macOS) or see https://devcenter.heroku.com/articles/heroku-cli, then re-run 'slack deploy'."
heroku auth:whoami >/dev/null 2>&1 || die \
  "the heroku CLI is not authenticated. Run 'heroku login' (or set HEROKU_API_KEY), then re-run 'slack deploy'."
git rev-parse --git-dir >/dev/null 2>&1 || die \
  "this project is not a git repository. Heroku builds from a git push, so run 'git init' and commit the project first."
git diff --quiet && git diff --cached --quiet || say \
  "warning: there are uncommitted changes. Heroku deploys committed code only, so those changes will not go live."
[ -f Procfile ] || die \
  "Procfile is missing. Heroku needs it to run this app as a worker rather than a web process. Create it with one line: 'worker: npm start'."

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

say "Deploying Slack app ${app_id} to Heroku"

# ---------------------------------------------------------------------------
# 3. Provision the Heroku app
# ---------------------------------------------------------------------------

# apps:create fails outright when the app already exists, so check first. This
# is what lets a re-deploy target the same app instead of erroring.
#
# apps:info reports "Couldn't find that app" both for an app that does not exist
# and for one that exists under another account, because Heroku app names are
# globally unique across all of Heroku. A generic name taken by a stranger
# therefore reaches apps:create below and fails there on the name rather than
# here. Set HEROKU_APP_NAME to something distinctive to avoid it.
if heroku apps:info --app "${HEROKU_APP_NAME}" >/dev/null 2>&1; then
  say "Reusing the Heroku app ${HEROKU_APP_NAME}"
else
  say "Creating the Heroku app ${HEROKU_APP_NAME}"
  if [ -n "${HEROKU_TEAM}" ]; then
    heroku apps:create "${HEROKU_APP_NAME}" --team "${HEROKU_TEAM}" >/dev/null
  else
    heroku apps:create "${HEROKU_APP_NAME}" >/dev/null
  fi
fi

# Sets or resets the `heroku` git remote to point at this app. Safe to repeat.
heroku git:remote --app "${HEROKU_APP_NAME}" >/dev/null

# ---------------------------------------------------------------------------
# 4. Configure secrets
# ---------------------------------------------------------------------------

# heroku config:set takes values as arguments only: there is no stdin or file
# input, so these two tokens are visible to `ps` for the life of the command.
# Nothing here can avoid that; it is a property of the Heroku CLI.
say "Setting SLACK_BOT_TOKEN and SLACK_APP_TOKEN on ${HEROKU_APP_NAME}"
heroku config:set \
  "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}" \
  "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}" \
  --app "${HEROKU_APP_NAME}" >/dev/null

# ---------------------------------------------------------------------------
# 5. Deploy
# ---------------------------------------------------------------------------

# Push the current HEAD to the app's main branch, whatever local branch the
# developer is on. A push with no new commit reports "Everything up-to-date"
# and builds nothing, so make an empty commit to force a rebuild in that case.
#
# The output is captured rather than piped so that a genuinely failed push is
# distinguishable from an up-to-date one. Piping into grep would swallow the
# difference and re-push over a real error.
say "Pushing to Heroku"
push_out=$(git push heroku HEAD:refs/heads/main 2>&1) \
  || die "the git push to Heroku failed:
${push_out}"
printf '%s\n' "${push_out}"

if printf '%s' "${push_out}" | grep -q 'Everything up-to-date'; then
  say "No new commit to deploy. Forcing a rebuild of the current code."
  git commit --allow-empty -m "chore: redeploy to Heroku" >/dev/null
  git push heroku HEAD:refs/heads/main
fi

# Scale worker up and web down, in one call, and never scale worker alone.
#
# The Node buildpack contributes a default `web` process type even though the
# Procfile only declares `worker`, and Heroku starts that web dyno on the first
# release. It runs the same `npm start`, so it becomes a second copy of the app:
# it opens its own Socket Mode connection, Slack then reports
# "num_connections": 2, and events are delivered to whichever copy Slack picks.
# It also never boots successfully, because a Socket Mode app binds no port and
# Heroku kills a web dyno that does not bind $PORT within 60 seconds, so it
# sits in a restart loop opening a fresh connection on every cycle. And it
# bills as a second dyno.
#
# None of that is visible from the worker's own logs, which look perfectly
# healthy, so scaling web to zero is not optional tidying.
say "Scaling the worker dyno to 1 and the web dyno to 0"
heroku ps:scale worker=1 web=0 --app "${HEROKU_APP_NAME}"

say ""
say "Deployed. The app runs in Socket Mode, so it has no public URL by design."
say "Follow the build and the websocket connection with:"
say "  heroku logs --tail --app ${HEROKU_APP_NAME}"
say "Check dyno state with:"
say "  heroku ps --app ${HEROKU_APP_NAME}"
