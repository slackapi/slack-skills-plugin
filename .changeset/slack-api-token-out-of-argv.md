---
"slack": patch
---

The `slack-api` skill no longer has the agent handle a Slack token when it calls methods without the Slack CLI. The developer provides the token as `SLACK_BOT_TOKEN` or `SLACK_USER_TOKEN`, and the curl examples pipe the `Authorization` header in on stdin, so the token stays out of the conversation, the command line, and shell history.
