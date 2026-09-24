# Heroku

Heroku runs the app as a `worker` dyno, a process type that binds no HTTP port.
Only `web` dynos have to listen on `$PORT`, so a Socket Mode app fits the `worker`
type exactly.

**Cost.** Heroku has no free tier. The cheapest option is the Eco dyno plan at
$5/month, pooled across an account, and it requires a credit card. Tell the
developer this before running anything.

**Three things to know before choosing Heroku.**

- **Some accounts cannot own an app personally.** Salesforce-managed Heroku accounts
  are one case: `heroku apps:create` refuses with "All apps must belong to a team."
  Run `heroku teams` to see which teams the account belongs to, and set
  `HEROKU_TEAM` to one of them. Creating the app on a shared team spends that
  team's budget, so confirm with the developer which team to use rather than
  picking one.
- **Tokens go on the command line.** `heroku config:set` has no stdin or file
  input, so `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` appear as process arguments and
  are visible to `ps` while the command runs. The deploy hook runs the command
  rather than a person typing it, so it stays out of shell history, but the `ps`
  exposure is real. Railway avoids this with `railway variable set --stdin`.
- **Deploying means pushing a commit.** Heroku builds from git, not from the
  working directory, so the project must be a git repository and the code being
  deployed must be committed. Uncommitted changes are simply not deployed.

---

## Install and authenticate

```sh
brew tap heroku/brew && brew install heroku
heroku login                  # or export HEROKU_API_KEY for headless auth
heroku auth:whoami            # confirms the CLI is authenticated
```

`heroku login -i` cannot be used at all with multi-factor authentication enabled.
For a non-interactive setup, create a token with `heroku authorizations:create` and
export it as `HEROKU_API_KEY`.

---

## What Heroku needs from the project

A `Procfile` in the project root declaring the `worker` process type. Without it
Heroku infers a `web` process from the start command, which is the wrong shape: it
would expect the app to bind a port and mark the deploy as failed when it does not.

```text
worker: npm start
```

For Bolt for Python, use the project's own entrypoint, for example
`worker: python app.py`.

---

## Write `.slack/deploy-target.sh`

```sh
#!/usr/bin/env bash
# Heroku target for deploy.sh. Sourced, not executed.

TARGET_NAME="Heroku"
HEROKU_APP_NAME="${HEROKU_APP_NAME:-$(basename "$PWD")}"

# Set HEROKU_TEAM when the app has to belong to a Heroku team rather than to the
# account personally. Some accounts, including Salesforce-managed ones, cannot own
# personal apps at all: `apps:create` refuses with "All apps must belong to a team.
# Create the app on a team instead." Leave it empty for a personal app.
HEROKU_TEAM="${HEROKU_TEAM:-}"

target_preflight() {
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
}

target_provision() {
  # apps:create fails outright when the app already exists, so check first. This
  # is what lets a re-deploy target the same app instead of erroring.
  #
  # Note that apps:info reports "Couldn't find that app" both for an app that does
  # not exist and for one that exists under another account, because Heroku app
  # names are globally unique across all of Heroku. A generic name taken by a
  # stranger therefore reaches apps:create below and fails there on the name rather
  # than here. Set HEROKU_APP_NAME to something distinctive to avoid it.
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
}

target_configure() {
  # heroku config:set takes values as arguments only: there is no stdin or file
  # input, so these two tokens are visible to `ps` for the life of the command.
  # Nothing here can avoid that; it is a property of the Heroku CLI.
  say "Setting SLACK_BOT_TOKEN and SLACK_APP_TOKEN on ${HEROKU_APP_NAME}"
  heroku config:set \
    "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}" \
    "SLACK_APP_TOKEN=${SLACK_APP_TOKEN}" \
    --app "${HEROKU_APP_NAME}" >/dev/null
}

target_deploy() {
  # Push the current HEAD to the app's main branch, whatever local branch the
  # developer is on. A push with no new commit reports "Everything up-to-date" and
  # builds nothing, so make an empty commit to force a rebuild in that case.
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

  # A worker dyno starts at zero. Scaling to one is what actually runs the app,
  # and it is a no-op when the dyno is already running.
  say "Scaling the worker dyno to 1"
  heroku ps:scale worker=1 --app "${HEROKU_APP_NAME}"

  say "Follow the build and the websocket connection with:"
  say "  heroku logs --tail --app ${HEROKU_APP_NAME}"
  say "Check dyno state with:"
  say "  heroku ps --app ${HEROKU_APP_NAME}"
}
```

---

## Re-deploying

`target_provision` reuses an existing app and `target_configure` overwrites the two
config vars, so both are safe to repeat. The one case needing care is a re-deploy
with no code change, which `git push` refuses as up-to-date. The function above
handles it by making an empty commit, which leaves a visible marker in the project's
history. A developer who would rather not carry those commits can instead change
something real, or delete the empty commits later.

---

## Verifying

```sh
heroku ps --app <name>                  # expect one worker dyno, state "up"
heroku logs --tail --app <name>         # look for the Socket Mode connection
heroku config --app <name>              # confirms both tokens are set
```

**Check that the dyno stays up while idle.** Heroku's Eco plan sleeps a dyno after
30 minutes of inactivity. That behaviour is documented in terms of inbound web
traffic, and a Socket Mode worker takes no inbound HTTP at all, so whether it
applies here is worth confirming on the specific app rather than assuming. Leave it
idle for 45 minutes, then message the app. A sleeping dyno drops the websocket and
the app stops answering in Slack.
