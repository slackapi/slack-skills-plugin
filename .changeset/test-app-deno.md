---
"slack": minor
---

The `test-slack-app` skill now covers Deno Slack SDK apps. It runs the project's `deno task test`, creates the app's triggers for the local app, and gives a step for each link, event, scheduled, and webhook trigger and the functions its workflows run. It used to list Bolt listeners only.
