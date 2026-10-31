# Railway

Railway runs the app as a long-lived service built from the uploaded working
directory. It suits a Socket Mode app well: the service binds no HTTP port, and
Railway does not require one.

The deploy script for this provider is `deploy-railway.sh`, alongside this file.
Copy it to `.slack/deploy-railway.sh` as described in the parent skill's Step 4.

**Cost.** Current pricing is at <https://railway.com/pricing>. Point the developer
there rather than quoting or fetching it. Railway bills by resource usage, so a
long-running service costs something for every hour it is up.

---

## Install and authenticate

```sh
brew install railway          # macOS; see https://docs.railway.com/guides/cli
railway whoami                # confirms the CLI is authenticated
```

If `railway whoami` fails, ask the developer to run `railway login` in their own
terminal. It opens a browser, so it cannot complete inside an agent session. For
a headless setup, export `RAILWAY_API_TOKEN` with an account token. A
project-scoped `RAILWAY_TOKEN` cannot create projects, so it is not enough for a
first deploy.

---

## What Railway needs from the project

No `Procfile`, `Dockerfile`, or config file. Railway's builder detects the
language and picks a start command, so check that it will pick the right one:

- **Bolt for JavaScript:** it runs `npm start`, so `package.json` needs a
  `scripts.start` entry that starts the app.
- **Bolt for Python:** it runs the first of `main.py`, `app.py`, `start.py`, or
  `bot.py` that exists. The Bolt templates use `app.py`, which works unless a
  `main.py` is also present. For any other entrypoint, set a start command in a
  `railway.json` file (see <https://docs.railway.com/reference/config-as-code>).

---

## Environment variables

- `RAILWAY_PROJECT_NAME` (optional): the Railway project name. Defaults to the
  project directory name.
- `RAILWAY_SERVICE_NAME` (optional): the Railway service name. Defaults to the
  project directory name.
- `RAILWAY_WORKSPACE` (optional, sometimes required): the workspace to create the
  project in. Required when the account belongs to more than one workspace,
  because `railway init` otherwise prompts, and the prompt fails in a deploy
  hook. `railway whoami --json` lists the account's workspaces. If there is more
  than one, ask the developer which to use.

Pass them on the deploy command, as shown in the parent skill's Step 5.

---

## Verifying

```sh
railway service status --service <name>           # deployment state
railway logs --service <name> --lines 100         # look for the Socket Mode connection
railway logs --build --service <name> --lines 100 # build output, if the build failed
```

Always pass `--lines`. Without it `railway logs` streams until it is stopped,
which hangs an agent session.

**Two connections right after a re-deploy are expected.** Railway starts the new
deployment before removing the old one, so the new one's logs can show
`"num_connections":2` for a moment. `railway deployment list --service <name>`
should then show the new deployment as `SUCCESS` and the old one as `REMOVED`.
If two deployments stay `SUCCESS`, two copies of the app are connected to Slack.

Expect the build to take a few minutes on the first deploy. Railway injects a
`PORT` variable even when nothing listens on it, which is harmless for a Socket
Mode app.

## Tearing down

Read the project name from `railway status`, then delete the project and unlink
the directory:

```sh
railway status                                  # shows the linked project
railway delete --project <name> --yes
railway unlink --yes
```

Railway stops the service right away but schedules the project's removal for
later, so the project stays in `railway list` for a while. `railway list --json`
shows the scheduled date as `deletedAt`. The project being listed does not mean
the delete failed.
