---
"slack": patch
---

Have the `slack-docs` skill pass `pin=false` to the docs search API, so searches about Claude, Cursor, Codex, MCP, or coding agents return docs pages instead of putting this plugin's own page first. The API ignores the parameter until docs.slack.dev supports it, so the change is safe to release before then.
