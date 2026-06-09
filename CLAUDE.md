# Slack Plugin

This plugin integrates Slack with Claude Code, providing tools to search, read, and send messages in Slack.

## Commands

- `/slack:summarize-channel <channel-name>` — Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` — Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` — Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` — Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` — Get a digest of recent activity across multiple Slack channels

## Skills

- **slack-messaging** — Guidance for composing well-formatted Slack messages using standard markdown
- **slack-search** — Guidance for effectively searching Slack to find messages, files, channels, and people

## Emoji Reactions

The `slack-reactions` MCP server adds `slack_add_reaction` and `slack_remove_reaction` tools. It runs as a local subprocess and calls the Slack Web API directly.

### Tools

- **slack_add_reaction** — Add an emoji reaction to a message (`channel_id`, `message_ts`, `emoji_name`)
- **slack_remove_reaction** — Remove an emoji reaction from a message (`channel_id`, `message_ts`, `emoji_name`)

### Setup

Requires a Bot User OAuth Token (`xoxb-...`) with the `reactions:write` scope. Set it in `.mcp.json`:

```json
"slack-reactions": {
  "command": "npx",
  "args": ["tsx", "./src/reactions.ts"],
  "env": {
    "SLACK_BOT_TOKEN": "xoxb-your-token-here"
  }
}
```

Install dependencies first: `npm install`
