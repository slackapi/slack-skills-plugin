---
"slack": patch
---

Claude Code install instructions now list Slack's Claude marketplace first. Updates on the official Claude marketplace are experiencing large delays, so we recommend Slack's marketplace until that is resolved.

Install the plugin from Slack's marketplace inside Claude Code:

```text
/plugin marketplace add slackapi/slack-skills-plugin
/plugin install slack@slack
```

Then turn on auto-update:

1. Run `/plugin`.
2. Open **Marketplaces**.
3. Select `slack`.
4. Select **Enable auto-update**.

Without auto-update, update an existing install to the latest version with:

```sh
claude plugin marketplace update slack
claude plugin update slack@slack
```

If you installed the plugin from the official Claude marketplace, uninstall it first, so that only one copy is enabled:

```sh
claude plugin uninstall slack@claude-plugins-official
```

Then install from Slack's marketplace as shown above, and run `claude plugin list` to confirm that `slack@slack` is the only Slack plugin listed.
