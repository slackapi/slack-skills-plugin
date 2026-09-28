# Block Kit Design Principles

Guidance on building layouts that read well, not on whether they parse. Validity — required
fields, allowed element nesting, per-surface block support — is what `blocks.validate` checks.
These principles are about _appropriateness_: reaching for the block that fits the shape of the
content, and arranging it so a reader takes it in at a glance. Apply them unless the developer
explicitly asks otherwise.

## Reach for the block that fits the shape of the content

Don't stack `section` + `divider` text when a purpose-built block fits better, and don't add
structure to content that doesn't need it. Match the block to what the content _is_:

- **Tabular or comparable rows** (metrics, line items, a leaderboard) belong in a `table`.
  Stacked sections force the reader to scan prose; a table aligns columns so values compare at a
  glance.
- **One rich entity the message is about** (an alert, an incident, a record, a PR) belongs in a
  `card`. A card groups the entity's title, body, and actions into one bounded unit instead of
  loose blocks.
- **A browsable set of peer items the reader chooses among** (a catalog, options, search results)
  belongs in a `carousel` of cards — horizontal browsing instead of an ever-growing vertical
  stack.
- **A status update or an approval** (one subject plus a decision) is well served by a `header`
  for the title, a `section` with `fields` for the key/value details, and an `actions` block for
  the buttons.
- **Multi-step work an agent is doing** (a plan, a checklist of tool calls) belongs in a `plan`
  of `task_card`s, each with a `status` — not a growing wall of "Step 3 done ✅" text.
- **A one-line notice with no structure** should stay plain text. Don't add blocks for their own
  sake; wrapping a one-line status in a `card` or a table works against the content, not for it.

Avoid `divider` between every block. Use it only to separate genuinely distinct groups; a
`header` or the edge of a `card` usually does the job better.

### Know where each block works and how much it holds

A block that fits the content can still be the wrong choice for the surface, and each block has
limits:

| Block | Surfaces | Holds at most |
|---|---|---|
| `table` | messages, App Home | 100 rows × 20 cells; 10,000 chars across cells per message |
| `carousel` | messages, App Home | 1–10 cards |
| `card` | messages, modals, App Home | 3 actions; title 150 chars, body 200 chars |
| `markdown` | messages only | 12,000 chars across all markdown blocks in the payload |
| `plan` / `context_actions` | messages only | 50 task cards / 5 elements |
| `section` `fields` | all | 10 fields, 2,000 chars each |
| _(whole surface)_ | — | 50 blocks per message; 100 per modal or App Home |

In a modal, where `table` and `carousel` aren't available, use a `section` with `fields` for key/value
data. For content that would go over these limits, summarize and link out; don't split
it across messages.

## Emphasis and actions

- **Emphasize one button at most per `actions` block.** Use `primary` for the single main or
  confirming action (Approve, Submit, Save). Use `danger` only when the _main_ action is
  destructive (Delete, Remove). In an Approve/Reject pair, `primary` goes on Approve and Reject
  stays unstyled. Leave secondary or neutral actions (Cancel, links) unstyled. If everything is
  emphasized, nothing is.
- **Label buttons with specific verbs** ("Approve request", "Open incident"), never "Click here"
  or "OK". The label, not the red or green style, must say what the button does.
- **Keep the visible action set small.** Put two or three actions inline and move advanced or
  rare ones into an `overflow` menu.
- **Guard destructive actions with a confirmation dialog** (`confirm`) so an accidental click
  can't do irreversible harm.

## Layout and reading order

- **Order blocks top-to-bottom in reading order:** lead with a `header` for the title, then the
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
- **When a flow is finished, remove its controls.** Replace the `actions` block with a
  `context` line recording the outcome ("Approved by <@U123> · 10:42"), so stale buttons can't be
  clicked again.
- **Keep `action_id`s stable** across updates so handlers keep matching. Give an updated message
  a **new `block_id`**, so interactions from an older copy can be told apart.

## Text: rich_text, mrkdwn, and the markdown block

- **Formatted text you build in code** (lists, quotes, code blocks, mentions, links) belongs in
  a `rich_text` block. It is the composer's native format and Slack's preferred one.
- **Short text inside a `section` or `context`** uses Slack `mrkdwn`: `*bold*`, `_italic_`,
  `~strike~`, `` `code` ``. This is Slack's syntax, not `**bold**`.
- **Long-form or AI/LLM-generated content that already exists in standard markdown** (headings,
  tables, numbered lists, `**bold**`) belongs in a `markdown` block (messages only). Its
  `block_id` is not preserved and images render as links. Use it for body content, not for
  anything you'll need to find again or update. Don't translate LLM markdown into mrkdwn by hand.

## AI and agent output

- **Show work in progress as structure:** use a `plan` / `task_card` for steps, and switch each
  card's `status` to `complete` or `error` as the work happens.
- **When streaming, send blocks in the final call** (`chat.stopStream`), not in the stream
  chunks.
- **Collect feedback with `feedback_buttons`** inside a `context_actions` block at the end of the
  response, instead of hand-rolled thumbs-up and thumbs-down buttons.
- **Cite sources, and ask before acting.** Put an explicit `confirm` or Approve/Cancel choice on
  anything that creates, sends, or deletes on the user's behalf.

## Accessibility and fallback

Accessibility is easy to skip and hard to retrofit, so build it in from the start:

- **Summarize the layout in a message's top-level `text` fallback.** Notifications and screen
  readers show it instead of the blocks. State the point and any action needed ("Deploy failed
  on prod-3 — approval needed to roll back"), not a generic "New message". An empty fallback
  leaves those readers with nothing, and `blocks.validate` won't warn you.
- **Give images descriptive `alt_text`** (what the image shows, not just "image"). Make sure
  image-heavy layouts also carry the key information as text. If an image is purely decorative,
  drop it.
- **Never use color as the only signal.** A red `danger` button, an emoji, or an `alert` level
  needs words that say the same thing.
- **Use emoji alongside text, never instead of it.** Don't use them as bullets or as the only
  label on a control. Keep them few.
- **Set `accessibility_label` on buttons** whose visible text is ambiguous out of context
  ("View", "Open").
- **Use `header` blocks for logical section headings.** They convey document structure to
  assistive tech. They take `plain_text` only, up to 150 chars.
- **Avoid directional references** such as "see above" or "the button on the right". Layouts
  reflow on mobile and are read linearly by screen readers.

## Quick self-review

Before handing back a layout, check:

1. Does each block match the shape of its content, and is it supported on this surface?
2. Does the first line (and the `text` fallback) say the point?
3. Is at most one button emphasized, and are destructive actions confirmed?
4. Is metadata in `context`, and is the reading order header → content → actions → context?
5. Will this message be updated? If so, how does it look when the flow finishes?
6. Can someone who can't see colors, emoji, or images still understand it?
