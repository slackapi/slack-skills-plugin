# Slack App Features

The current Slack features a new app or agent can use. Use this list as the starting shell in **Step 3: Fold the Idea into a Slack App Shell**: begin with every default for the app's shape, then add optional features the idea calls for.

- **Default** says whether the feature is on in the starting shell for an agent, an app that isn't an agent, or neither.
- **How to detect it** names the manifest key, scope, event, method, or Bolt utility that shows a project already uses the feature. It lets a future version of this skill compare an existing app against this list.

The agent features come from Slack's [Agent design](https://docs.slack.dev/concepts/agent-design.md) and [Developing an agent](https://docs.slack.dev/ai/developing-agents.md) guides. Before writing the spec, use the `slack:slack-docs` skill to check the "Agent features overview" section of the Agent design guide for anything newer than this list. For field schemas and method details, use the `slack:slack-docs` and `slack:slack-api` skills rather than memory.

## How People Reach the App

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Agent messaging experience | Labels the app as an agent and gives it an entry point in Slack's top navigation. Conversations happen in the Messages tab, with threads in a timeline above the composer | Agent | `features.agent_view` in the manifest, `assistant:write` bot scope. New apps can only use `agent_view`. The older `assistant_view` is headed for deprecation |
| Split view | Opens the agent in a side panel, next to whatever the person is doing | Agent | Comes with `features.agent_view` |
| Suggested prompts | 2-4 starter prompts that show what the agent does, so a new user knows where to start | Agent | `features.agent_view.suggested_prompts`, or `assistant.threads.setSuggestedPrompts` (Bolt `setSuggestedPrompts` or `set_suggested_prompts`) |
| Welcome message | A first message that explains the agent, and asks people to sign in or connect an account if it needs that | Agent | `app_home_opened` event with `tab` set to `messages` |
| Direct messages | A private conversation with the app | Agent, App | `features.app_home.messages_tab_enabled`, `message.im` bot event |
| Channel mentions | Ask the app for help in a channel without leaving the conversation | Agent, App | `app_mention` bot event, `app_mentions:read` scope |
| App Home tab | A home page for the app: a welcome, common actions, and a place to review what the agent did for the person | Agent, App | `features.app_home.home_tab_enabled`, `app_home_opened` event, `views.publish` |
| Slash commands | A quick action typed in the message box, like `/ticket`. Pick a name Slack doesn't already use: built-in commands like `/status` and `/remind` fail manifest validation | Optional | `features.slash_commands` |
| Shortcuts | An action from the shortcuts menu, or from a message's menu | Optional | `features.shortcuts` |
| Workflow Builder steps | Lets people use the app as a step in workflows they build themselves | Optional | `functions` in the manifest, `function_executed` event |
| Code channels | For a coding agent: one channel per task, with diffs, previews, and canvases in the channel's Artifacts panel | Optional, coding agents only | See "Code channels" in the Agent design guide |

## How It Responds

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Agent sessions and status | Shows the agent in the person's sessions list with a loading indicator while it works, cleared when it's done | Agent | `agents.sessions.setStatus` with `processing`, which creates the session if needed, then `active` (or `suspended` when the person needs to step in). It doesn't support custom loading messages. Bolt's `setStatus` (JavaScript) or `set_status` (Python) wraps the older `assistant.threads.setStatus`, which takes a free-text status and `loading_messages` |
| Stop button | Lets people stop the agent mid-task | Agent | `agent_session_stopped` event |
| Session titles | Names each conversation so people can find it later, and keeps the name in sync when they rename it | Agent | `agents.sessions.rename`, `agent_session_title_changed` event. Bolt's `setTitle` wraps the older `assistant.threads.setTitle` |
| What the person is viewing | Tailors answers to the channel, thread, canvas, or list the person has open | Agent | `app_context_changed` event |
| Streaming responses | Long answers appear as they're written, and people can redirect the agent early. Short or structured answers go out whole | Agent | `chat.startStream`, `chat.appendStream`, `chat.stopStream` with `markdown_text` chunks. Bolt `sayStream` (JavaScript) or `say_stream` (Python) |
| Standard markdown for generated text | Model output renders as written, using standard markdown rather than Slack's `mrkdwn` | Agent | `markdown_text` stream chunks, or the `markdown` block |
| Thinking steps | Shows the agent's steps and tool calls while it works, in plain language, then collapses them behind the answer | Agent, when the work has several steps | `task_update` and `plan_update` stream chunks, `task_display_mode`, `plan` and `task_card` blocks |
| Feedback | Thumbs up or down on each answer, so the developer learns what's working | Agent | `feedback_buttons` element in a `context_actions` block. An `icon_button` in the same block can offer delete |
| Confirmation before acting | The agent previews what it will create, send, or delete, and waits for approve, change, or cancel. It also offers choices when a request is ambiguous | Agent, when it takes actions | Buttons or menus in an `actions` block, handled before the tool runs |
| Sources and citations | Says where an answer came from, with links | Agent | Links in the reply, plus a `context` block listing references |
| AI disclaimer | A footer saying the answer was generated by AI and may be wrong | Agent | A `context` block at the end of the reply |
| Task recap | A short summary when a task finishes, with links to what changed and what was skipped | Agent, when it takes actions | Final message after the work |
| Replies in threads | Keeps channels tidy and context together. Channel replies stay short, DMs can be more conversational | Agent, App | Replies set `thread_ts` |
| Acknowledging reactions | An emoji reaction when the app sees a message, and another when it's done | Agent, App | `reactions:write` scope, `reactions.add` |
| Block Kit messages | Structured messages with sections, fields, tables, and buttons | App | `blocks` on `chat.postMessage` or `chat.stopStream` |
| Modals | A form or a focused view on top of Slack | App, when it collects input | `views.open`, `interactivity.is_enabled` |
| Scheduled messages | Posts at a set time, like a daily summary | Optional | `chat.scheduleMessage` |

## What It Can Reach

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| The agent's own tools | The actions and lookups that make the agent useful, like creating a ticket or checking a status | Agent | Tool definitions in the agent code |
| Slack MCP server | Lets the agent search messages and files, read channels and threads, and work with canvases, as the person using it and only with their access | Agent | `settings.is_mcp_enabled`, `search:read.*` user scopes |
| Files and images | Accepts the files people send, or says clearly which ones it can't handle | Optional | `files:read` scope, `files` on `message` events |
| Canvases | Writes longer documents, like a report or a plan, into Slack | Optional | `canvases:write` scope |
| Link unfurls | A rich preview when someone pastes a link to the developer's own service | Optional | `features.unfurl_domains`, `link_shared` event, `chat.unfurl` |

## How It Runs

| Feature | What it gives people | Default | How to detect it |
|---|---|---|---|
| Socket Mode | Runs without a public URL, locally and on hosts like Railway or Heroku | Agent, App | `settings.socket_mode_enabled` |
| Installable across an org | Can be installed once for a whole Enterprise Grid organization | Agent, App | `settings.org_deploy_enabled` |

## Limits to Plan Around

- **Workspace guests can't use apps with the agent feature.** If guests are the main users, plan an app that isn't an agent.
- **Some AI features need a paid plan.** A developer sandbox from the Developer Program has them for free.
- **Don't store Slack data.** Store IDs and other metadata, and fetch the content when it's needed.
