# Slack Plugin

This plugin integrates Slack with Claude Code, providing tools to search, read, and send messages in Slack. It also includes a **channel server** for real-time bidirectional Slack messaging via Socket Mode.

## Commands

- `/slack:summarize-channel <channel-name>` — Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` — Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` — Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` — Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` — Get a digest of recent activity across multiple Slack channels

## Skills

- **slack-messaging** — Guidance for composing well-formatted Slack messages using standard markdown
- **slack-search** — Guidance for effectively searching Slack to find messages, files, channels, and people

## Channel Server (Research Preview)

The `slack-channel` MCP server enables real-time Slack messaging as a Claude Code Channel. It runs as a local subprocess using Socket Mode — no public URL needed.

### Tools

- **reply** — Send a message to a Slack channel or thread (`channel_id`, `text`, optional `thread_ts`)
- **react** — Add an emoji reaction to a message (`channel_id`, `timestamp`, `emoji`)
- **manage_access** — Add, remove, or pair users in the access allowlist (`action`: `add_user` / `remove_user` / `pair_user`, `value`: Slack user ID)
- **manage_channels** — Watch or unwatch channels (`action`: `watch` / `unwatch`, `channel_id`)

### Setup

Requires a Slack app with Socket Mode and two tokens:
- `SLACK_BOT_TOKEN` (`xoxb-...`) — Bot User OAuth Token
- `SLACK_APP_TOKEN` (`xapp-...`) — App-Level Token for Socket Mode

See `docs/slack-app-setup.md` for detailed Slack app creation instructions.

### Running

```
claude --dangerously-load-development-channels server:slack-channel
```
