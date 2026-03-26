# Slack Channel Support — Design Spec

## Overview

Add Claude Code Channels support to the Slack MCP plugin, enabling real-time bidirectional messaging between Slack and a Claude Code session. The channel runs as a local Bun subprocess over stdio, using Slack's Socket Mode (WebSocket) for event delivery — no public URL or HTTP listener needed.

The primary use case is **headless operation**: an instance running on a server with no terminal interaction. All administration (access control, channel watching) happens through Slack conversations with Claude. Permission relay allows tool approval/denial from Slack.

## Architecture

The channel server is a single Bun process with three layers:

```
Slack (Socket Mode WSS)
    ↕
┌─────────────────────────────┐
│  Slack Layer (@slack/bolt)  │  ← receives events, sends replies
├─────────────────────────────┤
│  Bridge Layer               │  ← transforms events ↔ notifications
├─────────────────────────────┤
│  MCP Layer (@mcp/sdk)       │  ← channel capability, tools, permissions
└─────────────────────────────┘
    ↕ stdio
Claude Code
```

- **Slack Layer**: A `@slack/bolt` app in Socket Mode. Subscribes to `message` events (DMs + channel messages), `app_mention` events, and `reaction_added` events. Sends messages back via `chat.postMessage`.
- **Bridge Layer**: Stateless transformer. Takes a Bolt event, extracts relevant fields (sender, channel, thread_ts, text), checks sender gating, and emits an MCP `notifications/claude/channel` notification. In reverse, takes a reply tool call and routes it to the correct Bolt API method.
- **MCP Layer**: Standard channel server. Declares `claude/channel` + `claude/channel/permission` capabilities. Exposes `reply`, `react`, `manage_access`, and `manage_channels` tools. Handles permission relay notifications.

No HTTP listener is needed — Socket Mode is WebSocket-based, and the MCP connection is stdio. The process exposes no ports.

## Configuration

### Slack App Credentials

Provided via environment variables in the MCP server config:

- `SLACK_BOT_TOKEN` — Bot User OAuth Token (`xoxb-...`)
- `SLACK_APP_TOKEN` — App-Level Token (`xapp-...`) for Socket Mode

### Runtime Settings

Stored in a single JSON file at a configurable path (default: `~/.slack-channel/settings.json`). Configurable via the `SLACK_CHANNEL_SETTINGS_PATH` environment variable.

```json
{
  "gating": {
    "mode": "per-user",
    "allowedUsers": ["U12345ABC"],
    "allowedWorkspaces": []
  },
  "watchedChannels": ["C09876DEF", "C11223344"],
  "pairing": {
    "pendingCodes": {}
  }
}
```

- **`gating.mode`**: `"per-user"` (only `allowedUsers` can interact) or `"workspace"` (all users from `allowedWorkspaces` are allowed).
- **`watchedChannels`**: Channel IDs where the bot listens for all messages. In channels not on this list, only `@mentions` and DMs trigger notifications.
- **`pairing.pendingCodes`**: Transient map of `code → { userId, timestamp }` for the pairing flow. Codes expire after 5 minutes. Not persisted across restarts.

The settings file is read at startup. Default is `"per-user"` with an empty allowlist (bootstrap mode).

## MCP Server Registration

The `.mcp.json` gains a second entry alongside the existing remote Slack MCP:

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/mcp",
      "oauth": { "clientId": "...", "callbackPort": 3118 }
    },
    "slack-channel": {
      "command": "bun",
      "args": ["./src/index.ts"],
      "env": {
        "SLACK_BOT_TOKEN": "",
        "SLACK_APP_TOKEN": ""
      }
    }
  }
}
```

The existing `slack` tools (search, read, send) remain on the remote server. The `slack-channel` entry is the local channel subprocess. They coexist.

## MCP Capabilities

```ts
capabilities: {
  experimental: {
    'claude/channel': {},
    'claude/channel/permission': {},
  },
  tools: {},
},
instructions: `Messages from Slack arrive as <channel source="slack" event="..." user="..." channel_id="..." ...>.
Events: "dm" (direct message to bot), "mention" (@mention in a channel), "message" (watched channel), "reaction" (emoji on a bot message).
Reply with the reply tool, passing channel_id and optionally thread_ts from the tag.
Use the react tool to add emoji reactions.
Use manage_access and manage_channels to administer the instance when asked.`
```

## MCP Tools

### `reply`

Send a message back to Slack.

| Param | Type | Required | Description |
|---|---|---|---|
| `channel_id` | string | yes | Slack channel ID to send to |
| `text` | string | yes | Message content (standard markdown) |
| `thread_ts` | string | no | Thread timestamp to reply in-thread |

### `react`

Add an emoji reaction to a message.

| Param | Type | Required | Description |
|---|---|---|---|
| `channel_id` | string | yes | Channel containing the message |
| `timestamp` | string | yes | Message timestamp to react to |
| `emoji` | string | yes | Emoji name without colons (e.g. `thumbsup`) |

### `manage_access`

Add or remove users/workspaces from the allowlist, or switch gating mode. Only callable when the originating user is already in the allowlist.

| Param | Type | Required | Description |
|---|---|---|---|
| `action` | string | yes | `add_user`, `remove_user`, `add_workspace`, `remove_workspace`, `set_mode` |
| `value` | string | yes | User ID, workspace ID, or mode (`per-user` / `workspace`) |

### `manage_channels`

Add or remove channels from the watch list. After watching a new channel, the bot joins it via `conversations.join`.

| Param | Type | Required | Description |
|---|---|---|---|
| `action` | string | yes | `watch` or `unwatch` |
| `channel_id` | string | yes | Channel ID |

## Notification Format

### Inbound Events (Slack → Claude)

All events arrive as `<channel>` tags with consistent metadata keys:

**DM to the bot:**
```xml
<channel source="slack" event="dm" user="U12345ABC" user_name="alice" channel_id="D98765" ts="1711500000.000100">
Hey, can you check the latest deploy?
</channel>
```

**@mention in a channel:**
```xml
<channel source="slack" event="mention" user="U12345ABC" user_name="alice" channel_id="C09876DEF" channel_name="deploys" thread_ts="1711500000.000200" ts="1711500000.000300">
@bot what caused the last failure?
</channel>
```

**Message in a watched channel:**
```xml
<channel source="slack" event="message" user="U12345ABC" user_name="alice" channel_id="C09876DEF" channel_name="deploys" ts="1711500000.000400">
deploy to staging just failed with exit code 1
</channel>
```

**Reaction on a message Claude sent:**
```xml
<channel source="slack" event="reaction" user="U12345ABC" user_name="alice" channel_id="C09876DEF" emoji="eyes" item_ts="1711500000.000500" ts="1711500000.000600">
Reaction :eyes: on message: "Deploy summary: 3 services updated..."
</channel>
```

Meta keys: `event` for routing, `user` + `user_name` for identity, `channel_id` + `channel_name` for context, `ts` for the message timestamp, `thread_ts` when part of a thread.

### Permission Relay

When Claude Code emits a `permission_request`, the bridge formats it and sends it as a DM (or in the originating thread) to the allowed user(s):

> **Claude wants to run `Bash`:** `git pull origin main`
> Reply `yes abcde` or `no abcde`

Replies matching the `yes/no <id>` pattern are intercepted and emitted as `notifications/claude/channel/permission` verdicts instead of being forwarded as chat messages.

## Sender Gating & Pairing

### Gating Logic

Every inbound event is checked against the allowlist before emitting an MCP notification:

- **`per-user` mode**: `event.user` must be in `gating.allowedUsers`
- **`workspace` mode**: the user's workspace (from the event or a cached lookup) must be in `gating.allowedWorkspaces`

Gate on the sender's user ID, not the channel/room ID.

### First-User Bootstrap

1. Instance starts with an empty allowlist → enters bootstrap mode
2. First user to DM the bot receives a 6-character pairing code via ephemeral Slack message (only they can see it)
3. The code is also written to stdout and to a file at `~/.slack-channel/pairing-code.txt`
4. User echoes the code back to the bot (e.g., "pair ABC123")
5. Round-trip verified — code matches and was sent to the same user. User is added to the allowlist. Bootstrap mode ends.

Security: the code is ephemeral (only the recipient sees it), must be echoed by the same user, and expires after 5 minutes.

### Subsequent User Pairing

1. An authorized user asks Claude to pair a new user (e.g., "pair @bob")
2. Claude calls `manage_access` to note the intent; the bridge sends an ephemeral pairing code to Bob
3. Bob echoes the code back. Round-trip verified, Bob is added.

### Pre-configured Allowlist

For automated deployments, populate `settings.json` with known user IDs before starting. This skips pairing entirely.

## Project Structure

```
slack-mcp-plugin/
├── src/
│   ├── index.ts          # Entry point: wires up MCP server, Bolt app, bridge
│   ├── mcp.ts            # MCP server setup: capabilities, tools, permission relay
│   ├── slack.ts          # Bolt app setup: Socket Mode, event subscriptions
│   ├── bridge.ts         # Event transformer: Slack events ↔ MCP notifications
│   ├── gating.ts         # Sender allowlist checks, pairing flow logic
│   └── settings.ts       # Settings file read/write (atomic)
├── package.json          # bun, @slack/bolt, @modelcontextprotocol/sdk, zod
├── tsconfig.json
└── ... (existing files unchanged)
```

## Error Handling & Resilience

- **Socket Mode disconnects**: Bolt handles reconnection with exponential backoff automatically.
- **Settings file corruption**: Read with try/catch at startup. Invalid JSON → log warning, start with defaults (empty allowlist, bootstrap mode). Never crash on bad settings.
- **Pairing code expiry**: In-memory map with timestamps. Prune codes older than 5 minutes on each access. Not persisted.
- **Bolt event errors**: Wrap the bridge event handler in try/catch. Always `ack()` the event envelope first, then process. Never let a single bad event crash the process.
- **Settings file writes**: Atomic write (write to temp file, then rename) to prevent corruption.
- **Startup validation**: Check that both tokens are present and well-formed (`xoxb-` and `xapp-` prefixes). Fail fast with a clear error rather than connecting with bad credentials.

No external monitoring or health endpoints — infrastructure-level supervision (systemd, Docker) is the user's responsibility. The channel's responsibility is to not crash and to reconnect when disconnected.
