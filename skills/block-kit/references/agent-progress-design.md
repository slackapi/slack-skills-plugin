# Agent Progress Design: Plans and Task Cards

Guidance on showing an agent's work while it happens, using `plan` and `task_card` blocks and
their streaming equivalents, the `task_update` and `plan_update` chunks. It builds on
`design-principles.md` and covers when to show steps, how to word them, and how they should
change over time. For field schemas, see the `plan`, `task_card`, and `url_source` element pages.
For the streaming API, see `https://docs.slack.dev/reference/methods/chat.startStream.md` and
Slack's agent design guide, `https://docs.slack.dev/concepts/agent-design.md`. Apply these
principles unless the developer explicitly asks otherwise.

Both blocks are available in messages only.

## Pick the lightest progress signal that works

Progress UI is for people, not a log of everything the agent did. Use only as much as the work
needs:

| The work is… | Show |
|---|---|
| a message that needs no answer (thanks, a passing mention, people talking to each other) | nothing, or a single emoji reaction |
| quick (a few seconds) or a single lookup | a status only, such as "Searching your workspace…" |
| a few steps, with the steps mixed into the answer | task cards in the default `timeline` display mode, between the streamed text |
| multi-step work where the agent is making decisions | a `plan` |

- **Save plans for work where the agent decides what to do next.** Three lookups and an answer
  don't need a plan.
- **Make the plan secondary to the answer.** The plan explains how the agent got there; the
  answer is what people came for. Put the answer after the plan and make it able to stand on its
  own.
- **Acknowledge right away, before any progress UI.** Set a status, or add a working reaction
  such as 👀 to the person's message and remove it when the reply lands. Then they know the agent
  saw the message, even if it decides to stay quiet.
- **Give each reaction emoji one meaning** (👍 "got it", ✅ "done", ❤️ "thanks") and use only
  those. A reaction is a reply, so it should be as clear as one.

## Show progress as it happens

- **Update one message in place.** Don't post a new message per step.
- **Post something only when there's something to show**, not when the run starts. If the agent
  ends up staying quiet or only reacting, there's no empty message to clean up.
- **Use the plan and task card blocks, not text.** "Step 3 done ✅" lines in a `section` lack the
  status icons, structure, and accessibility the blocks already provide.

## Give each piece of text one job

A plan has three layers of text. Keep each one to its job so the plan reads at a glance:

| Layer | Says | While working | When done | On failure |
|---|---|---|---|---|
| plan title | where the run is overall | what the agent is doing now: "Searching Linear" | the outcome: "Worked for 12s" | "Error" or "Stopped" |
| task title | the action | present tense: "Searching Linear issues" | past tense: "Searched Linear issues" | "Couldn't search Linear issues" |
| task details / output | the facts | the subject: "#incidents, last 7 days" | the result: "3 matches: INC-41, INC-44, …" | the reason: "Linear needs a reconnect" |

- **Name the action in the task title, not the subject.** Keep the subject (a query, a channel, a
  file name) in the details, so titles stay short and the same tool always reads the same way.
- **Keep each title to one short phrase.** A paragraph of reasoning is too much.
- **Name the system in plain language, not the API**: "Checking your calendar", not "Calling
  `events.list`". This also shows people what the agent can access. For tools from a connected
  app, put the app's name in front of the details: "Todoist · 3 tasks due today".
- **Lead with the verb and object**: "Drafting the reply to Priya", "Creating a Linear issue".
- **Make write actions obvious.** A task that creates, sends, or deletes something should say so
  in its title ("Sending summary to #eng"). Read-only lookups can be grouped or kept low-key.
- **Turn tool output into a human line**: a count and a few names ("12 messages", "3 files:
  plan.md, notes.md, …"). Don't show JSON, and if there's nothing useful to say, say nothing
  rather than "Done".
- **Show retries as retries.** If the agent calls the same tool again after an error, title it
  "Retrying: Searching Linear issues", or add "attempt 2" to the details, so it doesn't look like a
  duplicate step.

## Status, details, output, and sources

- **Make status reflect what's actually happening.** Mark a task in progress only when the agent
  starts it, then switch it to complete or error. Don't mark everything complete at the end; the
  point is to show live progress.
- **Show the whole plan up front when the steps are known in advance.** When the agent decides
  steps as it goes, add tasks as they start rather than inventing a plan it might not follow.
- **Use details for what the task did and output for what it found.** Keep both to a line or two:
  details "Searched #incidents for the last 7 days", output "Found 3 related incidents". The full
  answer goes in the message body, not in a task's output.
- **Attach sources to the task that used them.** This keeps attribution next to the step it
  supports, so you don't need a separate citation list for those steps.
- **Hide a task's title** only when its details already say everything the title would.

## Voice

- **Keep one voice everywhere**, either first person ("I found 3 issues") or neutral ("Found 3
  issues"), across status, task titles, errors, and recaps. Slack's own AI uses the neutral voice.
  Don't give the agent feelings or a gender, and skip casual apologies.

## When something goes wrong

- **Mark the failing task as an error, not the whole plan.** Leave completed tasks complete so
  people can see how far the agent got.
- **Say what failed and why in that task's output**, in plain language: "No access to the
  Project Beta board".
- **Name the cause and the fix** rather than "Something went wrong." Tell apart a credential the
  person must fix ("Todoist needs a reconnect", with a Reconnect button), a temporary limit ("Rate
  limited, try again in a minute"), and a bug on your side ("Something broke on my end. I've
  logged it, please try again").
- **Set the plan title to "Error"** when the run ends with a failed step, so the outcome is
  visible even when the plan is collapsed.
- **Follow the plan with recovery options**: two or three next steps as buttons (Retry, Change
  Request, Ask an Admin), not a dead end. `human-in-the-loop.md` covers how to structure those
  choices.
- **Clear the status when the agent stops**, even on failure, so the thread isn't left showing
  "thinking" forever.

## Stopping and interruptions

- **Honor the Stop button.** Cancel the work, set the plan title to "Stopped", and post one short
  line: "Okay, I stopped." Leave completed tasks as they are, so people can see what was already
  done.
- **Start over quietly if a new message arrives mid-run.** When newer messages change the
  request, abandon the current run without a "stopped" note and respond to the thread as it is
  now. Nobody asked to stop, so there's nothing to acknowledge.
- **Cancel pending approvals with the run.** If a stopped run was waiting on an approval, mark the
  approval as cancelled (see `human-in-the-loop.md`, **Close the loop**) so its buttons don't
  outlive the run.

## When the work is done

- **Set the final plan title to the outcome**, such as "Worked for 12s", so a collapsed plan still
  says the run finished and roughly how long it took.
- **End with a short recap**: what happened, with links to anything created or changed, and
  anything skipped and why ("Couldn't assign to <@U123>, who isn't on the project"). Keep the
  recap shorter than the task took to describe.
- **Add `feedback_buttons`** in a `context_actions` block after the final answer, not inside the
  plan.

## Implementation notes

- **Respect the limits.** A `plan` holds up to 50 task cards, and each `task_id` in a plan must be
  unique.
- **Set a status with `agents.sessions.setStatus`.** When the agent stops, set it to `active`, or
  to `suspended` if the person has to do something before the agent can continue, such as
  answering a clarifying question.
- **When streaming** (`chat.startStream` → `chat.appendStream` → `chat.stopStream`), send
  progress as `task_update` chunks. Choose `task_display_mode` when you start the stream:
  `timeline` (the default) for cards interleaved with the streamed text, or `plan` for one grouped
  plan. Send a `task_update` with the same `id` to change a task's status, and a `plan_update`
  chunk to retitle the plan. Each chunk is limited to 256 characters, so keep `details` and
  `output` short.
- **Send a task's `details` once.** On an update with the same `id`, Slack appends the new
  `details` to the earlier text with no separator. Send details either while the task is in
  progress or when it completes, and don't send placeholder text you'll want to replace.
- **Send stream updates one at a time, in order, and wait for them all before
  `chat.stopStream`.** If updates are fired off without waiting, a task's final `complete` can
  arrive after the stream stops, which leaves that task spinning forever.
- **When not streaming**, post a message with a `plan` block and update it with `chat.update` as
  each task changes. Call `chat.update` no more than about once every 3 seconds, collecting
  several changes into one update.
- **Use `in_progress`, `complete`, and `error` for task status.** The plan guide also documents
  `pending` for tasks that haven't started in plan display mode, but the `task_card` page doesn't
  list it, so check the live page before relying on it.
- **Attach sources as `url_source` elements**, write `details` and `output` as `rich_text`, and
  hide a title with `hide_title`.
- **Handle Stop on the `agent_session_stopped` event**, ending the stream with the plan title
  "Stopped".

## Quick self-review

1. Does this work need a plan, or would a status or timeline task updates be enough?
2. Does each task title name the action, in plain language, with the facts in the details?
3. Do statuses change live, do write actions stand out, and are retries labeled?
4. Are `details` and `output` short (under 256 characters when streamed), sent once, free of raw
   JSON, with sources on the task that used them?
5. If a step fails, do people see what worked, what didn't, and what they can do next?
6. Does the plan title end as the outcome ("Worked for…", "Error", "Stopped"), with no task left
   spinning?
7. Is the final answer complete on its own, with the plan clearly secondary?
