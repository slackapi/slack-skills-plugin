---
"slack": patch
---

When the Slack CLI isn't installed, the `slack-cli` skill now asks whether to install it for you or show you the install command, in the same question that asks about an alias. Before, answering "No, I need to install it" to a question about aliases ran the install script from `downloads.slack-edge.com` without asking.
