# Human-in-the-Loop Design: Approvals, Choices, and Review

Guidance on Block Kit layouts where a person has to decide before an app or agent continues:
approval gates, sets of proposed actions to approve together, clarifying choices, and
edit-before-send. It builds on `design-principles.md`. For the underlying guidance, see Slack's
agent design guide (`https://docs.slack.dev/concepts/agent-design.md`, "Confirmation and
control") and governance guide (`https://docs.slack.dev/ai/agent-governance.md`). Apply these
principles unless the developer explicitly asks otherwise.

## Decide when to ask

- **Ask before anything that creates, sends, deletes, or spends**, and before acting as someone in
  a way other people will see. Reads and drafts don't need a gate.
- **Ask when the request is ambiguous** and more than one reasonable path exists. Offer the paths
  as choices rather than guessing.
- **Avoid asking about everything.** Confirming every step teaches people to click through
  without reading. Save gates for actions that matter, and let people stop being asked about a
  class of action once they trust it (see **Earn trust over time** below).
- **Match the gate to the stakes.** A reversible, low-impact action can go ahead and offer Undo
  afterwards. An irreversible or high-impact one needs approval first, and possibly a `confirm`
  dialog on top.
- **Write the policy down as lists, not case-by-case judgment.** A gate is easiest to trust when
  it's predictable:
  - **Always ask** for destructive actions (delete, cancel, archive, revoke, forget) and for
    outbound actions that reach other people (send, post, share, invite, forward).
  - **Don't ask** for cheap, reversible, or self-scoped actions (add a reaction, pin a message,
    save a note to the person's own memory, create a draft).
  - **Check unfamiliar tools for the same verbs**, such as tools from a connected MCP server
    (`gmail_send_email`, `calendar_event_delete`), and ask when one appears.

## Pick the pattern

| The decision is… | Use |
|---|---|
| go / don't go on one action | **Approval gate**: a preview, then Approve / Edit / Cancel |
| several proposed actions at once | **Approval set**: one message that lists every item, with a way to choose which to approve |
| which of a few paths to take | **Clarifying choice**: one button per option, each with a line of context |
| the content itself, before it's sent | **Edit before send**: a modal pre-filled with the draft |
| a sign-off from someone else | **Request to an approver**: a message to the approver, with the outcome sent back to the requester |

### Approval gate

- **Preview exactly what will happen**, so approval is an informed choice: the message that will
  be posted, the issue that will be filed, the recipients. Use a `section` with `fields` for
  key/value details, a `card` for a single entity, or a `rich_text` quote for draft text.
- **State the action and its scope in the first line**: "Send this summary to #eng (212
  members)?", not "Ready to proceed?" or "Confirm this action".
- **Describe the target by name, not by ID**: "Delete the canvas Q3 planning", not "Delete
  `F0123ABC`".
- **Use specific verbs on the buttons**: "Send Summary", "Edit", "Cancel". Emphasize only the
  approving button (see `design-principles.md`, **Emphasis and actions**). Leave Reject or Cancel
  unstyled: declining is the safe choice, and a red button suggests it's the dangerous one.
- **Offer a way to change it, not just yes or no.** An Edit button that opens a pre-filled modal
  (see **Edit before send**) prevents a reject-and-retry loop.
- **Show whose identity the action uses**: "Will be sent as you" or "Posted by the app on behalf
  of <@U123>", in a `context` block next to the actions.
- **Keep personal approvals private in a shared channel** with an ephemeral message, so other
  members don't see or click them.

### Approval set

When an agent proposes several actions ("Create these 5 issues", "Send these 3 replies"), put them
in one message rather than one message per item.

- **List every item with enough detail to judge it**, one item per line: a `section` per item
  with the key details in `fields` for a handful of items, or a `table` for many items with the
  same columns.
- **Let people choose which items to approve.** Two layouts work well:
  - **Select, then approve once** (best for 2–10 items): a `checkboxes` element with one option per
    item, every item checked by default, followed by an `actions` block with "Approve Selected"
    (`primary`) and "Cancel". The **Approval Set** pattern in `common-patterns.md` is a starting
    template.
  - **Decide per item**: a `section` per item with an `overflow` accessory (Approve, Skip, Edit),
    or a `data_table` with an `action_cell` button per row, plus "Approve All Remaining" at the
    end. Update the item's line in place as each decision comes in.
- **Show the totals in the button and the fallback**: "Approve 4 of 5", and `text` "5 issues
  ready to create, approval needed".
- **Replace the controls with a record after the decision** (see **Close the loop** below), so the
  message shows exactly what was approved and what was skipped.

### Clarifying choice

- **Offer two to four concrete options as buttons**, each labeled with what the agent will do:
  "Summarize Last Week", "Summarize Since Incident". Add a line of context for each in the
  `section` above (or use a `radio_buttons` element when the options need descriptions).
- **Include a way out**: "Something Else" opens a short modal or invites a reply in the thread.
- **Leave every option unstyled** unless one is clearly the recommended default.

### Edit before send

- **Open a modal pre-filled with the draft** from the Edit button. Name the submit label after the
  action ("Send Summary"), so editing and approving happen in one step.
- **Show the edited version in the message once it's sent**, so the record reflects what went out
  and not the original draft.

### Request to an approver

When the person who approves isn't the person who asked (expense sign-off, access requests,
deploy gates):

- **Send the request where the approver will act on it**: a DM to a named approver, or a post in
  an approvals channel for a group. Give the requester a separate message showing that the
  request is pending.
- **Name the requester and the reason up front**: "<@U123> requests prod database access for
  INC-482". Put supporting details in `fields`.
- **Record each approval in place** for N-of-M sign-offs: a `context` line such as "Approved by
  <@U234> · 1 of 2 needed", updated as each approver responds.
- **Send the outcome back to the requester**, whichever way the decision went, and include the
  approver's reason when rejecting.

## Close the loop

- **Replace the controls once a decision is made.** Update the message so the `actions` block
  becomes a `context` line: "Created 2 of 3 issues · Approved by <@U123> · 10:42". Buttons that
  stay up after the decision invite duplicate clicks. For a declined action, keep the preview but
  strike it through, followed by the outcome: `~Delete the canvas Q3 planning~ Rejected, I won't
  run it.`
- **Give every request a way to end without an answer.** An agent waiting on approval holds up the
  whole run. Every pending approval should settle exactly once, in one of these ways:

  | Ending | What happens | Message becomes |
  |---|---|---|
  | approved | the action runs | "Approved, running it now", then the result |
  | rejected | the action is skipped | "Rejected, I won't run it." |
  | timed out (minutes for an agent's in-run gate, longer for a human sign-off) | the action is skipped | "Timed out, I didn't run it." |
  | run stopped | the action is skipped | "Cancelled, the request was stopped." |

- **Never treat an unanswered gate as a yes.** If the prompt fails to post, the request times out,
  or the run is cancelled, treat it as a rejection.
- **Show the result, not just the decision.** Link to what was created or sent. If an item failed
  after approval, say which one and why.
- **Update the original message in a channel** rather than replying with a new one, so nobody
  else approves something that was already handled.
- **Expire stale requests.** If the decision no longer matters (the deploy window passed, the
  draft was replaced), update the message to say so and remove the buttons.

## Earn trust over time

- **Offer Undo after reversible actions** that ran without a gate: a "Created LIN-204 · Undo"
  `context` line, or a button that expires after a short window.
- **Offer "Always Allow" for a class of action** once someone has approved it a few times, as a
  secondary button next to the main approval ("Approve" and "Always Allow in #eng"). Honor it, and
  give people a place to revoke it, such as the App Home.
- **Let people review what the agent did on their behalf**, especially for asynchronous or bulk
  work. An App Home log of recent actions works well for this (see `home-tab-design.md`, **A
  review surface for agents**).

## Implementation notes

The layout has to support these handler responsibilities:

- **Check who clicked.** Anyone who can see a message can click its buttons. Check that the
  `user.id` in the interaction payload is allowed to approve, and if not, respond with an
  ephemeral message ("Only <@U234> can approve this request") without changing the original.
- **Make the decision idempotent.** Two approvers, or one double-click, can send two payloads.
  Put a unique request ID in the button's `value` (or `private_metadata` in a modal), settle that
  ID once, and ignore later clicks, including ones that arrive after a timeout.
- **Approve exactly what was shown.** If the proposal changes, post or update it with a new
  `block_id`, so a click on the old version can be recognized and rejected.
- **Read an approval set's final selection from `state.values`** in the button's payload. Each
  checkbox change also sends its own `block_actions` payload, which the handler can just
  acknowledge.
- **Close the loop with `chat.update`**, or `replace_original` via `response_url`. A
  `response_url` works for only 30 minutes (up to 5 uses), so use `chat.update` for decisions that
  may take longer.
- **Send personal approvals ephemerally** with `response_type: "ephemeral"` via `response_url`,
  or `chat.postEphemeral`.
- **Pre-fill an edit modal** with `initial_value` on a `plain_text_input` or `rich_text_input`.
- **Let each tool supply its own preview text** when it knows the human-readable names, and fall
  back to a generic description built from the arguments only when it doesn't.

## Quick self-review

1. Does this action need a gate, and does the gate match the stakes?
2. Does the preview show exactly what will happen, with the action and scope in the first line?
3. Are the buttons specific verbs, with one `primary`, and is there a way to edit rather than only
   reject?
4. For several items, is it one message where people can approve some and not others?
5. After the decision, are the controls replaced by a record of what happened?
6. Does every request end, by timeout or cancellation if not by a click, and does that ending
   default to not running the action?
7. Does the handler check who clicked, ignore duplicate clicks, and reject clicks on outdated
   versions?
