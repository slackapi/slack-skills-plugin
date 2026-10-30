---
"slack": minor
---

Set up a project for an app already created in App Settings. The agent setup prompt now takes `--app`, `--template`, and `--team` arguments, which App Settings adds to the prompt it shows after a developer creates and installs an app. The prompt asks the developer's language and turns the App Settings template name into a template repo. `create-slack-app` then skips choosing a workspace, a language, and a template, and links the new project to the existing app with `slack create --app`.
