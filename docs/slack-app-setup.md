# Slack App Setup for Channels

Step-by-step guide to create and configure the Slack app needed for the channel server.

## 1. Create the App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App**
3. Choose **From scratch**
4. Name it something like `Claude Code Channel` (or whatever you prefer)
5. Select your workspace
6. Click **Create App**

## 2. Enable Socket Mode

1. In the left sidebar, click **Socket Mode**
2. Toggle **Enable Socket Mode** to ON
3. You'll be prompted to create an App-Level Token:
   - Name it `socket-mode` (or anything descriptive)
   - Add the scope `connections:write`
   - Click **Generate**
4. **Copy the token** — it starts with `xapp-`. This is your `SLACK_APP_TOKEN`. Save it somewhere safe; you won't see it again.

## 3. Add Bot Token Scopes

1. In the left sidebar, click **OAuth & Permissions**
2. Scroll down to **Scopes** > **Bot Token Scopes**
3. Click **Add an OAuth Scope** and add each of these:

| Scope | Purpose |
|---|---|
| `chat:write` | Send messages and replies |
| `reactions:write` | Add emoji reactions |
| `channels:join` | Join public channels when asked to watch them |
| `channels:read` | Read channel info (names, members) |
| `channels:history` | Read messages in public channels the bot is in |
| `groups:read` | Read private channel info |
| `im:read` | Read DM channel info |
| `im:history` | Read DM messages sent to the bot |
| `users:read` | Look up user names and profiles |
| `app_mentions:read` | Receive @mention events |

## 4. Subscribe to Events

1. In the left sidebar, click **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Expand **Subscribe to bot events**
4. Click **Add Bot User Event** and add each of these:

| Event | Purpose |
|---|---|
| `message.im` | DMs to the bot |
| `message.channels` | Messages in public channels the bot is in |
| `app_mention` | @mentions of the bot in any channel |
| `reaction_added` | Emoji reactions on messages |

5. Click **Save Changes** at the bottom

## 5. Enable the Messages Tab

This allows users to DM the bot — required for pairing and direct interaction.

1. In the left sidebar, click **App Home**
2. Scroll down to **Show Tabs**
3. Check **Messages Tab**
4. Make sure **"Allow users to send Slash commands and messages from the messages tab"** is checked

## 6. Install the App to Your Workspace

1. In the left sidebar, click **Install App**
2. Click **Install to Workspace**
3. Review the permissions and click **Allow**
4. **Copy the Bot User OAuth Token** — it starts with `xoxb-`. This is your `SLACK_BOT_TOKEN`.

## 7. Configure the Channel Server

Add your tokens to `.mcp.json`:

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://mcp.slack.com/mcp",
      "oauth": {
        "clientId": "1601185624273.8899143856786",
        "callbackPort": 3118
      }
    },
    "slack-channel": {
      "command": "bun",
      "args": ["./src/index.ts"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token-here",
        "SLACK_APP_TOKEN": "xapp-your-token-here"
      }
    }
  }
}
```

## 8. Test Standalone (Without Claude Code)

Run the server directly to verify the Slack connection works:

```bash
SLACK_BOT_TOKEN=xoxb-... SLACK_APP_TOKEN=xapp-... bun src/index.ts
```

Expected output on stderr:
```
[slack-channel] connected to Slack as your-bot-name (U...)
[slack-channel] bootstrap mode: DM the bot to start pairing
[slack-channel] ready
```

If you see `ready`, the Slack connection is working. Press Ctrl+C to stop.

**Troubleshooting:**
- `SLACK_BOT_TOKEN is missing or invalid` — Check the token starts with `xoxb-`
- `SLACK_APP_TOKEN is missing or invalid` — Check the token starts with `xapp-`
- Connection hangs — Verify Socket Mode is enabled in the Slack app settings
- `not_authed` error — Reinstall the app to your workspace (step 5)

## 9. Test with Claude Code

```bash
claude --dangerously-load-development-channels server:slack-channel
```

Then in Slack:
1. DM the bot — you should see a pairing code as an ephemeral message
2. Reply `pair <CODE>` — you should see "Paired successfully"
3. Send a message — Claude should receive it and can reply

## 10. Invite the Bot to Channels (Optional)

The bot only receives messages in channels it's been invited to. To monitor a channel:

1. Go to the channel in Slack
2. Type `/invite @Claude Code Channel` (or whatever you named the bot)
3. Or ask Claude to watch it: "start watching #channel-name"
