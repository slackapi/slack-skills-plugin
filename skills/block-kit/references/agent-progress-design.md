# Agent Progress Design: Plans and Task Cards

Guidance on showing an agent's work while it happens, using `plan` and `task_card` blocks, and
their streaming equivalents, the `task_update` and `plan_update` chunks. This covers
_appropriateness_: when to show steps, how to word them, and how they should change over time.
For field schemas, see the `plan`, `task_card`, and `url_source` element pages. For the streaming
API, see `https://docs.slack.dev/reference/methods/chat.startStream.md` and Slack's agent design
guide, `https://docs.slack.dev/concepts/agent-design.md`. Apply these principles unless the
developer explicitly asks otherwise.

Both blocks are **messages only**. A `plan` holds up to 50 task cards, and each `task_id` in a
plan must be unique.

## Pick the lightest progress signal that works

Progress UI is for the user, not a log of everything the agent did. Use only as much as the work
needs:

| The work is… | Show |
|---|---|
| a message that needs no answer (thanks, a passing mention, people talking to each other) | nothing, or a single emoji reaction |
| quick (a few seconds) or a single lookup | a status only (`agents.sessions.setStatus`, such as "Searching your workspace…") |
| a few steps, with the steps mixed into the answer | `task_update` chunks in the default `timeline` display mode: individual task cards between the streamed text |
| multi-step work where the agent is making decisions | a `plan`: `task_display_mode: "plan"` when streaming, or a `plan` block you update with `chat.update` |

- **Use a plan for decisions, not data fetching.** Slack's guidance is to save plans for
  multi-step work where the agent chooses what to do next. Three lookups and an answer don't need
  a plan.
- **Make the plan secondary to the answer.** The plan explains how the agent got there; the
  answer is what the user came for. Put the answer after the plan and make it able to stand on its
  own.
- **Acknowledge right away, before any progress UI.** Set a status, or add a working reaction
  such as 👀 to the user's message and remove it when the reply lands. Then the user knows the
  agent saw the message, even if it decides to stay quiet.
- **If you react instead of replying, give each emoji one meaning** (👍 "got it", ✅ "done",
  ❤️ "thanks") and use only those. A reaction is a reply, so it should be as clear as one.

## Streaming vs. a posted message

- **When streaming** (`chat.startStream` → `chat.appendStream` → `chat.stopStream`), send
  progress as `task_update` chunks. Choose `task_display_mode` when you start the stream:
  `timeline` (the default) for cards interleaved with the streamed text, or `plan` for one grouped
  plan. Send a `task_update` with the same `id` to change a task's status, and a `plan_update`
  chunk to retitle the plan. Each `task_update` and `plan_update` chunk is limited to 256
  characters, so keep `details` and `output` short.
- **Send a task's `details` once.** On an update with the same `id`, Slack adds the new `details`
  to the earlier text instead of replacing it, with no separator. Send details either while the
  task is in progress or when it completes, not both, and never send placeholder text you'll want
  to replace.
- **Open the stream when there's something to show**, not when the run starts. If the agent ends
  up staying quiet or only reacting, nothing is posted, so there's no empty message to clean up.
- **Send stream updates one at a time, in order, and wait for them all before
  `chat.stopStream`.** If updates are fired off without waiting, a task's final `complete` can
  arrive after the stream stops, which leaves that task spinning forever.
- **When not streaming**, post a message with a `plan` block and update it in place with
  `chat.update` as each task changes. Don't post a new message per step, and don't call
  `chat.update` more than about once every 3 seconds. Collect several changes into one update.
- **Don't build a progress view from text** ("Step 3 done ✅" lines in a `section`). The plan and
  task card blocks already provide status icons, structure, and accessibility.

## Give each piece of text one job

A plan has three layers of text. Keep each one to its job so the plan reads at a glance:

| Layer | Says | While working | When done | On failure |
|---|---|---|---|---|
| plan title | where the run is overall | what the agent is doing now: "Searching Linear" | the outcome: "Worked for 12s" | "Error" or "Stopped" |
| task title | the action | present tense: "Searching Linear issues" | past tense: "Searched Linear issues" | "Couldn't search Linear issues" |
| task details / output | the facts | the subject: "#incidents, last 7 days" | the result: "3 matches: INC-41, INC-44, …" | the reason: "Linear needs a reconnect" |

- **Task titles name the action, not the subject.** Keep the subject (a query, a channel, a file
  name) in the details, so titles stay short and the same tool always reads the same way.
- **Keep each title to one short phrase.** Slack's guidance is that a step should be one short
  phrase; a paragraph of reasoning is too much.
- **Name the system in plain language, not the API**: "Checking your calendar", not "Calling
  `events.list`". This also shows the user what the agent can access. For tools from a connected
  app, put the app's name in front of the details: "Todoist · 3 tasks due today".
- **Lead with the verb and object**: "Drafting the reply to Priya", "Creating a Linear issue".
- **Make write actions obvious.** A task that creates, sends, or deletes something should say so
  in its title ("Sending summary to #eng"). Read-only lookups can be grouped or kept low-key.
- **Never show raw tool output.** Turn results into a human line: a count and a few names ("12
  messages", "3 files: plan.md, notes.md, …"). Never show JSON, and if there's nothing useful to
  say, say nothing rather than "Done".
- **Show retries as retries.** If the agent calls the same tool again after an error, title it
  "Retrying: Searching Linear issues", or add "attempt 2" to the details, so it doesn't look like a
  duplicate step.

## Status, details, output, and sources

- **Status reflects what's actually happening.** Set a task to `in_progress` only when the agent
  starts it, then switch it to `complete` or `error`. Don't mark everything complete at the end;
  the point is to show live progress.
- **Show the whole plan up front when the steps are known in advance.** Tasks that haven't
  started can use `pending` in plan display mode. The plan guide documents it, but the
  `task_card` page lists only `in_progress`, `complete`, and `error`, so check the live page.
  When the agent decides steps as it goes, add tasks as they start rather than inventing a plan it
  might not follow.
- **`details` is what the task did; `output` is what it found.** Keep both to a line or two of
  `rich_text`: details "Searched #incidents for the last 7 days", output "Found 3 related
  incidents". The full answer goes in the message body, not in a task's output.
- **Attach `sources` to the task that used them** (`url_source` elements). This keeps
  attribution next to the step it supports, so you don't need a separate citation list for those
  steps.
- **Use `hide_title`** only when the task's details already say everything the title would.

## Voice

- **Keep one voice everywhere**, either first person ("I found 3 issues") or neutral ("Found 3
  issues"), across status, task titles, errors, and recaps. Slack's own AI uses the neutral voice.
  Don't give the agent feelings or a gender, and skip casual apologies.

## When something goes wrong

- **Mark the failing task `error`, not the whole plan.** Leave completed tasks `complete` so the
  user can see how far the agent got.
- **Say what failed and why in that task's `output`**, in plain language: "No access to the
  Project Beta board".
- **Name the cause and the fix** rather than "Something went wrong." Tell apart a credential the
  user must fix ("Todoist needs a reconnect", with a Reconnect button), a temporary limit ("Rate
  limited, try again in a minute"), and a bug on your side ("Something broke on my end. I've
  logged it, please try again").
- **Set the plan title to "Error"** when the run ends with a failed step, so the outcome is
  visible even when the plan is collapsed.
- **Follow the plan with recovery options**: two or three next steps as buttons (Retry, Change Request, Ask an Admin), not a dead end. See `human-in-the-loop.md` for how to structure those
  choices.
- **Clear the status when the agent stops**, even on failure, so the thread isn't left showing
  "thinking" forever. Set `agents.sessions.setStatus` to `active`, or to `suspended` if the user
  has to do something before the agent can continue, such as when the reply ends with a
  clarifying question.

## Stopping and interruptions

- **Honor the Stop button.** When the user stops a run (the `agent_session_stopped` event),
  cancel the work, end the stream with the plan title "Stopped", and post one short line: "Okay,
  I stopped." Leave completed tasks as they are, so the user can see what was already done.
- **If the user sends a new message mid-run, start over quietly.** When newer messages change the
  request, abandon the current run without a "stopped" note and respond to the thread as it is
  now. The user didn't ask to stop, so there's nothing to acknowledge.
- **Cancel pending approvals with the run.** If a stopped run was waiting on an approval, mark the
  approval as cancelled (see `human-in-the-loop.md`) so its buttons don't outlive the run.

## When the work is done

- **Set the final plan title to the outcome**, such as "Worked for 12s", so a collapsed plan still
  tells the user the run finished and roughly how long it took.
- **End with a short recap**: what happened, with links to anything created or changed, and
  anything skipped and why ("Couldn't assign to <@U123>, who isn't on the project"). Keep the
  recap shorter than the task took to describe.
- **Add `feedback_buttons`** in a `context_actions` block after the final answer, not inside the
  plan.

## Quick self-review

1. Does this work need a plan, or would a status or timeline task updates be enough?
2. Does each task title name the action, in plain language, with the facts in the details?
3. Do statuses change live, do write actions stand out, and are retries labeled?
4. Are `details` and `output` short (under 256 characters when streamed), sent once, never raw
   JSON, with sources on the task that used them?
5. If a step fails, does the user see what worked, what didn't, and what they can do next?
6. Does the plan title end as the outcome ("Worked for…", "Error", "Stopped"), with no task left
   spinning?
7. Is the final answer complete on its own, with the plan clearly secondary?
