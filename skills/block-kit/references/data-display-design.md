# Data Display Design: Fields, Tables, and Charts

Guidance on presenting numbers and records so people understand them quickly. It builds on
`design-principles.md`. For field schemas, see the `section`, `table`, `data_table`, and
`data_visualization` block pages. Apply these principles unless the developer explicitly asks
otherwise.

## Pick the format that fits the data

| The data is… | Use | Surfaces |
|---|---|---|
| one number that matters | a sentence that states it ("Error rate is 2.1%, up from 0.4%") | all |
| progress toward a goal, or fewer than 4 data points | a sentence ("412 of 500 seats filled (82%)") or `section` `fields` | all |
| a few key/value facts about one thing | a `section` with `fields` (up to 10) | all |
| a short set of rows with the same columns | a `table` (up to 100 rows) | messages, App Home |
| many rows, or rows people sort, page through, or act on | a `data_table` (up to 200 rows, paginated, sortable, `action_cell` buttons) | messages, App Home |
| a trend over time | a `data_visualization` `line` (or `area` for totals that stack) | messages, App Home |
| a comparison across categories | a `data_visualization` `bar` | messages, App Home |
| shares of a whole | a `data_visualization` `pie`, with no more than about 5 slices | messages, App Home |

- **Start from the question people have.** "Did the deploy work?" needs a sentence, not a
  chart. "Which service is slowest this week?" needs a sorted table or a bar chart.
- **Show the same data once**, in a table or a chart, unless the two answer different
  questions. Pick one, and link to the full data for anything more.
- **Use `section` `fields` in a modal**, where `table`, `data_table`, and charts aren't
  available, and summarize rows into a few lines. Link out for the full set.

## Fields

- **Keep labels short and bold, and values short**: `*Status*\nIn review`. Fields lay out in two
  columns, so long values wrap and break the grid.
- **Put the most important pair first.** People scan fields top-left to bottom-right.
- **Use an even number of fields** where you can, so the last row isn't half empty.

## Tables

- **Lead with the column that identifies the row** (name, ID, title), and set a `data_table`'s
  `row_header_column_index` to it so screen readers announce each row by name.
- **Give every `data_table` a `caption`** (required) that says what the table shows: "Open
  incidents, sorted by severity".
- **Keep it narrow.** About five columns fit comfortably, especially on mobile. Drop columns
  people don't need to decide anything.
- **Sort rows by what matters**: the worst first, the newest first, the biggest first. Say how it's
  sorted in the caption or the lead sentence.
- **Put units in the header** ("Latency (ms)") rather than in every cell.
- **Choose a page size that fits the message.** Five rows suits a digest, and 10–20 suits a report
  people came to look at.
- **Offer at most one action per row** ("Open", "Mark Done"). Buttons in a copy of the message
  shared elsewhere are disabled, so don't rely on them as the only way to act.
- **Summarize and link out when the rows don't fit.** A message holds one `table`, and cell text
  is capped across the message (see `design-principles.md` for the limits).

## Charts

- **Write a title that says what the chart shows.** Keep it to 50 characters or fewer: "Deploys
  per day, last 2 weeks".
- **State the takeaway in text.** Put the main point, with its number, in the chart's description
  and in the message text: "Deploys doubled after the pipeline change." Notifications, previews,
  and screen readers get only the text, and on mobile people can't open the expanded view.
- **Name the items that matter.** A chart can't highlight a bar or point, and it drops value labels
  when space is tight. Write "3 accounts need attention: Harmony Labs, Acme, Northwind" rather than
  leaving people to find them.
- **Label both axes, including units**: "Latency (ms)".
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
- **Aggregate a long range rather than trimming it** (weekly instead of daily) when it has more
  points than a series holds.
- **Leave out missing data rather than filling it with zero.** Drop that category from every
  series and say what's missing in text.
- **Skip the chart when there's no data.** Say so in a sentence instead: "No deploys this week."
- **Include no more than two charts in a message.** For a dashboard, use the App Home or link to
  your product.

## Numbers and dates in text

- **Round to what matters**: "2.1%", not "2.0847%". Abbreviate only from 10,000 up, with a capital
  K or M ("21K messages"); below that, write the full number ("1,187").
- **Show change with direction and a baseline**: "up 3 points from last week", not a bare arrow
  or a color.
- **Localize timestamps**, so each person sees them in their own timezone and format, with
  relative wording ("today", "3 hours ago") where it helps.
- **Write dates without ordinals**: "Aug 2, 2026", not "Aug 2nd".

## Implementation notes

- **Use `raw_number` cells for numbers** so a `data_table` sorts them numerically.
- **Set a `data_table`'s page size** to fit the message; the default is 5 rows.
- **Build row actions with an `action_cell`**, with the row's ID in the button's `value` and a
  `fallback` cell for clients that can't show buttons.
- **Set chart axis labels with `x_label` and `y_label`.**
- **Give every series a value for every category.** A series holds at most 20 points.
- **Write timestamps with a `date` element in `rich_text`, or mrkdwn's `<!date^…>` syntax**, and
  always include fallback text.

## Quick self-review

1. Does the format answer people's question, and is it supported on this surface?
2. Is the key number or takeaway stated in text, not only in the table or chart?
3. Does every table have the identifying column first, a clear sort, and units in the header?
4. Does every chart have a title, axis labels, and few enough series and categories to read,
   with color used only to tell series apart?
5. Are timestamps localized, and are numbers rounded to what matters?
