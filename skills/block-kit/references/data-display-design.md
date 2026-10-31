# Data Display Design: Fields, Tables, and Charts

Guidance on presenting numbers and records so a reader understands them quickly. Like
`design-principles.md`, this covers _appropriateness_, not validity. For field schemas, see the
`section`, `table`, `data_table`, and `data_visualization` block pages. Apply these principles
unless the developer explicitly asks otherwise.

## Pick the format that fits the data

| The data is… | Use | Surfaces |
|---|---|---|
| one number that matters | a sentence that states it ("Error rate is 2.1%, up from 0.4%") | all |
| progress toward a goal, or fewer than 4 data points | a sentence ("412 of 500 seats filled (82%)") or `section` `fields` | all |
| a few key/value facts about one thing | a `section` with `fields` (up to 10) | all |
| a short set of rows with the same columns | a `table` (up to 100 rows) | messages, App Home |
| many rows, or rows the reader sorts, pages through, or acts on | a `data_table` (up to 200 rows, paginated, sortable, `action_cell` buttons) | messages, App Home |
| a trend over time | a `data_visualization` `line` (or `area` for totals that stack) | messages, App Home |
| a comparison across categories | a `data_visualization` `bar` | messages, App Home |
| shares of a whole | a `data_visualization` `pie`, with no more than about 5 slices | messages, App Home |

- **Start from the question the reader has.** "Did the deploy work?" needs a sentence, not a
  chart. "Which service is slowest this week?" needs a sorted table or a bar chart.
- **Don't show the same data twice** in a table and a chart unless they answer different
  questions. Pick one, and link to the full data for anything more.
- **In a modal**, where `table`, `data_table`, and charts aren't available, use `section` `fields`
  for key/value data and summarize rows into a few lines. Link out for the full set.

## Fields

- **Keep labels short and bold, and values short**: `*Status*\nIn review`. Fields lay out in two
  columns, so long values wrap and break the grid.
- **Put the most important pair first.** Readers scan fields top-left to bottom-right.
- **Use an even number of fields** where you can, so the last row isn't half empty.

## Tables

- **Lead with the column that identifies the row** (name, ID, title), and set a `data_table`'s
  `row_header_column_index` to it so screen readers announce each row by name.
- **Give every `data_table` a `caption`** (required) that says what the table shows: "Open
  incidents, sorted by severity".
- **Keep it narrow.** About five columns fit comfortably, especially on mobile. Drop columns the
  reader doesn't need to decide anything.
- **Sort rows by what matters**: the worst first, the newest first, the biggest first. Say how it's
  sorted in the caption or the lead sentence.
- **Use `raw_number` cells for numbers** so a `data_table` sorts them numerically. Put units in
  the header ("Latency (ms)") rather than in every cell.
- **Choose a page size for a `data_table`** that fits the message: the default of 5 rows suits a
  digest, and 10–20 suits a report the reader came to look at.
- **Use an `action_cell` for one action per row** ("Open", "Mark Done"), with the row's ID in the
  button's `value` and a `fallback` cell for clients that can't show buttons. Buttons in a copy of
  the message shared elsewhere are disabled, so don't rely on them as the only way to act.
- **Only one `table` fits in a message, and cell text is capped across the message** (10,000
  characters for `table`, 20,000 for `data_table`). For more, summarize and link out.

## Charts

- **Write a title that says what the chart shows.** Keep it to 50 characters or fewer: "Deploys
  per day, last 2 weeks".
- **State the takeaway in text.** Put the main point, with its number, in the chart's description
  and in the message text: "Deploys doubled after the pipeline change." Notifications, previews,
  and screen readers get only the text, and on mobile the reader can't open the expanded view.
- **Name the items that matter.** A chart can't highlight a bar or point, and it drops value labels
  when space is tight. Write "3 accounts need attention: Harmony Labs, Acme, Northwind" rather than
  leaving the reader to find them.
- **Label both axes, including units.** Use `x_label` and `y_label`: "Latency (ms)".
- **Use one series for one comparison.** A bar chart of 8 services is one series in one color.
  Giving each bar its own series adds colors that suggest a difference that isn't there.
- **Keep series to a few.** One to three lines or bar groups are easy to read. Past 6, colors
  repeat in a second shade that's hard to tell apart, especially with color vision deficiency.
  Series names appear in the legend, so keep them short and distinct.
- **Use color only to tell series apart.** Slack assigns colors automatically, in series order, and
  they change in dark mode. Avoid ordering series so a color seems to mean good or bad, and avoid
  referring to "the orange line". Say what's good or bad in text, and refer to each series by name.
- **Choose the chart type that fits the data.**
  - **Bar** compares values across categories. Keep to about 6 categories with one-word labels
    ("Q1", "Legal", "API"), because the card is often narrow. For more categories or longer
    labels, use a sorted table.
  - **Line** shows a trend over time. Keep to 3 lines with at least 4 points each.
  - **Area** shows a total over time and what it's made of. Areas always stack, so use one only
    when the series add up to a meaningful total; otherwise, use a line chart. Keep to 3 series.
  - **Pie** shows parts of one whole. Keep to 5 segments, largest first, and group the rest into
    "Other". For more, use a sorted bar chart.
- **Order categories meaningfully.** Put time left to right. For bars, put the largest first unless
  the categories have a natural order. Slack keeps the order you provide.
- **Fit the data to the block.** A series holds at most 20 points, so aggregate a long range
  (weekly instead of daily) rather than trimming it. Every series needs a value for every
  category, so don't fill a gap with zero. Drop that category from every series and say what's
  missing in text.
- **Skip the chart when there's no data.** Say so in a sentence instead: "No deploys this week."
- **Include no more than two charts in a message.** For a dashboard, use the App Home or link to
  your product.

## Numbers and dates in text

- **Round to what matters**: "2.1%", not "2.0847%". Abbreviate only from 10,000 up, with a capital
  K or M ("21K messages"); below that, write the full number ("1,187").
- **Show change with direction and a baseline**: "up 3 points from last week", not a bare arrow
  or a color.
- **Use a `date` element in `rich_text`, or mrkdwn's `<!date^…>` syntax, for timestamps**, so each
  reader sees them in their own timezone and format, with relative wording ("today", "3 hours
  ago") where it helps. Always include fallback text.
- **Write dates without ordinals**: "Aug 2, 2026", not "Aug 2nd".

## Quick self-review

1. Does the format answer the reader's question, and is it supported on this surface?
2. Is the key number or takeaway stated in text, not only in the table or chart?
3. Does every table have the identifying column first, a clear sort, and units in the header?
4. Does every chart have a title, axis labels, and few enough series and categories to read,
   with color used only to tell series apart?
5. Are timestamps localized, and are numbers rounded to what matters?
