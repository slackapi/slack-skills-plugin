# Heroku

Heroku runs the app as a `worker` dyno, a process type that binds no HTTP port.
Only `web` dynos have to listen on `$PORT`, so a Socket Mode app fits the `worker`
type exactly.

The deploy script for this provider is `heroku/deploy.sh`, alongside this file.
It is a self-contained bash script, run by the Slack CLI's `deploy` hook. Copy
it into the project root as described in the parent skill's Step 4.

**Cost.** Heroku has no free tier, and it requires a credit card. Tell the developer
this before running anything. Which paid tier applies depends on who owns the app:

- **A personal app** can use the Eco plan, $5/month pooled across the account.
- **A team app** cannot use Eco. It gets Basic dynos, billed per dyno per month,
  which is why scaling the unwanted `web` dyno to zero in the deploy script
  matters to the bill and not only to correctness.

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

## Environment variables

- `HEROKU_APP_NAME` (optional): the Heroku app name. Defaults to the project
  directory name. Heroku app names are globally unique across all of Heroku, so
  set this to something distinctive when a generic name is likely taken.
- `HEROKU_TEAM` (optional, sometimes required): the Heroku team to create the
  app under. Required when the account cannot own personal apps (Salesforce-
  managed accounts). Leave empty for a personal app.

---

## Re-deploying

The provision and configure steps in the deploy script reuse an existing app and
overwrite the two config vars, so both are safe to repeat. The one case needing
care is a re-deploy with no code change, which `git push` refuses as
up-to-date. The script handles it by making an empty commit, which leaves a
visible marker in the project's history. A developer who would rather not carry
those commits can instead change something real, or delete the empty commits
later.

---

## Verifying

```sh
heroku ps --app <name>                  # expect one worker dyno, state "up"
heroku logs --tail --app <name>         # look for the Socket Mode connection
heroku config --app <name>              # confirms both tokens are set
```

**Confirm only one dyno is running.** `heroku ps` should list `worker` at 1 and no
`web` process at all. If a `web` dyno appears, the app has two copies of itself
connected to Slack and the second one is in a restart loop. Re-run the scale
command from the deploy script. Checking the worker's own logs will not reveal
this: they look healthy either way.

**Check that the dyno stays up while idle, on an Eco app.** Heroku's Eco plan sleeps
a dyno after 30 minutes of inactivity. That behaviour is documented in terms of
inbound web traffic, and a Socket Mode worker takes no inbound HTTP at all, so
whether it applies here is unverified. Leave it idle for 45 minutes, then message the
app: a sleeping dyno drops the websocket and the app goes quiet in Slack. This does
not affect a team app, whose Basic dynos do not sleep.
