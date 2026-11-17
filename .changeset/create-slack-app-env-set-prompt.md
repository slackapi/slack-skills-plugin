---
"slack": patch
---

`create-slack-app` no longer asks for an AI provider API key in chat. The developer sets it with `slack env set <NAME>` in their own terminal, where the CLI hides what they type, so the key stays out of the agent's transcript and shell history.
