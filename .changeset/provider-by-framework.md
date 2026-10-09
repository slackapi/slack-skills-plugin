---
"slack": patch
---

Fix `create-slack-app` offering Pydantic AI when you create a JavaScript agent app. Pydantic AI only works with Python, so the skill now asks for your language first and only lists the AI providers that work with it.
