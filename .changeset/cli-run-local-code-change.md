---
"slack": patch
---

Starting an existing app on the developer's machine to try a code change now loads the `slack-cli` skill for `slack run`, instead of `test-slack-app`. Claude picked `test-slack-app` for about half of these requests, because its description also mentions trying an app out with `slack run`.
