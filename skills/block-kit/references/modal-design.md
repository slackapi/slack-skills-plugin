# Modal and Form Design

Guidance on modals and forms that are quick to fill in and hard to get wrong. It builds on
`design-principles.md`: `blocks.validate` tells you whether a view parses, and this tells you
whether it works for the person filling it in. For the view object's fields and the full modal
lifecycle, see `https://docs.slack.dev/surfaces/modals.md` and
`https://docs.slack.dev/reference/views/modal-views.md`. Apply these principles unless the
developer explicitly asks otherwise.

## Decide whether it should be a modal at all

A modal interrupts people. Use one only for short, focused work that someone started:

- **Use a modal** to collect structured input (a form), to confirm a consequential action with
  more context than a `confirm` dialog can hold, or to show details on demand.
- **Use a message** for a decision one or two buttons can capture (Approve / Reject). A modal
  adds a click and hides the decision from everyone else in the channel.
- **Use the App Home** for persistent settings or a dashboard people return to. Modals are
  short-lived and their state is lost when they close.
- **Never open a modal someone didn't ask for.** A modal needs a `trigger_id` from that person's
  own interaction, and the trigger expires after 3 seconds. Open the modal right away, and show a
  loading view if the data isn't ready yet (see **Loading, success, and failure** below).
- **Never ask for passwords or other credentials.** Send people to your own sign-in flow.

## Frame the modal

- **Write a title that says what the form is**, in 24 characters or fewer: "New incident",
  "Request time off". Leave out the app name; Slack already shows it.
- **Label Submit with the outcome, as a verb**: "Create Incident", "Send Request", "Save". Avoid
  "Submit" or "OK" when a specific verb fits.
- **Label Close "Cancel"** unless closing does something other than discard the form. Use "Done"
  for a modal that only shows information (see `design-principles.md`, **Words and labels**).
- **Say what submitting will do** when the label doesn't make it obvious, especially if it sends
  something on the person's behalf: "This sends a message to #incidents and pages the on-call
  engineer." Put it in a `context` block just above the inputs, or in the modal's first
  `section`.
- **Add an introductory `section` only when people need instructions.** A form whose labels are
  clear doesn't need a paragraph introducing it.

Submit is the modal's main action, so leave buttons inside the view unstyled (see
`design-principles.md`, **Emphasis and actions**).

## Inputs

Each `input` block holds one field: a label, an element, and optionally a hint.

- **Give every input a label that names the value**, in sentence case: "Due date", "Affected
  service". Avoid questions and "Please enter…".
- **Put constraints and format in `hint`** ("Use the service's PagerDuty name"). It stays visible
  below the field. Use `placeholder` only for an example value ("Ex. api-gateway"). Placeholders
  disappear as soon as someone starts typing, so don't put instructions in them.
- **Mark optional fields with `optional: true`** rather than putting "(optional)" in the label.
  Inputs are required by default, so think about each field: if your handler can work without it,
  make it optional.
- **Pre-fill what you already know.** Reviewing a pre-filled value is faster than typing it.
- **Put `focus_on_load` on the first field** people should fill in (at most one per view).
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

- **Order fields the way people think about the task**: the most important or identifying field
  first ("Title"), details after, optional fields last.

## Keep it short

- **Ask only for what you need now.** Every field costs people time. Once a form reaches about
  six inputs, split it.
- **Split a long form into steps**, no more than three: a modal's stack holds at most 3 views.
- **Show or hide dependent fields in place** rather than pushing a new view for them.
- **Avoid pushing a view for something that fits in the current one.** Each pushed view is
  another screen to get through, and another Cancel that might send people back.

## Validation and errors

- **Validate on submit and show the error under the field**, with the modal still open and
  everything the person entered still there.
- **Write errors that say how to fix the problem**: "Pick a date in the future", not "Invalid
  date". Don't just repeat the label.
- **Don't blame people or apologize.** "This email address doesn't look quite right", not "You
  entered an invalid email address" or "Sorry, that's invalid". "You don't have permission…" is
  fine.
- **Show every field error at once**, not one per submit.
- **Constrain input before you validate it.** A `datepicker`, a `number_input` with `min_value`,
  or a select prevents errors that a free-text field would need a message for.
- **Put a problem with the whole form in an `alert` at the top** with `level: "error"`, for
  example "That incident was already closed".

## Loading, success, and failure

- **For slow work, open the modal first with a loading view.** Show a short `section` such as
  "Loading your projects…", then fill it in when the data arrives.
- **For slow submissions, show a working view** ("Creating incident…"), then replace it with the
  result.
- **Confirm what happened after submit.** Either close the modal and post the result where the
  person will see it (an ephemeral message, a DM, or the thread the flow started in, with a link
  to what was created), or update the modal to a success view with an `alert` at
  `level: "success"` and a link. Don't close silently.
- **Keep people's input when submission fails on your side.** Show an error or an `alert` that
  says what went wrong and what to try next. Don't close the modal and throw the form away.
- **Close the whole stack when the flow is done**, so people don't land back on an earlier step of
  a form they already finished.
- **Handle Cancel gracefully.** Clean up if you need to (release a lock, delete a draft), and
  don't reopen the modal or nag people to finish.

## Destructive and consequential actions

- **Use a `confirm` dialog** on a button for a single irreversible action. Keep its title to the
  action, with no end punctuation ("Delete incident"), its text to the consequence, and its
  confirm label to the verb ("Delete"). Set `style: "danger"` on the confirm dialog itself.
- **Use a review view instead** when people need to see what will happen before confirming, such
  as a bulk change, a message that will be posted, or anything that sends on their behalf. Push a
  view that summarizes the result, with the Submit label stating the action ("Send to 42 People").

## Implementation notes

- **Fit the frame's limits.** The title and the Submit label each hold 24 characters, and
  `submit` is required whenever the view contains an `input` block.
- **Pre-fill with the element's initial field**: `initial_value`, `initial_option(s)`,
  `initial_date`, `initial_user`, or `initial_conversation`. For a conversation picker opened from
  a channel, set `default_to_current_conversation`.
- **Push steps** with `response_action: "push"`, or `views.push` from a button inside the modal.
  Carry earlier answers forward in `private_metadata` (up to 3,000 characters), not in hidden
  fields.
- **Update dependent fields with `views.update`.** Set `dispatch_action: true` on the controlling
  input so changing it sends a `block_actions` payload. Keep the same `block_id` and `action_id`
  on every input so entries are kept, and pass the payload's `hash` so a stale update can't
  overwrite a newer one.
- **Return field errors with `response_action: "errors"`**, keyed by the input's `block_id`:
  `{ "response_action": "errors", "errors": { "due_date": "Pick a date in the future" } }`. You
  have 3 seconds to respond.
- **Show a form-level `alert` or a working view with `response_action: "update"`**, then
  `views.update` to the result when slow work finishes. Don't hold the `trigger_id` while you
  fetch data.
- **Close the stack with `response_action: "clear"`.**
- **Set `notify_on_close: true`** to receive a `view_closed` event when someone cancels.

## Quick self-review

Before handing back a modal, check:

1. Is a modal the right surface, and does the title say what the form is in 24 characters or
   fewer?
2. Does the Submit label name the outcome, and is it clear what submitting will do?
3. Does every input have a clear label, constraints in `hint` (not `placeholder`), and the right
   `optional` setting?
4. Are known values pre-filled, and does the element limit the possible answers wherever it can?
5. Is the form six inputs or fewer per view, and three views or fewer in the stack?
6. What do people see while loading, on a validation error, on success, and on failure?
