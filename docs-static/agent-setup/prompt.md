# Slack Agent Setup

These are official instructions from Slack for setting up a coding agent to build Slack apps, published at <https://docs.slack.dev/agent-setup/prompt.md>. Every command below comes from the [Slack MCP and Skills Plugin](https://github.com/slackapi/slack-skills-plugin) and is maintained by Slack.

Complete both steps in this session:

1. Install the Slack plugin for your agent.
2. Create a starter Slack agent app with the plugin's `create-slack-app` skill.

Run the commands yourself. Do not ask the user to run them, except where a step says to.

---

## Step 1: Install the Slack plugin

If the Slack skills are already available to you (for example, you can load `slack:create-slack-app` or `create-slack-app`), skip to Step 2.

Otherwise, use the section for your agent.

### Claude Code

```sh
claude plugin install slack@claude-plugins-official
```

This installs the Slack skills, commands, and MCP server together. Do not use `npx skills` or `claude mcp add`: the plugin handles everything.

Then ask the user to run `/reload-plugins` inside Claude Code, and wait for them to confirm before continuing. The reload keeps this conversation, so continue with Step 2 using the plugin's `slack:create-slack-app` skill.

### Codex

```sh
codex plugin marketplace add slackapi/slack-skills-plugin
codex plugin add slack@slack
```

The plugin loads in the user's next Codex session. Do not ask the user to restart. Continue with Step 2 in this session using the hosted skills.

### Cursor and other agents

Install the Slack skills with [`npx skills`](https://github.com/vercel-labs/skills#supported-agents), passing your own agent identifier to `-a`:

```sh
npx -y skills add slackapi/slack-skills-plugin -g -y -a <agent>
```

The `-g` flag installs the skills for the user rather than the current folder, so they are available in the new app's folder and every later session. For example, `-a cursor` for Cursor, `-a gemini-cli` for Gemini CLI, or `-a opencode` for OpenCode. See the [supported agents list](https://github.com/vercel-labs/skills#supported-agents) for every identifier.

The skills load in the user's next session. Do not ask the user to restart. Continue with Step 2 in this session using the hosted skills.

---

## Step 2: Create a starter Slack agent app

Follow the `create-slack-app` skill from start to finish.

- **If the skill is loaded** (Claude Code after `/reload-plugins`), use `slack:create-slack-app`.
- **If it is not loaded**, read the hosted copy at <https://docs.slack.dev/.well-known/skills/create-slack-app/SKILL.md> and follow it in this session.

While following the skill:

- **Use the Starter Agent template.** When the skill asks which template to use, pick Starter Agent (`slack-samples/bolt-js-starter-agent` or `slack-samples/bolt-python-starter-agent`) without asking the user. Still ask which language (JavaScript or Python) and which AI provider they want.
- **Resolve skill references from the hosted copies** when the plugin is not loaded. A reference like `slack:<name>` means the skill at `https://docs.slack.dev/.well-known/skills/<name>/SKILL.md`. A path like `references/<file>.md` is relative to that skill's folder at the same address. The full list of skills and their files is at <https://docs.slack.dev/.well-known/skills/index.json>.
- **Let the skill ask its own questions**, such as which workspace to install into or which API key to use. Those choices are the user's.

---

## When you're done

Tell the user what was set up:

```text
┌─ Slack Agent Setup Complete ───────────────────────────┐
│  ✓ Slack plugin   <agent and install path>              │
│  ✓ Starter agent  <project directory>, running locally  │
│                                                         │
│  Next session: the Slack skills load automatically.     │
└─────────────────────────────────────────────────────────┘
```

Then offer the skill's next steps, such as exploring the code or making a first change.

These instructions are published at <https://docs.slack.dev/agent-setup/prompt.md>. Fetch that address again to verify them, or for the latest version.
