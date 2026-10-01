# Modal and Form Design

Guidance on modals and forms that are quick to fill in and hard to get wrong. Like
`design-principles.md`, this covers _appropriateness_, not validity: `blocks.validate` tells you
whether a view parses, and this tells you whether it works for the person filling it in. For the
view object's fields and the full modal lifecycle, see `https://docs.slack.dev/surfaces/modals.md`
and `https://docs.slack.dev/reference/views/modal-views.md`. Apply these principles unless the
developer explicitly asks otherwise.

## Decide whether it should be a modal at all

A modal interrupts the user. Use one only for short, focused work that the user started:

- **Use a modal** to collect structured input (a form), to confirm a consequential action with
  more context than a `confirm` dialog can hold, or to show details on demand.
- **Use a message** for a decision one or two buttons can capture (Approve / Reject). A modal
  adds a click and hides the decision from everyone else in the channel.
- **Use the App Home** for persistent settings or a dashboard the user returns to. Modals are
  short-lived and their state is lost when they close.
- **Never open a modal the user didn't ask for.** A modal needs a `trigger_id` from the user's
  own interaction, and that trigger expires after 3 seconds. Open the modal right away, and show a
  loading view if the data isn't ready yet (see **Loading, success, and failure** below).
- **Never ask for passwords or other credentials.** Send the user to your own sign-in flow.

## Frame the modal

- **Title says what the form is**, in 24 characters or fewer: "New incident", "Request time off".
  Leave out the app name; Slack already shows it.
- **Submit label is the outcome, as a verb**: "Create Incident", "Send Request", "Save". Never
  "Submit" or "OK" when a specific verb fits. It is limited to 24 characters, and `submit` is
  required whenever the view contains an `input` block.
- **Close label is "Cancel"** unless closing does something other than discard the form. Use
  "Done" for a modal that only shows information, and "Save" (never "Done") for one that commits
  changes.
- **Let Submit be the only emphasized button.** Slack renders it as the modal's main action, so
  leave buttons inside the view's blocks unstyled (or `danger` for a destructive one).
- **Say what submitting will do** when it isn't obvious from the label, especially if it sends
  something on the user's behalf: "This sends a message to #incidents and pages the on-call
  engineer." Put it in a
  `context` block just above the inputs, or in the modal's first `section`.
- **Lead with a short `section`** only when the user needs instructions. A form whose labels are
  clear doesn't need a paragraph introducing it.

## Inputs

Each `input` block holds one field: a label, an element, and optionally a hint.

- **Every input gets a label that names the value**, in sentence case: "Due date", "Affected
  service". Not a question, and not "Please enter…".
- **Use `hint` for constraints and format** ("Use the service's PagerDuty name"). It stays visible
  below the field. Use `placeholder` only for an example value ("Ex. api-gateway"). Placeholders
  disappear as soon as the user starts typing, so they must never carry instructions the user
  needs.
- **Mark optional fields as `optional: true`** rather than putting "(optional)" in the label.
  Inputs are required by default, so think about each field: if your handler can work without it,
  make it optional.
- **Pre-fill what you already know** with `initial_value`, `initial_option(s)`, `initial_date`,
  `initial_user`, or `initial_conversation`. Reviewing a pre-filled value is faster than typing
  it. For a conversation picker opened from a channel, set `default_to_current_conversation`.
- **Put `focus_on_load` on the first field** the user should fill in (at most one per view).
- **Pick the element that constrains the answer** so you don't have to validate free text:

  | The answer is… | Use |
  |---|---|
  | one of 2–5 visible choices | `radio_buttons` |
  | one of many | `static_select` (up to 100 options), or `external_select` for a large or live list |
  | several from a list | `checkboxes` (up to 10 options) or `multi_static_select` |
  | a person, channel, or conversation | `users_select`, `conversations_select` (and multi variants) |
  | a date, time, or both | `datepicker`, `timepicker`, `datetimepicker` |
  | a number, email, or URL | `number_input`, `email_input`, `url_input` |
  | short or long free text | `plain_text_input` (`multiline: true` for long text, `max_length` to cap it) |
  | formatted text | `rich_text_input` |
  | a file | `file_input` |

- **Order fields the way the user thinks about the task**: the most important or identifying
  field first ("Title"), details after, optional fields last.

## Keep it short

- **Ask only for what you need now.** Every field costs the user time. Slack's guidance is to
  split the form once it reaches about six inputs.
- **Split a long form into steps** with `response_action: "push"` (or `views.push` from a button
  inside the modal). A modal holds at most 3 views in its stack, so plan for no more than three
  steps. Carry earlier answers forward in `private_metadata` (up to 3,000 characters), not in
  hidden fields.
- **Use `views.update` to show or hide dependent fields** in place. Set `dispatch_action: true`
  on the controlling input so changing it sends a `block_actions` payload, then update the view.
  Keep the same `block_id` and `action_id` on every input so the user's entries are kept, and pass
  the payload's `hash` so a stale update can't overwrite a newer one.
- **Don't push a view for something that fits in the current one.** Each pushed view is another
  screen the user has to get through, and another Cancel that might send them back.

## Validation and errors

- **Validate on submit and respond with `response_action: "errors"`**, keyed by the input's
  `block_id`: `{ "response_action": "errors", "errors": { "due_date": "Pick a date in the future" } }`.
  The error appears under that field and the modal stays open with everything the user entered.
  You have 3 seconds to respond.
- **Write errors that say how to fix the problem**: "Pick a date in the future", not "Invalid
  date". Don't just repeat the label.
- **Don't blame the user or apologize.** "This email address doesn't look quite right", not "You
  entered an invalid email address" or "Sorry, that's invalid". "You don't have permission…" is
  fine.
- **Show every field error at once**, not one per submit.
- **Constrain input before you validate it.** A `datepicker`, `number_input` with `min_value`, or
  a select prevents errors that a free-text field would need a message for.
- **For a problem with the whole form**, not one field (for example "That incident was already
  closed"), update the view with `response_action: "update"` and put an `alert` block at the top
  with `level: "error"`. `alert` is available only in modals.

## Loading, success, and failure

- **For slow work, open the modal first with a loading view.** Show a short `section` such as
  "Loading your projects…", then fill it in with `views.update` when the data arrives. Don't
  hold the `trigger_id` while you fetch data: it expires after 3 seconds.
- **For slow submissions**, acknowledge with `response_action: "update"` to a "Creating
  incident…" view, do the work, then `views.update` that view to the result.
- **Confirm what happened after submit.** Either close the modal and post the result where the
  user will see it (an ephemeral message, a DM, or the thread the flow started in, with a link to
  what was created), or update the modal to a success view with an `alert` at `level: "success"`
  and a link. Don't close silently.
- **When submission fails on your side**, keep the user's input. Return `errors` or an `update`
  with an `alert` that says what went wrong and what to try next. Never close the modal and
  throw the form away.
- **Close the whole stack when the flow is done** with `response_action: "clear"`, so the user
  doesn't land back on an earlier step of a form they already finished.
- **Handle Cancel gracefully.** Set `notify_on_close: true` if you need to clean up (release a
  lock, delete a draft). Don't reopen the modal or nag the user to finish.

## Destructive and consequential actions

- **Use a `confirm` dialog** on a button for a single irreversible action. Keep its title to the
  action, with no end punctuation ("Delete incident"), its text to the consequence, and its confirm label to the
  verb ("Delete"). Set `style: "danger"` on the confirm dialog itself.
- **Use a review view instead** when the user needs to see what will happen before confirming,
  such as a bulk change, a message that will be posted, or anything that sends on their behalf.
  Push a view that summarizes the result, with the Submit label stating the action ("Send to 42 People").

## Quick self-review

Before handing back a modal, check:

1. Is a modal the right surface, and does the title say what the form is in 24 characters or
   fewer?
2. Does the Submit label name the outcome, and is it clear what submitting will do?
3. Does every input have a clear label, constraints in `hint` (not `placeholder`), and the right
   `optional` setting?
4. Are known values pre-filled, and does the element limit the possible answers wherever it can?
5. Is the form six inputs or fewer per view, and three views or fewer in the stack?
6. What does the user see while loading, on a validation error, on success, and on failure?
