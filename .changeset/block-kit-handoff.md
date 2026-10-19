---
"slack": patch
---

Fix `create-slack-app` never handing off to the `block-kit` skill, so an agent building a message, modal, or App Home layout now uses it instead of writing Block Kit JSON from memory. `create-slack-app` and `block-kit` also check their optional argument against the allowed values before using it, and ask the developer when it doesn't match.
