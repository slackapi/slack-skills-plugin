---
"slack": patch
---

Claude Code installs now start from the plugin's own marketplace, `slack@slack`, which gets each release as soon as it ships. The README, the docs.slack.dev page, and the agent setup prompt all lead with it. If you installed `slack@claude-plugins-official`, switch with `claude plugin uninstall slack@claude-plugins-official`, then `claude plugin marketplace add slackapi/slack-skills-plugin` and `claude plugin install slack@slack`. Run `claude plugin list` to confirm that `slack@slack` is the only Slack plugin installed.
