---
name: test-slack-app
description: Use when a developer wants to test, try out, smoke-test, verify, or confirm that a Slack app built with the Slack CLI (or a plain Bolt app) actually works, by running it in a developer sandbox or a Free Team, never a workspace with real users, with `slack run` and exercising its real slash commands, shortcuts, events, actions, modals, App Home, and assistant surfaces, or a Deno Slack SDK app's workflows, functions, and triggers (`slack trigger create`, `deno task test`). Also covers `slack doctor` and `slack manifest validate` health checks before hands-on testing.
---

# Test Slack App

Help a developer confirm that a Slack app they already built actually works. This is the last step of the build loop, after the `create-slack-app` skill scaffolds an app and the `slack-cli` skill runs it.

The approach is simple and safe:

1. **Run the app in a developer sandbox or a Free Team:** a sandbox for preference, or a Free Team the developer created for this. Never a workspace with real coworkers in it.
2. **Read the app's source** to learn what it actually listens for.
3. **Hand the developer concrete steps** to perform in Slack, then help them confirm the app responds.

This is guided manual checking, not an automated test suite: you drive the setup and tell the developer what to type or click, and they confirm what they see. It works best for apps managed by the Slack CLI; there is a best-effort path for plain Bolt apps in Step 2.

---

## Step 1: Set Up a Safe Place to Test

### 1a. Detect the Slack CLI

Load the `slack-cli` skill (with your skill tool, if you have one) before running any command, and follow its **Step 1: Detect the Slack CLI** to check whether the public Slack CLI is installed and resolve its command name. Don't check for the CLI yourself first: a `slack` on `PATH` isn't always the public CLI, and that step tells them apart. The fingerprint check, alias fallback, and install instructions all live there; do not duplicate them here. Refer to the resolved command as `SLACK_CMD` throughout. If the CLI is not installed, guide the developer through that same step to install it, since running the app needs it.

### 1b. Make sure there is a safe workspace to test in

Testing belongs in a workspace nobody is working in: a developer sandbox for preference, or a Free Team the developer created for this. Never a workspace with real coworkers in it.

- **Explain it from the live docs, not from here.** Use the `slack-docs` skill to fetch and summarize <https://docs.slack.dev/tools/developer-sandboxes.md>, so the recommendation always reflects the current docs rather than a copy that drifts out of date. Tell the developer that Slack recommends a sandbox for building and testing apps.
- **Find the current target.** Run `SLACK_CMD auth list` for the authenticated workspaces and their team IDs, and, from the project directory, `SLACK_CMD app list` for the apps already installed and their IDs.
- **Confirm the target is safe.** The CLI cannot tell a sandbox, a Free Team, and a workspace full of real users apart, so ask the developer which one they are pointed at. A sandbox or a Free Team they created for this is fine. A workspace with coworkers in it is not: stop and get them onto one of the other two.
- **A Deno Slack SDK app needs a developer sandbox or a paid plan.** A project is a Deno Slack SDK app when its `.slack/hooks.json` runs `deno_slack_hooks`, or its `deno.json` or `deno.jsonc` imports `deno-slack-sdk`. Slack requires a paid plan for workflow apps, so a Free Team won't work. Steer the developer to a sandbox, per <https://docs.slack.dev/tools/deno-slack-sdk/guides/deploying-to-slack.md>.
- **If there is no safe target yet**, set one up with the `create-slack-app` skill (**Step 3: Choose Where to Install the App**), which owns the ranked targets, the `sandbox list` / `sandbox create` flow, and the Developer Program links. Either path finishes in the browser, so have the developer come back here once the workspace exists and they have logged into it.

### 1c. Quick health check

Catch obvious setup problems with the CLI's own validation before the slower hands-on checks:

- `SLACK_CMD doctor`: checks the CLI, language runtime, and authentication.
- `SLACK_CMD manifest validate`: run from the project directory if the app has a manifest, to confirm the app configuration is well-formed.

For a Deno Slack SDK app (spotted as **1b. Make sure there is a safe workspace to test in** describes), also run the project's own tests. If `deno.json` or `deno.jsonc` defines a `test` task, run `deno task test`. The Deno samples' function tests use `SlackFunctionTester` with a stubbed `fetch`, so they need no workspace. With no `test` task, run `deno test --allow-read` if the project has `*_test.ts` files.

Surface anything these flag before moving on.

---

## Step 2: Run the App

Whichever path you use below, first turn the app's log level up to debug so you have the most context while testing. Prefer a way that leaves the developer's code untouched: read the logger setup to see whether it reads a log-level environment variable (some templates wire one such as `SLACK_LOG_LEVEL` or `LOG_LEVEL`). If it does, set that variable instead of editing source. For a CLI-managed app, `SLACK_CMD env set <LOG_LEVEL_VAR> debug` stores it in the project `.env` that `slack run` reads; for a plain Bolt app, set it in the environment or `.env` the app already reads. Only when the logger reads no such variable should you edit the source, finding where the log level is set and switching it to debug for this run.

### CLI-managed apps (recommended)

Follow **Step 6: Running an App Locally (`slack run`)** in the `slack-cli` skill to start the local dev server in the background. This also installs the app into the target workspace, which matters for a fresh sandbox or Free Team where nothing is installed yet. Once it is running, file changes auto-reload.

For a Deno Slack SDK app, there is usually no log-level variable to set. Pass `--activity-level debug` to `SLACK_CMD run` instead, which shows the app's activity logs, including `console.log` output from functions, at debug level. The local run also offers to create triggers, which a background shell cannot answer, so add `--hide-triggers` and create them in **3a. Read the source to find what the app listens for**.

### Plain Bolt apps without the CLI (best-effort)

If the app is a plain Bolt app started with `node` or `python` rather than the Slack CLI, this skill can still help, but the run path is best-effort and not the primary flow:

- Point the app at the test workspace: set its bot and app-level tokens (from that workspace's app settings) in the environment or the `.env` file the app reads.
- Prefer socket mode so the app needs no public URL. This works only if the app is coded for socket mode and the app-level token has `connections:write`; adding tokens to an app scaffolded for HTTP will not deliver events.
- Start the app with its own command (for example `npm start` or `python app.py`) and watch its logs.

Say plainly that this path is best-effort, and that the smoothest experience comes from a CLI-managed app.

---

## Step 3: Try It Out in Slack and Confirm It Works

This is the heart of the skill. Do not hand the developer a generic checklist. Ground every step in what _this_ app actually registers.

### 3a. Read the source to find what the app listens for

Read the app's listener code and list the interactions it registers. Depending on the framework these look like:

- **[Slash commands](https://docs.slack.dev/interactivity/implementing-slash-commands.md):** a registered command name such as `/ship`.
- **[Shortcuts](https://docs.slack.dev/interactivity/implementing-shortcuts.md):** global or message shortcuts with a callback ID.
- **[Events](https://docs.slack.dev/apis/events-api.md):** subscribed events such as `app_mention`, `message`, or `reaction_added`.
- **[Actions](https://docs.slack.dev/interactivity/handling-user-interaction.md):** interactive components (buttons, selects) with an action ID.
- **[View submissions](https://docs.slack.dev/surfaces/modals.md):** modal submit handlers (`view_submission`).
- **[App Home](https://docs.slack.dev/surfaces/app-home.md):** an `app_home_opened` handler or a published Home tab.
- **[Assistant / agent](https://docs.slack.dev/ai.md):** an assistant or `assistant_thread_started` handler, common in the agent templates.

For a Deno Slack SDK app, read these instead:

- **Workflows:** the `workflows` listed in `manifest.ts`, and the steps each one runs in `workflows/`.
- **Functions:** each `DefineFunction` in `functions/`, its inputs and outputs, and the Slack API calls or datastore writes it makes.
- **Triggers:** each file in `triggers/` and its `type`: shortcut (a link trigger), event, scheduled, or webhook. Triggers are not created when the app is installed. First run `SLACK_CMD trigger list --app local --team <team ID> --limit 50` to see the triggers that already exist (the list shows 4 unless `--limit` is set). Check each file for placeholder values, such as a sample channel ID or a `start_time` already in the past. For a file with no trigger yet, run `SLACK_CMD trigger create --trigger-def triggers/<file>.ts --app local --team <team ID>`. For one that already has a trigger, run `SLACK_CMD trigger update --trigger-id <trigger ID> --trigger-def triggers/<file>.ts --app local --team <team ID>`, so the test uses the file as it is now rather than a second copy. For an Enterprise organization, ask the developer which workspace the trigger is for, or whether all of them, and add `--org-workspace-grant <workspace ID>` or `--org-workspace-grant all`. Never choose `all` yourself. Triggers created for the local app do not carry over to a deployed app.

Name the concrete identifiers you find (the actual command and callback names), not placeholders.

### 3b. Turn each into a "do this, expect that" step

For every registered interaction, give the developer a concrete step and what a working app should do in response. A few spots are non-obvious, so spell them out:

- **Slash command** → type the command (for example `/ship`) in a channel or DM in the test workspace → expect the response the handler sends.
- **Global shortcut** → open the shortcuts menu (the lightning-bolt or `+` button in the message composer, depending on your client) and pick it → expect the modal or message it opens.
- **Message shortcut** → hover a message, open **More actions** (the `⋯` menu), pick the shortcut → expect its response.
- **Event** such as `app_mention` → @-mention the app in a channel it belongs to → expect its reply.
- **Button or select** → click the component in a message or modal the app posted → expect what the action handler does.
- **Modal submit** (`view_submission`) → submit the modal → expect the confirmation or side effect.
- **App Home** → click the app in the left sidebar to open its **Home** tab → expect the published view.

For a Deno Slack SDK app, each step starts a workflow from one of its triggers:

- **Link (shortcut) trigger** → open the shortcut URL that `trigger create` printed, or paste it into a channel and click the button it unfurls into → expect the workflow's first step, such as its form.
- **Event trigger** → cause the event in a channel the trigger watches, such as posting a message or adding a reaction → expect the workflow to run.
- **Scheduled trigger** → read its `schedule` (`start_time` and `frequency`) in the trigger file and wait for that time → expect the workflow to run at that time.
- **Webhook trigger** → send a POST request with a flat JSON body to the URL that `trigger create` printed → expect the workflow to run with those inputs.
- **Each function** → after the workflow runs, confirm the side effect the function's code makes, such as a message posted or a datastore item written.

### 3c. Confirm and report

While the developer interacts, help them confirm it is working:

- If the app runs under `slack run`, watch its logs (ask "show me the output from slack run") to confirm events arrive and to read any errors. For a Deno Slack SDK app, the same output shows each workflow step and function execution.
- If a response looks wrong (a malformed message or Block Kit view, or an API error), use the `block-kit` and `slack-api` skills to dig into the payload or method.

Close with a short summary: what you and the developer confirmed working, and what they should eyeball themselves. Remember this is manual checking: you are helping the developer watch the app respond, not producing an automated pass or fail.

---

## Notes

- `SLACK_CMD` is a placeholder: always substitute the actual command name resolved in Step 1a.
- Scope: this skill tests an app that already exists. To create or scaffold one, use the `create-slack-app` skill; for raw CLI mechanics, use the `slack-cli` skill; for message or Block Kit formatting, use the `slack-messaging` and `block-kit` skills.
- Out of scope for now: automated test frameworks for Bolt, programmatically simulating user interactions, and driving the Slack UI with a browser. Today the developer performs the interactions; this skill makes sure they know exactly what to do and what to expect.
