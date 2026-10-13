# Slack MCP and Skills Plugin

A [Claude Code][claude-code], [Cursor][cursor], [Codex][codex-cli], and [OpenCode][opencode] plugin that brings Slack into your AI tools with a [Slack MCP Server][slack-mcp-docs] and set of Slack skills for both users and developers.

[![CI Build](https://github.com/slackapi/slack-skills-plugin/actions/workflows/ci-build.yml/badge.svg)](https://github.com/slackapi/slack-skills-plugin/actions/workflows/ci-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Installation

### Claude Code

The plugin is published on the [official Claude marketplace](https://claude.com/plugins/slack). Install it from inside Claude Code:

```text
/plugin install slack@claude-plugins-official
```

The Slack MCP server is configured automatically. You'll be prompted to authenticate to your Slack workspace via OAuth on first use.

### Cursor

The plugin is published on the [official Cursor Marketplace](https://cursor.com/marketplace/slack). Install it from inside Cursor:

```text
/add-plugin slack
```

This installs the skills, commands, and MCP server together. You'll be prompted to authenticate to your Slack workspace via OAuth on first use.

### OpenCode

The plugin supports OpenCode 2 and OpenCode 1 (1.18.29 or newer). Add the
git-backed plugin to your OpenCode config:

```json
{
  "plugins": [
    "slack@git+https://github.com/slackapi/slack-skills-plugin.git"
  ]
}
```

OpenCode 1 configs use the singular `plugin` key with the same value.

The plugin keeps the root `skills/` and `commands/` directories authoritative and
registers eight skills, five `slack-*` commands, and the remote Slack MCP server
in memory. It does not install, copy, or rewrite project files. Registration is
idempotent. If your config already defines a `slack` MCP server, the plugin
preserves it and does not replace it.

One package serves both OpenCode generations:

- OpenCode 2 loads the default export's `setup`, which registers skills,
  commands, and MCP through the V2 skill, command, and MCP transforms.
- OpenCode 1 calls the same export's `server()`, which returns the native
  `config` hook.

#### Configure an eligible Slack app

OpenCode currently requires an eligible internal Slack app that you own or
administer. Slack MCP also supports directory-published apps; unlisted apps are
not eligible. Configure an internal app as follows:

1. In **OAuth & Permissions**, add the user scopes required by the Slack MCP
   tools you plan to use:
   - Search: `search:read.public`, `search:read.private`, `search:read.mpim`,
     `search:read.im`, `search:read.files`, `search:read.users`, `files:read`,
     and `emoji:read`.
   - Messages: `chat:write`, `channels:history`, `groups:history`,
     `mpim:history`, `im:history`, and `reactions:write`.
   - Conversations: `channels:write`, `groups:write`, `im:write`,
     `mpim:write`, `channels:read`, `groups:read`, and `mpim:read`.
   - Canvases and profiles: `canvases:read`, `canvases:write`, `users:read`,
     and `users:read.email`.
2. Enable [PKCE][slack-pkce]. This marks the app as a public OAuth client and is
   a one-way operation; disabling it requires contacting Slack support.
3. Register the exact redirect URL
   `http://127.0.0.1:19876/mcp/oauth/callback`.
4. Open the app's **App Assistant** (`app-assistant`) page and enable Slack MCP
   server access **before** authenticating from OpenCode.
5. Ask a workspace admin to approve the app and its requested MCP access.

Slack does not support dynamic client registration, so export the app's client
ID, then start OpenCode:

```sh
export SLACK_OPENCODE_CLIENT_ID="your-app-client-id"
opencode
```

In the session, run `/mcps`, select `slack`, and sign in. `opencode mcp list`
should then report Slack as connected. If you authenticated before enabling MCP
server access, run `opencode mcp logout slack` and sign in again.

`SLACK_OPENCODE_CLIENT_ID` is read through the config value
`{env:SLACK_OPENCODE_CLIENT_ID}`. Never commit a client ID, client secret, or
token. No client secret is needed for this PKCE flow.

The plugin registers Slack MCP as the OpenCode 2 server below (OpenCode 1
receives the same values as `clientId` and `redirectUri`):

```json
{
  "mcp": {
    "servers": {
      "slack": {
        "type": "remote",
        "url": "https://mcp.slack.com/mcp",
        "oauth": {
          "client_id": "{env:SLACK_OPENCODE_CLIENT_ID}",
          "redirect_uri": "http://127.0.0.1:19876/mcp/oauth/callback",
          "callback_port": 19876
        }
      }
    }
  }
}
```

#### Use the skills and commands

OpenCode discovers these eight skills:

- `block-kit`
- `create-slack-app`
- `slack-api`
- `slack-cli`
- `slack-docs`
- `slack-messaging`
- `slack-search`
- `test-slack-app`

Skills load on demand. For example, prompt OpenCode with "Use the `slack-search`
skill to find discussions about the launch" or "Use the `block-kit` skill to
draft a feedback modal."

OpenCode also discovers exactly five namespaced commands:

- `/slack-channel-digest <channel1, channel2, ...>`
- `/slack-draft-announcement <topic>`
- `/slack-find-discussions <topic>`
- `/slack-standup`
- `/slack-summarize-channel <channel-name>`

For example, run `/slack-summarize-channel engineering` in an OpenCode session.
The `slack-*` namespace avoids collisions with generic project commands.

**Advanced: bearer-token fallback.** If your eligible app already issued a user
token with the required Slack MCP scopes, define your own `slack` MCP server
with:

```json
"oauth": false,
"headers": {
  "Authorization": "Bearer {env:SLACK_MCP_TOKEN}"
}
```

Set `SLACK_MCP_TOKEN` to that app-issued scoped user token. OpenCode will not run
OAuth or manage token refresh in this mode.

### Codex

The plugin is published as a Codex marketplace in this repository. Add the marketplace, then install the plugin:

```sh
codex plugin marketplace add slackapi/slack-skills-plugin
codex plugin add slack@slack
```

Start a new Codex session to pick up the plugin, then invoke a skill by name with a `$` mention, for example `$block-kit`.

Codex support currently ships the skills only; the MCP server is not yet wired into the Codex surface.

### Other agents

The skills install into other coding agents with [`npx skills`][npx-skills], no plugin marketplace required:

```bash
# Install the skills for a coding agent, named by its own identifier
npx skills add slackapi/slack-skills-plugin -y -a <agent>

# For example, Gemini CLI or OpenCode
npx skills add slackapi/slack-skills-plugin -y -a gemini-cli
npx skills add slackapi/slack-skills-plugin -y -a opencode
```

Other popular agents include `crush`, `devin`, `hermes-agent`, `openclaw`, and `pi`. See [supported agents][npx-skills] for the full list of agents and their identifiers. Add `-g` to install for your user instead of the current project.

The `-y` flag installs every skill without prompting. Drop it to choose skills from a list, or pass `-s <skill>` to name the ones you want.

This path carries the skills only: no commands, and no MCP server.

## Features

### MCP Server

The plugin connects your AI tool to Slack's hosted [MCP server][slack-mcp-docs]:

- **Search** - find messages, files, users, and channels (public and private)
- **Messaging** - send and schedule messages, read channels, follow threads, add reactions
- **Canvas** - create, read, and update canvas documents
- **Users** - read profiles and list channel members

### Skills

Eight skills load on demand to handle messaging tasks and developer workflows:

- [`slack:slack-messaging`](skills/slack-messaging/SKILL.md) - composing well-formatted, effective Slack messages
- [`slack:slack-search`](skills/slack-search/SKILL.md) - finding messages, files, channels, and people
- [`slack:slack-api`](skills/slack-api/SKILL.md) - discovering and calling Slack Web API methods
- [`slack:slack-cli`](skills/slack-cli/SKILL.md) - using the [Slack CLI][slack-cli] to create, run, and manage apps
- [`slack:slack-docs`](skills/slack-docs/SKILL.md) - searching and reading current Slack platform documentation
- [`slack:create-slack-app`](skills/create-slack-app/SKILL.md) - building a Slack app or agent with the CLI and [Bolt][bolt]
- [`slack:block-kit`](skills/block-kit/SKILL.md) - building and validating [Block Kit][block-kit] layouts
- [`slack:test-slack-app`](skills/test-slack-app/SKILL.md) - running an existing Slack app somewhere safe and confirming it works in Slack

### Commands

Five slash commands for common Slack workflows:

- `/slack:summarize-channel <channel-name>` - Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` - Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` - Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` - Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` - Get a digest of recent activity across multiple Slack channels

## Usage examples

Once installed, talk to your tool in natural language:

- "Search for messages about the product launch from the last week"
- "Send a message to #general saying the deployment is complete"
- "Summarize the last day of activity in #engineering"
- "Draft an announcement about the new pricing page"
- "Create a new Slack app using Bolt for Python"
- "Build a Block Kit feedback modal with a rating select and a comments field"
- "Validate the Block Kit JSON in ./modal.json"

## Documentation

- [Slack MCP server][slack-mcp-docs]
- [Slack developer docs](https://docs.slack.dev/)
- [Block Kit Builder][block-kit]

## Limitations

- **Workspace admin approval.** Your Slack workspace admin must approve MCP integration before you can authenticate.

## Contributing

We welcome contributions from everyone! Please check out our [contributor's guide](.github/contributing.md) for guidelines on opening issues and pull requests.

Working on the plugin itself? See the [maintainer's guide](.github/maintainers_guide.md) for local development setup.

[claude-code]: https://claude.com/claude-code
[cursor]: https://cursor.com
[opencode]: https://opencode.ai
[codex-cli]: https://developers.openai.com/codex/cli
[slack-mcp-docs]: https://docs.slack.dev/ai/mcp-server/
[slack-pkce]: https://docs.slack.dev/authentication/using-pkce
[npx-skills]: https://github.com/vercel-labs/skills#supported-agents
[slack-cli]: https://tools.slack.dev/slack-cli
[bolt]: https://tools.slack.dev/bolt-js
[block-kit]: https://app.slack.com/block-kit-builder
