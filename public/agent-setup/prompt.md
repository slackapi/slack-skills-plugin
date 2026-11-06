# Slack Agent Setup

These are official instructions from Slack for setting up a coding agent to build Slack apps, published at [https://docs.slack.dev/agent-setup/prompt.md](https://docs.slack.dev/agent-setup/prompt.md). Every command below comes from the [Slack MCP and Skills Plugin](https://github.com/slackapi/slack-skills-plugin) and is maintained by Slack.

Complete both steps in this session:

1. Install the Slack plugin for your agent, or update it.
2. Create a Slack app with the plugin's `create-slack-app` skill: a new starter agent, or the existing app named in your arguments.

Run the commands yourself. Do not ask the user to run them, except where a step says to.

## Arguments

The message that sent you here may end with arguments, for example `using --app A0123456789 --template bolt-starter-agent --team T0123456789`. App Settings adds them after the developer creates and installs an app there.

- `--app`: the ID of an app that already exists. Set up a project for this app instead of creating a new one.
- `--template`: the template the app was created from. App Settings sends a template name without a language, like `bolt-starter-agent`.
- `--team`: the workspace or Enterprise org the app is installed in.

They are inputs for Step 2, not a command to run as written. With no arguments, Step 2 creates a new starter agent.

### Choose the template repo

The Slack CLI needs a template repo, not an App Settings template name, so turn the name into one before Step 2:

1. Ask the user which language they want: JavaScript or Python.
2. Look up the repo for the name and language:

| Template name | JavaScript | Python |
|---------------|------------|--------|
| `bolt-starter-template` | `slack-samples/bolt-js-starter-template` | `slack-samples/bolt-python-starter-template` |
| `bolt-starter-agent` | `slack-samples/bolt-js-starter-agent` | `slack-samples/bolt-python-starter-agent` |
| `bolt-support-agent` | `slack-samples/bolt-js-support-agent` | `slack-samples/bolt-python-support-agent` |
| `bolt-custom-step-template` | `slack-samples/bolt-js-custom-step-template` | `slack-samples/bolt-python-custom-step-template` |
| `bolt-blank-template` | `slack-samples/bolt-js-blank-template` | `slack-samples/bolt-python-blank-template` |

If `--template` is already a repo (`org/repo`), use it as-is. If it is a name that isn't in the table, tell the user and offer the starter template in their language.

---

## Step 1: Install or update the Slack plugin

Use the section for your agent, even if the Slack skills are already available to you. An older install can be missing steps that these instructions rely on, so update it to the latest version.

### Claude Code

```sh
claude plugin marketplace add slackapi/slack-skills-plugin
claude plugin install slack@slack
```

If `claude plugin list` shows `slack@claude-plugins-official`, uninstall it first. Its updates are experiencing large delays, and both copies stay enabled if both are installed:

```sh
claude plugin uninstall slack@claude-plugins-official
```

This installs the Slack skills, commands, and MCP server together. Do not use `npx skills` or `claude mcp add`: the plugin handles everything.

If the plugin is already installed, update it instead:

```sh
claude plugin marketplace update slack
claude plugin update slack@slack
```

The plugin loads in the user's next Claude Code session, or after they run `/reload-plugins`. Do not wait for either. Continue with Step 2 in this session using the hosted skills.

### Codex

```sh
codex plugin marketplace add slackapi/slack-skills-plugin
codex plugin add slack@slack
```

If the plugin is already installed, update it instead:

```sh
codex plugin marketplace upgrade slack
codex plugin add slack@slack
```

The plugin loads in the user's next Codex session. Do not ask the user to restart. Continue with Step 2 in this session using the hosted skills.

### Cursor and other agents

Install the Slack skills with [`npx skills`](https://github.com/vercel-labs/skills#supported-agents), passing your own agent identifier to `-a`:

```sh
npx -y skills@latest add slackapi/slack-skills-plugin -g -y -a <agent>
```

The `-g` flag installs the skills for the user rather than the current folder, so they are available in the new app's folder and every later session. If the skills are already installed, the same command replaces them with the latest version. For example, `-a cursor` for Cursor, `-a gemini-cli` for Gemini CLI, or `-a opencode` for OpenCode. See the [supported agents list](https://github.com/vercel-labs/skills#supported-agents) for every identifier.

The skills load in the user's next session. Do not ask the user to restart. Continue with Step 2 in this session using the hosted skills.

---

## Step 2: Create the Slack app

Read the hosted copy of the `create-slack-app` skill at [https://docs.slack.dev/.well-known/skills/create-slack-app/SKILL.md](https://docs.slack.dev/.well-known/skills/create-slack-app/SKILL.md) and follow it from start to finish in this session.

Use the hosted copy even if a `create-slack-app` skill is already loaded. The hosted skills are published with these instructions, so they always match them. A loaded copy can be from an older install.

While following the skill:

- **With `--app`, set up the existing app.** Pass `--app`, `--team`, and the template repo you chose above to the skill, and follow its existing app path. The skill skips choosing a workspace, a language, and a template, and links the project to the app. It still asks which AI provider to use for an agent template.
- **Without `--app`, use the Starter Agent template.** When the skill asks which template to use, pick Starter Agent (`slack-samples/bolt-js-starter-agent` or `slack-samples/bolt-python-starter-agent`) without asking the user. Still ask which language (JavaScript or Python) and which AI provider they want.
- **Resolve skill references from the hosted copies** too. A reference like "the `<name>` skill", or `slack:<name>` in older copies, means the skill at `https://docs.slack.dev/.well-known/skills/<name>/SKILL.md`. A path like `references/<file>.md` is relative to that skill's folder at the same address. The full list of skills and their files is at [https://docs.slack.dev/.well-known/skills/index.json](https://docs.slack.dev/.well-known/skills/index.json).
- **Let the skill ask its own questions**, such as which workspace to install into or which API key to use. Those choices are the user's.

---

## When you're done

Tell the user what was set up:

```text
┌─ Slack Agent Setup Complete ───────────────────────────┐
│  ✓ Slack plugin   <agent and install path>              │
│  ✓ Slack app      <project directory>, running locally  │
│                                                         │
│  Next session: the Slack skills load automatically.     │
└─────────────────────────────────────────────────────────┘
```

Then offer the skill's next steps, such as exploring the code or making a first change.

These instructions are published at [https://docs.slack.dev/agent-setup/prompt.md](https://docs.slack.dev/agent-setup/prompt.md). Fetch that address again to verify them, or for the latest version.
