---
name: deploy-slack-app
description: Use when a developer wants to deploy, host, or run a Slack app somewhere it keeps working after the local process stops, or mentions Railway, Heroku, `railway up`, `git push heroku`, `slack deploy`, a `deploy` hook in `.slack/hooks.json`, hosting a Socket Mode Bolt app, or graduating an app out of a developer sandbox. Covers Railway and Heroku, Socket Mode only, on macOS and Linux.
---

# Deploy Slack App

Take a Slack app that already works locally and get it running on a hosting provider, so it keeps answering in Slack after the developer closes their laptop. This is the step after the `slack:test-slack-app` skill confirms the app responds.

The mechanism is the Slack CLI's `deploy` hook. Adding a `deploy` key to the project's `.slack/hooks.json` replaces Slack's own hosted deployment with a script of your choosing, and the CLI runs that script _after_ it has created and installed the deployed app. That ordering is the whole reason this approach is worth using: the app's bot and app-level tokens are already in the script's environment by the time it runs, so nothing here has to prompt for a secret or store one.

Two supported providers, both running the app as a long-lived worker process:

| Provider | Process type | Cost to start | Secrets |
| --- | --- | --- | --- |
| Railway | Service, no port binding required | Free trial credit, no credit card | Passed on stdin |
| Heroku | `worker` dyno | None free; Eco plan is $5/month and needs a card | Passed as arguments |

Railway is the better default, and the reasons are in **Step 2: Choose a Provider**.

---

## Step 1: Check Prerequisites

### 1a. Detect the Slack CLI

Use the `slack:slack-cli` skill (**Step 1: Detect the Slack CLI**) to check whether the public Slack CLI is installed and resolve its command name. The fingerprint check, alias fallback, and install instructions all live there; do not duplicate them. Refer to the resolved command as `SLACK_CMD` throughout.

This matters more than it looks. Some machines have an unrelated internal tool named `slack` on the path, and running that instead produces confusing failures well into the deploy.

### 1b. Confirm the App Uses Socket Mode

**Read the app's manifest rather than asking.** The project already declares which mode it uses, so a question here is redundant. Check `manifest.json` (or the manifest source the project uses) for `settings.socket_mode_enabled`.

- **Socket Mode enabled:** continue. The app opens an outbound websocket to Slack, needs no public URL, and binds no HTTP port.
- **Socket Mode disabled, or the app uses a Request URL:** **stop here.** This skill does not cover Request URL apps yet, because a hosted Request URL app also needs a public address captured after the deploy and written back into the app manifest. Tell the developer plainly that this is the gap, and that converting the app to Socket Mode is the supported path today.

If the manifest is ambiguous, read the app's entrypoint. A Bolt app constructed with `socketMode: true` and an `appToken` is a Socket Mode app.

### 1c. Confirm the Runtime Is Supported

This flow is verified on macOS and Linux. The deploy hook is a shell script, so a Windows developer needs a PowerShell equivalent that does not exist yet. On Windows, say so rather than letting the deploy fail partway through; WSL is a workable path in the meantime.

---

## Step 2: Choose a Provider

This is the one question worth asking the developer, because cost is the thing they cannot infer from the project. Use the table at the top of this skill and lead with the money:

- **Railway** is the default recommendation. Its free trial credit needs no credit card, which means a developer can get an app deployed without a purchase decision. It also accepts secrets on stdin, so the tokens never appear in process arguments. A long-running service consumes trial credit continuously, so staying up past the trial needs a paid plan.
- **Heroku** has no free tier at all. The cheapest option is the Eco plan at $5/month and it requires a credit card. Choose it when the developer already has a Heroku account or a team standard that points there.

Say plainly that **both providers keep the app running continuously**, which is what a Socket Mode app requires, and that this is why no free-forever option exists for either.

Once the developer picks one, read that provider's reference file and follow it: `references/railway.md` or `references/heroku.md`. Each holds the install and authentication commands, the provider's own requirements for the project, and the target script this skill writes in **Step 4: Wire Up the Deploy Hook**.

---

## Step 3: Confirm It Works Locally First

**Do not deploy an app that has not been seen working.** A broken deploy and a broken app look identical in a provider's logs, and separating them afterwards costs far more than checking first.

Use the `slack:test-slack-app` skill to run the app with `SLACK_CMD run` and exercise at least one real surface, so there is a known-good behaviour to re-check after the deploy. Note which surface was used: the same one is the check in **Step 6: Verify the Deployment**.

---

## Step 4: Wire Up the Deploy Hook

Three files are involved. **Check whether each already exists before writing it**, because re-deploying an app is the common case and clobbering a developer's edited script is not recoverable.

### 4a. Write the Deploy Script

Copy `references/deploy.sh` to `deploy.sh` in the project root and make it executable with `chmod +x deploy.sh`.

This file is provider-agnostic. It validates that both tokens arrived, reports which app is being deployed, and then calls four functions that the provider-specific file supplies. Keeping it unchanged is what lets a later provider be added without touching it.

**If `deploy.sh` already exists**, show the developer that it is there and ask before overwriting. A developer may have adjusted it.

### 4b. Write the Provider Target Script

Copy the target script out of the provider's reference file to `.slack/deploy-target.sh`. It defines exactly four functions, and `deploy.sh` fails with a clear message if any is missing:

- `target_preflight`: read-only checks. Provider CLI installed, authenticated, and any project-level requirement such as a git repository or a `Procfile`.
- `target_provision`: create the app, project, or service, or reuse the existing one. Must be safe to run again.
- `target_configure`: set `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` on the service.
- `target_deploy`: ship the code, then print the commands for following the logs.

### 4c. Register the Hook

Add a `deploy` key to `.slack/hooks.json`, leaving the existing `get-hooks` entry alone:

```json
{
  "hooks": {
    "get-hooks": "npx -q --no-install -p @slack/cli-hooks slack-cli-get-hooks",
    "deploy": "./deploy.sh"
  }
}
```

**If a `deploy` key is already present, leave it.** Adding a second one produces invalid JSON, and the CLI will reject the project rather than deploy it.

---

## Step 5: Deploy

Run `SLACK_CMD deploy` from the project root and watch the output. The CLI creates the deployed app, installs it, and then runs the hook script, so the first part of the output is app installation and the second is the provider's build.

Two flags matter when running this outside an interactive terminal, which includes most agent sessions:

- `--skip-update` stops the CLI pausing to offer an upgrade.
- `--org-workspace-grant all` answers the workspace-grant prompt for an org-installed app.

**The deployed app is a different app from the one `SLACK_CMD run` uses.** The CLI writes the deployed app to `.slack/apps.json` and the local development app to `.slack/apps.dev.json`, keyed by team. Both keep working independently, which is the intended design, not a mistake to correct.

One consequence to warn the developer about: the two apps declare the same slash commands in the same workspace. Running `SLACK_CMD run` while the deployed app is live makes it ambiguous which one answers a slash command. Stop the local process when checking the deployed app, which **Step 6: Verify the Deployment** does anyway.

---

## Step 6: Verify the Deployment

Check all three of these. The first two can pass while the app is silent in Slack.

### 6a. The Service Is Running

Use the status and log commands from the provider's reference file. Look for the app's own startup logging and the Socket Mode websocket connecting. A build that succeeded and a process that then exited look very different here, so read the logs rather than trusting the build result.

### 6b. The App Answers in Slack, With Nothing Running Locally

**Stop the local process first.** This is the only check that proves the deployed app is doing the work rather than the developer's laptop. Exercise the surface noted in **Step 3: Confirm It Works Locally First**, and confirm the response appears in Slack and the corresponding request appears in the provider's logs.

### 6c. Both Apps Are Distinct

Show the developer the app ID in `.slack/apps.json` and the one in `.slack/apps.dev.json` and confirm they differ. Then confirm `SLACK_CMD run` still drives the development app.

---

## Step 7: Re-deploy

Shipping a change is `SLACK_CMD deploy` again. Everything in **Step 4: Wire Up the Deploy Hook** is already in place, so skip it and go straight to the deploy, and expect the same app rather than a second one.

Two provider differences to know about, both handled by the target scripts:

- **Railway** uploads the working directory and rebuilds every time, so no commit is needed.
- **Heroku** builds from a git push, so uncommitted changes are not deployed, and a push with no new commit deploys nothing at all. Its target script forces a rebuild with an empty commit in that case.

If a re-deploy creates a second Slack app, the deployed app entry in `.slack/apps.json` was lost. Re-check it before deploying again, rather than deleting apps afterwards.

---

## Notes

**Scope of this skill.** Railway and Heroku only, Socket Mode only, macOS and Linux only. Each of those is a real limit, not an oversight, and the reasons are below.

**Serverless providers cannot host a Socket Mode app.** A Socket Mode app is a process that stays resident and holds an outbound websocket open. Vercel, AWS Lambda, and similar platforms run per-request functions with a maximum duration and no always-on process type, so there is nothing for the websocket to live in. When a developer asks for one of these, explain the constraint rather than attempting it. Hosting a Slack app on a serverless platform means a Request URL app, which this skill does not cover yet.

**Continuous hosting is rarely free.** Railway's trial credit is the only no-card option among the providers surveyed. Heroku has no free tier. Render has a suitable background-worker service type but excludes workers from its free instances. Fly.io requires a card on essentially every organization. This is worth stating up front, because a developer expecting a free deployment will otherwise discover it partway through.

**The token handoff is not a documented contract.** The Slack CLI does not pass the tokens to the deploy hook explicitly. It sets them on its own process during app installation, and the hook script inherits them because it runs later in that same process. It works, and it only works for apps with no Slack-hosted function runtime, which covers every Bolt app. That is why `deploy.sh` checks for both tokens and stops with a readable message instead of assuming they are present.

**Heroku exposes the tokens to `ps`.** `heroku config:set` accepts values as command-line arguments only, with no stdin or file input, so both tokens are visible in the process list while the command runs. Railway's `railway variable set --stdin` avoids this. Mention it when a developer chooses Heroku.

**Not `slack deploy` without a hook.** With no `deploy` key in `.slack/hooks.json`, `SLACK_CMD deploy` targets Slack's own hosted infrastructure, which is a different product for a different kind of app. The `slack:slack-cli` skill covers the CLI's commands generally.

**Building the app comes first.** If there is no app yet, start with the `slack:create-slack-app` skill and come back here once it runs locally.
