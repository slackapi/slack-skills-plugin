# Block Kit Design Principles

Guidance on building layouts that read well, not on whether they parse. Validity — required
fields, allowed element nesting, surface compatibility — is what `blocks.validate` checks. These
principles are about _appropriateness_: reaching for the block that fits the shape of the
content, and arranging it so a reader takes it in at a glance. Apply them unless the developer
explicitly asks otherwise.

## Reach for the block that fits the shape of the content

Don't stack `section` + `divider` text when a purpose-built block fits better, and don't add
structure to content that doesn't need it. Match the block to what the content _is_:

- **Tabular or comparable rows** (metrics, line items, a leaderboard) belong in a `table`.
  Stacked sections force the reader to scan prose; a table aligns columns so values compare at a
  glance.
- **One rich entity the message is about** (an alert, an incident, a record, a PR) belongs in a
  `card`. A card groups the entity's title, fields, and actions into one bounded unit instead of
  loose blocks.
- **A browsable set of peer items the reader chooses among** (a catalog, options, search results)
  belongs in a `carousel` of cards — horizontal browsing instead of an ever-growing vertical
  stack.
- **A status update or an approval** (one subject plus a decision) is well served by a `header`
  for the title, a `section` with `fields` for the key/value details, and an `actions` block for
  the buttons.
- **A one-line notice with no structure** should stay plain text. Don't add blocks for their own
  sake; wrapping a one-line status in a `card` or a table works against the content, not for it.

## Emphasis and actions

- **At most one emphasized button per `actions` block.** Use `primary` for the single
  main/confirming action (Approve, Submit, Save) and `danger` for a destructive one (Delete,
  Remove, Reject); leave secondary or neutral actions (Cancel, links) unstyled. Never give two
  buttons `primary` in the same group — if everything is emphasized, nothing is.
- **Guard destructive actions with a confirmation dialog** (`confirm`) so an accidental click
  can't do irreversible harm.

## Layout and reading order

- **Order blocks top-to-bottom in reading order:** lead with a `header` for the title, then the
  content `section`s, then any `actions`, then a trailing `context` block for footnotes. Don't
  bury the title in the middle of the layout.
- **Put secondary or metadata text in a `context` block, not a `section`** — attribution,
  timestamps, status, help links. Separate multiple fragments with " · " (for example,
  "Posted by <@U123> · 2 min ago").

## Text: mrkdwn vs. the markdown block

- **Short, interactive layouts** use Slack `mrkdwn` inside `section` and `context` blocks:
  `*bold*`, `_italic_`, `~strike~`, `` `code` `` — note this is Slack's syntax, not `**bold**`.
- **Long-form or AI/LLM-generated content that already exists in standard markdown** (headings,
  tables, numbered lists, `**bold**`) belongs in a `markdown` block (messages only), which renders
  standard markdown. Reach for it when the developer has such content or needs those features in
  the message body.

## Accessibility and fallback

Accessibility is easy to skip and hard to retrofit, so build it in from the start:

- **Give images descriptive `alt_text`** (what the image shows, not just "image"), and make sure
  image-heavy layouts also carry the key information as text.
- **Summarize the layout in a message's top-level `text` fallback.** Notifications and screen
  readers display it instead of the blocks, so an empty fallback leaves those readers with
  nothing.
- **Use `header` blocks for logical section headings** — they convey document structure to
  assistive tech.
