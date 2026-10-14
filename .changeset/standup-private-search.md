---
"slack": patch
---

Include DMs and private channels when `/slack:standup` gathers recent activity. The command now uses the consent-gated `slack_search_public_and_private` search, so updates that never appear in public channels are part of the standup.
