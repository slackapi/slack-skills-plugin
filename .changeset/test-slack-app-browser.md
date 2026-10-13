---
"slack": minor
---

The test-slack-app skill can now perform its test steps itself: it drives the Slack web client in a browser window the developer watches, using Playwright CLI, in a developer sandbox or Free Team only. It checks each slash command, shortcut, modal, button, message, and App Home step against the `slack run` logs and reports the results with screenshots. Testing by hand stays the default.
