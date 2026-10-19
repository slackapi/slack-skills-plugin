---
"slack": patch
---

Clarify in the `block-kit` skill that `blocks.validate` checks block and element shape only. It does not enforce which surface a block is allowed on or how many of a block a message can hold, so the skill now checks those against the design principles' surface and limits table instead of treating a passing validation as proof.
