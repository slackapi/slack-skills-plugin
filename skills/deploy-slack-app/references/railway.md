# Railway

Railway runs the app as a long-lived service built from the uploaded working
directory. It suits a Socket Mode app well: the service binds no HTTP port, and
Railway does not require one.

**Cost.** Railway's Free Trial is a one-time credit with no credit card required,
which makes it the cheapest way to get a Slack app running for the first time. A
long-running service consumes that credit continuously, so it will need a paid plan
to stay up.

---

## Install and authenticate

```sh
brew install railway          # macOS; see https://docs.railway.com/guides/cli
railway login                 # or export RAILWAY_TOKEN for a headless project token
railway whoami                # confirms the CLI is authenticated
```

---

## Write `.slack/deploy-target.sh`

```sh
#!/usr/bin/env bash
# Railway target for deploy.sh. Sourced, not executed.

TARGET_NAME="Railway"
RAILWAY_PROJECT_NAME="${RAILWAY_PROJECT_NAME:-$(basename "$PWD")}"
RAILWAY_SERVICE_NAME="${RAILWAY_SERVICE_NAME:-$(basename "$PWD")}"

target_preflight() {
  command -v railway >/dev/null 2>&1 || die \
    "the railway CLI is not installed. Install it with 'brew install railway' (macOS) or see https://docs.railway.com/guides/cli, then re-run 'slack deploy'."
  railway whoami >/dev/null 2>&1 || die \
    "the railway CLI is not authenticated. Run 'railway login' (or set RAILWAY_TOKEN for a project token), then re-run 'slack deploy'."
}

target_provision() {
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
}

target_configure() {
  # --stdin keeps the token values out of the command line, so they never reach
  # `ps` output or a shell history file. --skip-deploys stops each set from
  # triggering its own build; the single `railway up` below is the deploy.
  say "Setting SLACK_BOT_TOKEN and SLACK_APP_TOKEN on ${RAILWAY_SERVICE_NAME}"
  printf '%s' "${SLACK_BOT_TOKEN}" \
    | railway variable set SLACK_BOT_TOKEN --service "${RAILWAY_SERVICE_NAME}" --stdin --skip-deploys >/dev/null
  printf '%s' "${SLACK_APP_TOKEN}" \
    | railway variable set SLACK_APP_TOKEN --service "${RAILWAY_SERVICE_NAME}" --stdin --skip-deploys >/dev/null
}

target_deploy() {
  say "Uploading and building"
  railway up --service "${RAILWAY_SERVICE_NAME}" --detach

  say "Follow the build and the websocket connection with:"
  say "  railway logs"
  say "Check service health with:"
  say "  railway status"
}
```

---

## What Railway needs from the project

Nothing. Railway's builder detects a Node.js or Python project and runs its start
command, so no `Procfile`, `Dockerfile`, or config file is required. Make sure the
project's own start command runs the app: `npm start` for Bolt for JavaScript,
which means `package.json` needs a `scripts.start` entry.

---

## Re-deploying

All four functions above are safe to run again. `railway up` uploads the current
working directory and rebuilds every time, so a re-deploy needs no commit and no
cache flush. Setting a variable to the same value is a no-op.

---

## Verifying

```sh
railway status                # service state
railway logs                  # look for the Socket Mode connection
```

Expect the build to take a few minutes on the first deploy. Railway injects a
`PORT` variable even when nothing listens on it, which is harmless for a Socket
Mode app.
