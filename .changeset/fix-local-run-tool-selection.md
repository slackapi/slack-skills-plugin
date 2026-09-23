---
"slack": patch
---

Ensure "run my Slack app locally" prompts route to the `slack-cli` skill rather than `create-slack-app`. The `create-slack-app` description previously advertised "creating + running a project from a Bolt template locally", overlapping with `slack-cli`'s territory; dropping "+ running" disambiguates the two.
