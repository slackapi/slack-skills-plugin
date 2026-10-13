---
"slack": minor
---

Add OpenCode support through a native git-backed plugin. One package serves
OpenCode 2 (skill, command, and MCP transforms) and OpenCode 1 (`config` hook),
registering the eight canonical skills, five `slack-*` commands, and an
OAuth-enabled Slack MCP server while preserving an existing `slack` server.
