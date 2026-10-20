# Slack App Features

The current Slack features a new app or agent can use. Use this list as the starting shell in **Step 3: Fold the Idea into a Slack App Shell**: begin with every default for the app's shape, then add optional features the idea calls for.

- **Default** says whether the feature is on in the starting shell for an agent, an app that isn't an agent, or neither.
- **How to detect it** names the manifest key, scope, event, or Bolt call that shows a project already uses the feature. It lets a future version of this skill compare an existing app against this list.

For field schemas, method details, and anything this list doesn't name, use the `slack:slack-docs` and `slack:slack-api` skills rather than memory.

## How people reach the app

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Agent view | Opens the agent in its own pane beside whatever they're doing, with an _Add Agent_ entry point | Agent | `features.agent_view` in the manifest, `assistant:write` bot scope |
| Suggested prompts | Starter questions in the agent view, so a new user knows what to ask | Agent | `features.agent_view.suggested_prompts`, or `assistant.threads.setSuggestedPrompts` |
| Direct messages | A private conversation with the app | Agent, App | `features.app_home.messages_tab_enabled`, `message.im` bot event |
| Channel mentions | Ask the app for help in a channel without leaving the conversation | Agent, App | `app_mention` bot event, `app_mentions:read` scope |
| App Home tab | A home page for the app: a welcome, common actions, and the user's own items | Agent, App | `features.app_home.home_tab_enabled`, `app_home_opened` bot event, `views.publish` |
| Slash commands | A quick action typed in the message box, like `/ticket` | Optional | `features.slash_commands` in the manifest |
| Shortcuts | An action from the shortcuts menu, or from a message's menu | Optional | `features.shortcuts` in the manifest |
| Workflow Builder steps | Lets people use the app as a step in workflows they build themselves | Optional | `functions` in the manifest, `function_executed` event |

## How it responds

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Replies in threads | Keeps channels and DMs tidy, and keeps context together | Agent, App | Replies set `thread_ts` |
| Acknowledging reactions | An emoji reaction when the app sees a message, and another when it's done | Agent | `reactions:write` scope, `reactions.add` |
| Thinking status | A short status, like "Searching your workspace...", while the agent works | Agent | Bolt `setStatus` (JavaScript) or `set_status` (Python), `loading_messages` |
| Streaming responses | The answer appears as it's written, instead of after a long wait | Agent | Bolt `sayStream` (JavaScript) or `say_stream` (Python), `chat.startStream` |
| Progress for multi-step work | Shows the agent's plan and steps as it works through them | Agent, when the work has several steps | `plan` and `task_card` blocks, or `task_update` and `plan_update` stream chunks |
| Feedback buttons | Thumbs up or down on each answer, so the developer learns what's working | Agent | `feedback_buttons` element in a `context_actions` block |
| Approval before acting | The agent asks before it creates, sends, deletes, or spends anything | Agent, when it takes actions | Button `actions` blocks with an `action` listener before the tool runs |
| Block Kit messages | Structured messages with sections, fields, tables, and buttons, not just text | App | `blocks` on `chat.postMessage` |
| Modals | A form or a focused view that opens on top of Slack | App, when it collects input | `views.open`, `interactivity.is_enabled` |
| Scheduled messages | Posts at a set time, like a daily summary | Optional | `chat.scheduleMessage` |

## What it can reach

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| The agent's own tools | The actions and lookups that make the agent useful, like creating a ticket or checking a status | Agent | Tool definitions in the agent code |
| Slack MCP server | Lets the agent search messages and files, read channels and threads, and work with canvases, as the user | Agent | `settings.is_mcp_enabled`, `search:read.*` user scopes |
| Canvases | Writes longer documents, like a report or a plan, into Slack | Optional | `canvases:write` scope |
| Link unfurls | Shows a rich preview when someone pastes a link to the developer's own service | Optional | `features.unfurl_domains`, `link_shared` event, `chat.unfurl` |

## How it runs

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Socket Mode | Runs without a public URL, locally and on hosts like Railway or Heroku | Agent, App | `settings.socket_mode_enabled` |
| Installable across an org | Can be installed once for a whole Enterprise Grid organization | Agent, App | `settings.org_deploy_enabled` |
