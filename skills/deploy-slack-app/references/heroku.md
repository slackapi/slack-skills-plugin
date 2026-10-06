# Heroku

Heroku runs the app as a `worker` dyno, a process type that binds no HTTP port.
Only `web` dynos have to listen on `$PORT`, so a Socket Mode app fits the `worker`
type exactly.

The deploy script for this provider is `deploy-heroku.sh`, alongside this file.
Copy it to `.slack/deploy-heroku.sh` as described in the parent skill's Step 4.

**Cost.** Current pricing is at <https://www.heroku.com/pricing>. Point the developer
there rather than quoting or fetching it. Two things hold whatever the price list
says:

- **Who owns the app changes the bill.** Personal apps and team apps can have
  different plans available and be billed differently, and a shared team has a
  shared budget. Confirm with the developer which one they are creating.
- **Every running dyno counts.** That is why the deploy script makes sure no `web`
  dyno runs alongside the worker.

**Three things to know before choosing Heroku.**

- **Some accounts cannot own an app personally.** Enterprise-managed Heroku accounts
  are one case: `heroku apps:create` refuses with "All apps must belong to a team."
  Run `heroku teams` to see which teams the account belongs to, ask the developer
  which one to use, and set `HEROKU_TEAM` to it.
- **Tokens go on the command line.** `heroku config:set` has no stdin or file
  input, so `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` appear as process arguments and
  are visible to `ps` while the command runs. The deploy hook runs the command
  rather than a person typing it, so it stays out of shell history, but the `ps`
  exposure is real. Mention it to the developer.
- **Deploying means pushing a commit.** Heroku builds from git, not from the
  working directory, so the project must be a git repository with at least one
  commit, and the code being deployed must be committed. Uncommitted changes are
  not deployed.

---

## Install and authenticate

```sh
brew tap heroku/brew && brew install heroku
heroku auth:whoami            # confirms the CLI is authenticated
```

If `heroku auth:whoami` fails, ask the developer to run `heroku login` in their
own terminal. It waits for a keypress and opens a browser, so it cannot complete
inside an agent session. For a headless setup, create a token with
`heroku authorizations:create` and export it as `HEROKU_API_KEY`.

---

## What Heroku needs from the project

A committed `Procfile` in the project root declaring the `worker` process type.
Without it Heroku infers a `web` process from the start command, which is the
wrong shape: it would expect the app to bind a port and mark the deploy as failed
when it does not. Write it with the project's own start command:

```text
worker: npm start
```

For Bolt for Python, use the project's entrypoint, for example
`worker: python app.py`. Commit the file before deploying: the deploy script stops
if the `Procfile` is not in git, because an uncommitted one never reaches Heroku.

The project must be its own git repository, not a directory inside another one.
`slack create` does not run `git init`, so check with `git rev-parse --show-toplevel`
and run `git init` in the project if it names a parent directory. The deploy script
stops in that case, because the push would deploy the parent repository's code.

For Bolt for Python, also commit a `.python-version` file holding the major and minor
version the app runs on locally, such as `3.13`. Without one, Heroku picks its own
default version and warns that a missing file will become an error.

---

## Environment variables

- `HEROKU_APP_NAME` (optional): the Heroku app name. When unset, the script reuses
  the app the project's `heroku` git remote points at, and on a first deploy falls
  back to the project directory name. Names are globally unique across all of
  Heroku and may only contain lowercase letters, digits, and dashes, so on a first
  deploy pick something distinctive with the developer.
- `HEROKU_TEAM` (optional, sometimes required): the Heroku team to create the
  app under. Required when the account cannot own personal apps. Leave empty for
  a personal app. Only read when the app is first created.

Pass them on the deploy command, as shown in the parent skill's Step 5.

---

## Verifying

```sh
heroku ps --app <name>                             # expect one worker dyno, state "up"
heroku logs --num 100 --app <name>                 # look for the Socket Mode connection
heroku config --app <name> | cut -d: -f1           # confirms both tokens are set, without printing them
```

Do not use `heroku logs --tail`: it streams until it is stopped, which hangs an
agent session. Do not run a bare `heroku config`: it prints the token values.

**Confirm only one dyno is running.** `heroku ps` should list `worker` at 1 and no
`web` process at all. If a `web` dyno appears, the app has two copies of itself
connected to Slack and the second one is in a restart loop. Run
`heroku ps:scale web=0 --app <name>`. The worker's own logs will not reveal this:
they look healthy either way.

**Two connections right after a first deploy are expected.** For Bolt for
JavaScript, Heroku starts a `web` dyno with the first release, before the deploy
script scales it to 0. The worker's first log line can show `num_connections: 2`
while that `web` dyno shuts down. If `heroku ps` lists only the worker, there is
one copy running.

**If the chosen plan's documentation mentions dynos sleeping**, leave the app idle
for longer than the stated period, then message it. A sleeping dyno drops the
websocket and the app goes quiet in Slack.
