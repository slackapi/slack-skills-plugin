---
"slack": patch
---

Skills that hand off to the `slack-cli` skill for CLI detection now ask the agent to load that skill before running any command. Agents like OpenCode used to check `PATH` for `slack` themselves, which can find a different tool with the same name, and then fall back to curl.
