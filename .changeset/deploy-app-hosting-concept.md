---
"slack": patch
---

The `deploy-slack-app` description now leaves conceptual questions about how Slack app hosting works to the `slack-docs` skill. Claude used to load `deploy-slack-app` for "How does hosting for Slack apps work conceptually?" because the description mentions hosting. A request to deploy or host an app still loads `deploy-slack-app`.
