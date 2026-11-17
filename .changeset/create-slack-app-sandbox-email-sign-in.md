---
"slack": patch
---

`create-slack-app` no longer asks for a sandbox password in chat. New developer sandboxes use email sign-in, the Slack CLI default since v4.11.0, so no password ends up in the agent's transcript or shell history.
