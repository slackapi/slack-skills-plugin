---
"slack": patch
---

The `slack-cli` and `deploy-slack-app` skills now ask the developer which workspaces to grant when an app is first installed to an Enterprise organization, instead of always granting all of them. The agent shows the same choices the CLI prompt offers, all workspaces first and then each workspace by name, and passes the answer to `--org-workspace-grant`.
