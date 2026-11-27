---
"slack": minor
---

Add OpenCode plugin support. The plugin installs into [OpenCode](https://opencode.ai) with `opencode plugin -g "slack@git+https://github.com/slackapi/slack-skills-plugin.git"` and registers the Slack skills on OpenCode 1 and OpenCode 2. OpenCode support ships the skills only: the commands and the Slack MCP server don't load there yet. Thanks to @youenchene, whose work in #125 mapped out both OpenCode plugin APIs.
