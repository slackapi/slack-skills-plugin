# Railway

Railway runs the app as a long-lived service built from the uploaded working
directory. It suits a Socket Mode app well: the service binds no HTTP port, and
Railway does not require one.

The deploy script for this provider is `deploy-railway.sh`, alongside this file.
It is a self-contained bash script, run by the Slack CLI's `deploy` hook. Copy
it to `.slack/deploy-railway.sh` in the project as described in the parent
skill's Step 4.

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

## What Railway needs from the project

Nothing. Railway's builder detects a Node.js or Python project and runs its start
command, so no `Procfile`, `Dockerfile`, or config file is required. Make sure the
project's own start command runs the app: `npm start` for Bolt for JavaScript,
which means `package.json` needs a `scripts.start` entry.

---

## Environment variables

- `RAILWAY_PROJECT_NAME` (optional): the Railway project name. Defaults to the
  project directory name.
- `RAILWAY_SERVICE_NAME` (optional): the Railway service name. Defaults to the
  project directory name.

---

## Re-deploying

The deploy script is safe to run again. `railway up` uploads the current working
directory and rebuilds every time, so a re-deploy needs no commit and no cache
flush. Setting a variable to the same value is a no-op.

---

## Verifying

```sh
railway status                # service state
railway logs                  # look for the Socket Mode connection
```

Expect the build to take a few minutes on the first deploy. Railway injects a
`PORT` variable even when nothing listens on it, which is harmless for a Socket
Mode app.
