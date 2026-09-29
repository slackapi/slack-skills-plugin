#!/usr/bin/env bash
#
# Deploy a Socket Mode Bolt app to Heroku, as a Slack CLI `deploy` hook.
#
# Installed as .slack/deploy-heroku.sh and registered as the `deploy` hook in
# .slack/hooks.json by the deploy-slack-app skill. The CLI runs it from the
# project root after installing the deployed app, so relative paths resolve
# there and SLACK_BOT_TOKEN and SLACK_APP_TOKEN are inherited from its
# environment. That handoff is not a documented contract, which is why the
# checks below exist.
#
# Supported on macOS and Linux.

set -euo pipefail

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# The Heroku app name. When unset, reuse the app the `heroku` git remote already
# points at, so a re-deploy targets the same app even though an environment
# variable set on the first deploy is gone by the next one. The directory name
# is only the default for a first deploy. Heroku app names are global, so a
# generic one is often taken.
remote_app=$(
  git remote get-url heroku 2>/dev/null \
    | sed -n 's#.*/\([^/]*\)\.git$#\1#p' \
    || true
)
HEROKU_APP_NAME="${HEROKU_APP_NAME:-${remote_app:-$(basename "$PWD")}}"

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
git rev-parse --verify HEAD >/dev/null 2>&1 || die \
  "this repository has no commits yet. Heroku builds from a git push, so commit the project first."
[ -z "$(git status --porcelain)" ] || say \
  "warning: there are uncommitted or untracked changes. Heroku deploys committed code only, so those changes will not go live."
git ls-files --error-unmatch Procfile >/dev/null 2>&1 || die \
  "Procfile is missing or not committed. Heroku needs it to run this app as a worker rather than a web process. Create it with one line, such as 'worker: npm start' (Bolt for JavaScript) or 'worker: python app.py' (Bolt for Python), and commit it."

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

# heroku config:set takes values as arguments only, so these two tokens are
# visible to `ps` while the command runs. The Heroku CLI offers no alternative.
say "Setting SLACK_BOT_TOKEN and SLACK_APP_TOKEN on ${HEROKU_APP_NAME}"
heroku config:set \
  "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}" \
  "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}" \
  --app "${HEROKU_APP_NAME}" >/dev/null

# ---------------------------------------------------------------------------
# 5. Deploy
# ---------------------------------------------------------------------------

# Push the current HEAD to the app's main branch, whatever local branch the
# developer is on. The output is captured rather than piped so that a failed
# push is distinguishable from an up-to-date one.
#
# A push with no new commit reports "Everything up-to-date" and builds nothing.
# In that case the dynos are restarted below instead, which picks up any
# changed tokens. The code itself has not changed, so there is nothing to
# rebuild, and an empty commit would also sweep up anything the developer had
# staged.
say "Pushing to Heroku"
push_out=$(git push heroku HEAD:refs/heads/main 2>&1) \
  || die "the git push to Heroku failed:
${push_out}"
printf '%s\n' "${push_out}"

up_to_date=false
if printf '%s' "${push_out}" | grep -q 'Everything up-to-date'; then
  up_to_date=true
fi

# Run exactly one worker and no web dyno, in one call so there is no window
# with both running.
#
# The Node buildpack adds a default `web` process type even though the Procfile
# only declares `worker`, and Heroku starts it on the first release. It runs the
# same start command, so it is a second copy of the app holding a second Socket
# Mode connection, stuck in a restart loop because it never binds $PORT, and
# billed as a second dyno. The worker's own logs look healthy throughout.
#
# The Python buildpack adds no `web` type, and scaling one that does not exist
# is an error, so only scale web when the formation has it.
formation=$(heroku ps:scale --app "${HEROKU_APP_NAME}" 2>/dev/null || true)
if printf '%s' "${formation}" | grep -qE '(^|[[:space:]])web='; then
  say "Scaling the worker dyno to 1 and the web dyno to 0"
  heroku ps:scale worker=1 web=0 --app "${HEROKU_APP_NAME}"
else
  say "Scaling the worker dyno to 1"
  heroku ps:scale worker=1 --app "${HEROKU_APP_NAME}"
fi

if [ "${up_to_date}" = true ]; then
  say "No new commit to deploy. Restarting the dynos to pick up the current config."
  heroku ps:restart --app "${HEROKU_APP_NAME}"
fi

say ""
say "Deployed. A successful build does not prove the app started, so check for"
say "the Socket Mode connection in the app's logs:"
say "  heroku logs --num 100 --app ${HEROKU_APP_NAME}"
say "  heroku ps --app ${HEROKU_APP_NAME}"
