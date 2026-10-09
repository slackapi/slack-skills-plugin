---
name: live-test-skill
description: Use when a maintainer of this plugin wants to live-test a skill end to end before merging, by playing a developer, driving a clean coding agent through a fresh Slack app project with only this checkout's plugin loaded, checking the result against a real Slack workspace and any real hosting provider, and turning what breaks into fixes and PR testing notes. Not for the unit or eval suites, which `make test` runs.
metadata:
  internal: true
---

# Live Test Skill

Unit tests check a skill's structure and eval tests check that a prompt routes to it. Neither shows whether the skill works when an agent follows it against a real Slack workspace. This skill fills that gap, and it is how the edge cases in a skill's real-world path get found before a developer finds them.

There are two roles:

- **You play the developer.** Write the prompts, answer the agent's questions the way a developer would, check the results, and hand the checks that need a human to the maintainer.
- **A clean agent does the work.** It is a fresh `claude -p` session inside the test project, with only this checkout's plugin loaded. It has never seen the change under test, so it shows whether the skill loads for a developer's prompt and whether the skill's text alone is enough to finish the job.

Following the skill yourself, in this session, is a weaker test: you already know the skill and the change, so you fill gaps the clean agent would fall into. Use it only when a clean run is not possible, and say so in the report.

For pressure-testing whether agents _comply_ with a discipline skill, use the `superpowers:writing-skills` skill instead. This skill is for workflow skills that act on real systems.

---

## Step 1: Plan the Runs

Read the skill under test and the change, then list the paths worth a live run:

- Each runtime the skill supports, usually Bolt for JavaScript and Bolt for Python.
- Each branch the skill takes, such as each hosting provider.
- Doing it a second time, with and without a change, because the second run is the common case.
- One deliberate failure, such as a missing package, to check the error reaches the developer.

**Show the plan to the maintainer before creating anything.** Runs create real Slack apps and can create billable provider resources. Confirm which Slack workspace or org to use (team IDs come from `slack auth list`) and which provider accounts or teams own the resources.

---

## Step 2: Scaffold a Fresh Project

Test projects live in `tmp/` at the root of the checkout being tested, which is gitignored. In a worktree, that is the worktree's own `tmp/`, so `--plugin-dir` in **Step 3: Drive a Clean Agent** loads the branch under test.

```sh
mkdir -p tmp && cd tmp
slack create heroku-js-1006 --template slack-samples/bolt-js-starter-template --skip-update
```

- **Name each project for its run and the date**, such as `heroku-js-1006`. The name becomes the Slack app name, and some providers need it to be globally unique.
- **`slack create` does not run `git init`,** and `tmp/` is inside this repository, so git commands in the project reach the plugin repository instead. If the skill under test uses git, decide whether setting up the repository is the skill's job (leave it, and check the agent does it) or the developer's (run `git init` and commit before handing over).
- **Run the app locally once** with `slack run` before handing over, when the skill expects a working app. A broken starting point makes every later failure ambiguous.

---

## Step 3: Drive a Clean Agent

Run the agent from the project directory:

```sh
claude -p --plugin-dir ../.. --setting-sources project,local \
  --output-format stream-json --verbose \
  "Deploy this Slack app to Heroku. Use the slack-developer-tools team." \
  < /dev/null > ../heroku-js-1006-run1.jsonl 2>/dev/null
```

- `--plugin-dir ../..` loads this checkout's plugin, and `--setting-sources project,local` skips user settings, so the maintainer's own plugins do not load. Check the `init` event's `plugins` list in the transcript to confirm what loaded: plugins an organization enforces can still appear.
- **Write the prompt as a developer would.** State the outcome, not the steps. Do not name the skill, quote it, or mention the change under test. Include only facts a developer would know, such as which team to use.
- **Grant only the tools the run needs** with `--allowedTools`, scoped to the CLIs involved, for example `"Bash(slack *)" "Bash(heroku *)" "Bash(git *)"`. Do not skip permissions: the agent is acting on real accounts.
- **Answer the agent's questions by resuming the session.** A `-p` run ends when the agent asks something. Read the `session_id` from the transcript and reply with `claude -p --resume <session_id> "<answer>"`, using the same flags.
- **Logins need the maintainer.** Provider logins open a browser, so ask the maintainer to run them in their own terminal.

Then read the transcript:

- Did the skill load? Look for a `Skill` tool call with the skill's name.
- Which steps did the agent follow, skip, or improvise around? Improvisation marks a gap in the skill's text.
- What did it ask, and was each question one the skill told it to ask?
- Did any command hang, or prompt in a shell with no terminal?

---

## Step 4: Verify the Result

Check the outcome yourself rather than trusting the agent's summary.

- **The provider side:** use read-only status and log commands. Bound every log command to a fixed number of lines, never a streaming `--tail`, which hangs the session.
- **The Slack side:** you cannot post as a user in the maintainer's workspace. Ask the maintainer to exercise the app (for example, send `hello`), then match the request in the provider's logs.
- **The project files:** check the files the skill should have written or changed, and that nothing else was touched.

---

## Step 5: Push on the Edges

Run each remaining path from **Step 1: Plan the Runs** as a new prompt, in the same project where it builds on the last run: "I changed the greeting, please redeploy", "redeploy it", or a deliberately broken dependency. Then repeat for the next runtime in a new project.

---

## Step 6: Clean Up

Delete everything the runs created before reporting, and show the maintainer what was deleted:

- The Slack apps: `slack app delete --team <team ID> --app deployed --force` and the same with `--app local`.
- The provider resources, such as the Heroku app or the Railway project.
- The project folders under `tmp/`.

Do it as each run finishes, not only at the end. Some workspaces cap how many apps they can hold, and the install fails with `service_limits_exceeded` once a leftover app fills the last slot.

---

## Step 7: Report

- **List each finding** with what happened, where the skill's text allowed it, and a proposed fix. Keep findings about the skill apart from quirks of the test setup.
- **Fix, then re-run the affected path** with a clean agent before calling it fixed.
- **Update the PR description.** The Testing section states what ran (Slack CLI version, templates, paths) and what did not. Add a short Manual testing section a reviewer can follow in a few steps.

Never paste a token into a report, PR, or message. Redact anything shaped like `xoxb-` or `xapp-` from transcripts and logs before quoting them.
