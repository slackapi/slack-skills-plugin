---
"slack": patch
---

The `deploy-slack-app` skill now spots a Deno Slack SDK app and deploys it to Slack with plain `slack deploy`, then creates its triggers for the deployed app. It used to read the app's manifest as a Request URL app and stop, or steer it to a Railway or Heroku deploy hook.
