---
"slack": patch
---

Fix `create-slack-app` offering Pydantic AI for a JavaScript agent app. Agents could ask for the language and the AI provider in one question, so the provider list included Pydantic AI before the developer had picked JavaScript, and `bolt-js-starter-agent` has no Pydantic AI option. The skill now asks for the language first and offers only that language's providers.
