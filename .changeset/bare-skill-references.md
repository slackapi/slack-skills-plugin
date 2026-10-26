---
"slack": patch
---

Fix skill cross-references for agents that install the skills with `npx skills`. Skills now point at each other by bare name (the `slack-cli` skill) instead of `slack:slack-cli`, which only Claude Code registers, so agents like Cursor and Codex can follow a hand-off from one skill to the next.
