# Block Kit Design Principles

Guidance on building layouts that read well, not on whether they parse. Validity — required
fields, allowed element nesting, per-surface block support — is what `blocks.validate` checks.
These principles are about _appropriateness_: reaching for the block that fits the shape of the
content, and arranging it so people take it in at a glance. Apply them unless the developer
explicitly asks otherwise.

These principles apply to every surface, and the companion references build on them rather than
repeating them: `modal-design.md` (modals and forms), `home-tab-design.md` (App Home),
`data-display-design.md` (fields, tables, and charts), `agent-progress-design.md` (plans and
task cards), and `human-in-the-loop.md` (approvals and choices).

## Reach for the block that fits the shape of the content

Don't stack `section` + `divider` text when a purpose-built block fits better, and don't add
structure to content that doesn't need it. Match the block to what the content _is_:

- **Put tabular or comparable rows in a `table`** (metrics, line items, a leaderboard). Stacked
  sections make people scan prose; a table aligns columns so values compare at a glance. When
  people need to page, sort, or act on rows (more than a screenful, or a button per row), use a
  `data_table` instead.
- **Put a trend, comparison, or share of a whole in a `data_visualization` chart** (deploys per
  day, spend by team), and state the key number in text as well. `data-display-design.md` covers
  choosing between fields, tables, and charts.
- **Put one rich entity in a `card`** (an alert, an incident, a record, a PR). A card groups the
  entity's title, body, and actions into one bounded unit instead of loose blocks.
- **Put a browsable set of peer items in a `carousel` of cards** (a catalog, options, search
  results), so people browse horizontally instead of scrolling an ever-growing vertical stack.
- **Build a status update or an approval from a `header`, a `section` with `fields`, and an
  `actions` block**: the title, the key/value details, then the buttons.
- **Show multi-step agent work as a `plan` of `task_card`s** (a plan, a checklist of tool
  calls), each with a `status`, rather than a growing wall of "Step 3 done ✅" text.
- **Group related blocks in a `container`** (a record's details, an optional breakdown), with a
  title and, for secondary detail, `is_collapsible` so it starts collapsed. It holds up to 10
  child blocks, but not `card`, `carousel`, or `data_table`.
- **Put a notice about a whole modal in an `alert` block** (a validation problem, a success
  state, a warning before submitting). `alert` is available only in modals, so in a message,
  state the level in words ("Deploy failed", "Warning:") in a `header` or `section`.
- **Put a status, a date, or a source inside text as a `rich_text` inline element**: a `tag` for
  a status pill ("In progress"), a `date` for a timestamp that shows in each person's own
  timezone and format, and a `citation` for an AI answer's source.
- **Keep a one-line notice with no structure as plain text.** Wrapping a one-line status in a
  `card` or a table works against the content, not for it.

Avoid a `divider` between every block. Use one only to separate genuinely distinct groups; a
`header` or the edge of a `card` usually does the job better.

### Know where each block works and how much it holds

A block that fits the content can still be the wrong choice for the surface, and each block has
limits:

| Block | Surfaces | Holds at most |
|---|---|---|
| `table` | messages, App Home | 100 rows × 20 cells; 10,000 chars across cells per message |
| `data_table` | messages, App Home | 200 rows + header × 20 columns; 20,000 chars across cells per message |
| `data_visualization` | messages, App Home | 2 per message; 12 series or slices; 20 points per series |
| `carousel` | messages, App Home | 1–10 cards |
| `card` | messages, modals, App Home | 3 actions; title 150 chars, body 200 chars |
| `container` | messages, App Home | 10 child blocks; title 150 chars |
| `alert` | modals only | 200 chars |
| `markdown` | messages only | 12,000 chars across all markdown blocks in the payload |
| `plan` / `context_actions` | messages only | 50 task cards / 5 elements |
| `section` `fields` | all | 10 fields, 2,000 chars each |
| _(whole surface)_ | — | 50 blocks per message; 100 per modal or App Home |

In a modal, where `table` and `carousel` aren't available, use a `section` with `fields` for
key/value data. For content that would go over these limits, summarize and link out first. For a
large table, a paginated `data_table` comes next. Split content across messages only as a last
resort: people can't sort, search, or act on it as one set, and every extra message is another
notification.

## Emphasis and actions

- **Emphasize at most one button per message or view**, not per `actions` block. If the layout
  has one clear main action, make it `primary` (Approve, Save, Send). Use `danger` only when the
  _main_ action is destructive (Delete, Remove). In an Approve/Reject pair, `primary` goes on
  Approve and Reject stays unstyled. When the buttons are equal choices (clarifying options, row
  actions, filters), leave them all unstyled. If everything is emphasized, nothing is.
- **Treat Submit as a modal's main action.** Slack already emphasizes it, so leave buttons inside
  the view's blocks unstyled rather than adding a `primary` one to compete with it.
- **Label buttons with specific verbs** ("Approve Request", "Open Incident"), not "Click Here".
  The label, not the red or green style, must say what the button does.
- **Keep the visible action set small.** Put two or three actions inline and move advanced or
  rare ones into an `overflow` menu.
- **Guard destructive actions with a confirmation dialog** (`confirm`) so an accidental click
  can't do irreversible harm.

## Words and labels

Match the conventions of Slack's own UI, so an app reads like part of Slack:

- **Use Title Case for action button labels** ("Approve Request", "View Logs"). **Use sentence
  case for everything else**: `header` text, modal titles, input labels, menu and `overflow`
  options, links, and `context` text.
- **Leave end punctuation off headings**: "Deploy failed on prod-3", not "Deploy failed on
  prod-3."
- **Use Save for a button that commits changes and Done for one that only closes.** Don't label a
  button that saves "Done", or one that only closes "Save".

## Layout and reading order

- **Order blocks top to bottom in reading order.** Lead with a `header` for the title, then the
  content `section`s, then any `actions`, then a trailing `context` block for footnotes. Don't
  bury the title in the middle of the layout.
- **Put the point first.** The first line should say what happened or what's needed ("Deploy
  failed on prod-3", "Your approval is needed"). Background comes after that.
- **Put secondary or metadata text in a `context` block, not a `section`**: attribution,
  timestamps, status, help links. Separate multiple fragments with " · " (for example,
  "Posted by <@U123> · 2 min ago").

## Messages that change over time

- **Update the message in place** (`chat.update`, or `replace_original` via `response_url`) for
  progress and state changes. Don't post a new message for each step.
- **Remove a flow's controls when it's finished.** Replace the `actions` block with a `context`
  line recording the outcome ("Approved by <@U123> · 10:42"), so stale buttons can't be clicked
  again.

## Text: rich_text, mrkdwn, and the markdown block

- **Build formatted text in code as a `rich_text` block** (lists, quotes, code blocks, mentions,
  links). It's the composer's native format.
- **Format short text inside a `section` or `context` with Slack `mrkdwn`**: `*bold*`,
  `_italic_`, `~strike~`, `` `code` ``. This is Slack's syntax, not `**bold**`.
- **Put long-form or AI-generated content that's already in standard markdown in a `markdown`
  block** (messages only). Use it for body content, not for anything you'll need to find again
  or update, and don't translate LLM markdown into mrkdwn by hand.

## AI and agent output

- **Show work in progress as structure.** Use a `plan` of `task_card`s for steps, or
  `task_update` chunks when streaming. `agent-progress-design.md` covers when to use a plan, how
  to word steps, and how to handle failures.
- **Collect feedback with `feedback_buttons`** inside a `context_actions` block at the end of the
  response, instead of hand-rolled thumbs-up and thumbs-down buttons.
- **Cite sources where the claim is made.** In `rich_text`, use a `citation` element for each
  source. In mrkdwn, use inline links, with a `context` block listing references at the end.
- **Ask before acting.** Put an explicit `confirm` or Approve/Cancel choice on anything that
  creates, sends, or deletes on someone's behalf. `human-in-the-loop.md` covers approval gates,
  approving several actions in one message, and closing the loop afterwards.

## Accessibility and fallback

Accessibility is easy to skip and hard to retrofit, so build it in from the start:

- **Summarize the layout in a message's top-level `text` fallback.** Notifications and screen
  readers show it instead of the blocks. State the point and any action needed ("Deploy failed
  on prod-3 — approval needed to roll back"), not a generic "New message". An empty fallback
  leaves those people with nothing, and `blocks.validate` won't warn you.
- **Give images descriptive `alt_text`** (what the image shows, not just "image"). Make sure
  image-heavy layouts also carry the key information as text. If an image is purely decorative,
  drop it.
- **Don't rely on color alone.** A red `danger` button, an emoji, or an `alert` level needs words
  that say the same thing.
- **Use emoji alongside text, not instead of it, and only in running text.** Keep them out of
  buttons, menu options, labels, and headers, and don't use them as bullets. Keep them few.
- **Set `accessibility_label` on buttons** whose visible text is ambiguous out of context
  ("View", "Open").
- **Use `header` blocks for logical section headings.** They convey document structure to
  assistive tech. They take `plain_text` only, up to 150 chars.
- **Give tables and charts a text equivalent.** A `data_table` needs a `caption`, and
  `row_header_column_index` should point at the column that names each row. A chart needs its
  main takeaway in text next to it ("Deploys doubled week over week").
- **Avoid directional references** such as "see above" or "the button on the right". Layouts
  reflow on mobile and are read linearly by screen readers.

## Implementation notes

- **Keep `action_id`s stable across updates** so handlers keep matching. Give an updated message
  a new `block_id`, so interactions from an older copy can be told apart.
- **When streaming, send the rest of the layout in the final call** (`chat.stopStream`), so
  partly built blocks don't render mid-stream.
- **Expect a `markdown` block to lose its `block_id`** and to render images as links.

## Quick self-review

Before handing back a layout, check:

1. Does each block match the shape of its content, and is it supported on this surface?
2. Does the first line (and the `text` fallback) say the point?
3. Is at most one button `primary` in the whole message or view, and are destructive actions
   confirmed?
4. Is metadata in `context`, and is the reading order header → content → actions → context?
5. Will this message be updated? If so, how does it look when the flow finishes?
6. Can someone who can't see colors, emoji, or images still understand it?
7. Are buttons in Title Case and everything else in sentence case, with no end punctuation in
   headings and no emoji in buttons, labels, or headers?
