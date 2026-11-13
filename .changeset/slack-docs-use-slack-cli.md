---
"slack": minor
---

The `slack-docs` skill now searches and reads docs.slack.dev with the Slack CLI when it is installed, using `slack docs search --hide-pinned` and `slack docs get`. Agents without the CLI, or with an older one, keep using the search API and fetching the page's markdown.
