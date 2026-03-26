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
    "allowedUsers": ["U12345ABC"]
  },
  "watchedChannels": ["C09876DEF", "C11223344"]
}
```

- **`gating.mode`**: `"per-user"` — only users in `allowedUsers` can interact. (Workspace-level gating is deferred to a future iteration; see [Future Work](#future-work).)
- **`watchedChannels`**: Channel IDs where the bot listens for all messages. In channels not on this list, only `@mentions` and DMs trigger notifications.

Pairing codes are transient, process-local state — stored in an in-memory `Map<string, { userId: string; timestamp: number }>` inside `gating.ts`, never written to the settings file. Codes expire after 5 minutes and are pruned on each access.

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

**Development flag**: During the research preview, start Claude Code with `--dangerously-load-development-channels server:slack-channel` to bypass the channel allowlist. Once the plugin is on the approved allowlist, this flag is no longer needed.

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

Add or remove users from the allowlist or initiate pairing. **Authorization**: when a tool call arrives, the bridge checks `lastActiveContext.userId` against the allowlist. If `lastActiveContext` is null (no gated interaction has occurred yet) or the caller is not in the allowlist, the tool returns an authorization error and no action is taken.

| Param | Type | Required | Description |
|---|---|---|---|
| `action` | string | yes | `add_user`, `remove_user`, `pair_user` |
| `value` | string | yes | Slack user ID (e.g. `U12345ABC`) |

- **`add_user`**: Directly adds a user to the allowlist (no pairing round-trip). Use for trusted additions.
- **`remove_user`**: Removes a user from the allowlist.
- **`pair_user`**: Initiates the pairing flow for the target user — sends them an ephemeral code that they must echo back before being added. Use when the requesting user wants to verify the target's identity.

All values are Slack user IDs. If Claude receives a `@handle` from the user, it should resolve it to a user ID using the existing remote `slack_search_users` tool before calling `manage_access`.

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

**Reaction event filter**: Only emit `reaction` notifications when `reaction_added.item.type === 'message'` AND the reacted-to message's author (`item_user`) matches the bot's own user ID. All other `reaction_added` events are silently dropped.

Meta keys: `event` for routing, `user` + `user_name` for identity, `channel_id` + `channel_name` for context, `ts` for the message timestamp, `thread_ts` when part of a thread.

**Meta key constraint**: All meta keys must match `[a-z0-9_]+`. Keys containing hyphens or other characters are silently dropped by Claude Code.

**Name resolution**: `user_name` and `channel_name` require resolving Slack IDs via `users.info` and `conversations.info` API calls. The bridge maintains a per-process in-memory cache (`Map<string, string>`) for both, populated on first lookup. Cache entries do not expire within a process lifetime (names change rarely).

### Permission Relay

The bridge maintains a `lastActiveContext: { userId: string, channelId: string, threadTs?: string }` variable, updated on every gated inbound event. When Claude Code emits a `permission_request`, the bridge sends the prompt to this context — either in the originating thread or as a DM to the last active user.

If `lastActiveContext` is null (no interaction has occurred yet), the permission request is logged to stderr and dropped. The local terminal dialog remains open as the only way to respond.

Example prompt sent to Slack:

> **Claude wants to run `Bash`:** `git pull origin main`
> Reply `yes abcde` or `no abcde`

Replies matching the `yes/no <id>` pattern (regex: `/^\s*(y|yes|n|no)\s+([a-km-z]{5})\s*$/i`) are intercepted and emitted as `notifications/claude/channel/permission` verdicts instead of being forwarded as chat messages.

## Sender Gating & Pairing

### Gating Logic

Every inbound event is checked against the allowlist before emitting an MCP notification:

- `event.user` must be in `gating.allowedUsers`

Gate on the sender's user ID, not the channel/room ID. Events from ungated users are silently dropped (no error response).

### First-User Bootstrap

1. Instance starts with an empty allowlist → enters bootstrap mode
2. The first user to DM the bot receives a 6-character pairing code via ephemeral Slack message (only they can see it)
3. The code is also written to stdout (captured in Claude Code's debug log) and to a file at `~/.slack-channel/pairing-code.txt`
4. Only one pairing code is active at a time during bootstrap. If a second user DMs while a code is pending, the bot replies with an ephemeral message: "Pairing already in progress, please try again shortly."
5. User echoes the code back to the bot (e.g., "pair ABC123")
6. Round-trip verified — code matches and was sent to the same user. User is added to the allowlist. Bootstrap mode ends.
7. After the first user is paired, subsequent users go through the "Subsequent User Pairing" flow below.

Security: the code is ephemeral (only the recipient sees it), must be echoed by the same user, and expires after 5 minutes.

### Subsequent User Pairing

1. An authorized user asks Claude to pair a new user (e.g., "pair @bob")
2. Claude resolves Bob's user ID via the remote `slack_search_users` tool, then calls `manage_access` with `action: "pair_user"` and `value: "U67890XYZ"`
3. The bridge resolves the target user and sends them an ephemeral pairing code
4. Bob echoes the code back to the bot. Round-trip verified, Bob is added to the allowlist.

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

## Future Work

These items are explicitly out of scope for v1 but noted for future iterations:

- **Workspace-level gating**: A `"workspace"` gating mode that allows all users from specified Slack workspaces. Requires resolving workspace membership via `team.id` from events or the `authorizations` field, with a caching strategy. Deferred due to complexity and unclear benefit for the primary headless use case.
- **All-channel message monitoring**: Listening to all messages in all channels (not just watched ones).
- **File/image attachments**: Forwarding file uploads from Slack as channel event attachments.
- **Multi-session support**: Routing different Slack channels to different Claude Code sessions.
