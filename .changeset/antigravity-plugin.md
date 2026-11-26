---
"slack": minor
---

Add Antigravity plugin support. A new `.antigravity-plugin/plugin.json` manifest exposes the Slack skills to the [Antigravity CLI](https://antigravity.google/docs/cli/using/) (`agy`), so the plugin installs with `agy plugin install https://github.com/slackapi/slack-skills-plugin`. Antigravity support ships the skills only: the commands and the Slack MCP server don't load there yet.
