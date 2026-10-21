---
name: plan-slack-app
description: 'Use when a developer wants to plan, design, or write a spec for a Slack app or agent before any code exists, or describes an idea, a problem to solve, or what an app in Slack should do for their team: "plan a Slack app for...", "an idea for a Slack agent that...", "what should a Slack bot for this do?", "write a spec for a Slack agent". Produces a product spec covering the agent view, App Home, streaming, and Block Kit. Scaffolding is `create-slack-app`.'
---

# Plan Slack App

Help a developer turn an idea into a plan for a Slack app or agent before anything is scaffolded. Most developers know their problem, or roughly what the app should do, but not which Slack features exist. So don't ask them to choose features. Start from a full, current Slack app shell, fold their idea into it, then ask a few plain questions to make it their own.

The output is a product spec: one markdown file a coding agent can build from. The `slack:create-slack-app` skill then scaffolds the project, and the spec travels with it into the build.

Nothing gets scaffolded until the developer approves the spec. That includes running `slack create`, installing dependencies, and invoking `slack:create-slack-app`. Reading and exploring are fine.

---

## Working with Superpowers Brainstorming

The `superpowers:brainstorming` skill is a popular, general-purpose skill for planning anything before it gets built. This skill works with it and never competes with it, replaces it, or requires it.

- **If `superpowers:brainstorming` is already running the conversation**, do not start a second one. Bring this skill's Slack knowledge into that conversation instead: use the shell in **Step 3: Fold the Idea into a Slack App Shell** as the defaults it proposes, and make sure its written design covers the sections in `references/spec-template.md`. Its design document is the spec. When it hands off to a plan, the plan's first task is scaffolding with `slack:create-slack-app`, as in **Step 6: Hand Off to create-slack-app**.
- **If it is not installed, or not in use**, run the short conversation below. Do not suggest installing it.

---

## Step 1: Check That This Is a New App

- **The developer already knows exactly what to scaffold** (for example, "create the Python starter template"): there is nothing to plan. Use the `slack:create-slack-app` skill directly.
- **The current directory is already a Slack app** (it has a `.slack/` directory, or a `manifest.json` next to a Bolt dependency): planning changes to an existing app is not supported yet. Say so plainly. Support may have shipped in a newer version of the Slack Skills Plugin, so ask the developer to update the plugin and try again. If they are already on the latest version, help with their request directly instead.
- **Otherwise**, continue.

---

## Step 2: Hear the Problem

Your first message is two things:

1. One line saying that if they'd rather skip the questions, you can pick sensible defaults and start building.
2. One open question about the problem, not the app. For example: "What's the problem you want this app to solve, and who runs into it?"

If they opt out of the questions, choose the shell defaults from Step 3, say the main choices in one line (agent or not, language, how people reach it), write the spec from those defaults, and go to Step 6.

Ask one question per message. Match the developer's words, and don't use Slack feature names they haven't used themselves. If they say "just guess" or "what do you think?", propose something concrete.

---

## Step 3: Fold the Idea into a Slack App Shell

Read `references/slack-app-features.md`. It lists the current Slack features an app or agent can use, what each one gives the people using it, and which are on by default.

1. **Decide whether this is an agent.** If people will talk to it, ask it things, or hand it work, it's an agent: use the agent defaults. If it reacts to events, collects input through forms, or posts updates, it's an app: use the app defaults.
2. **Start from every default for that shape.** A developer gets the most out of Slack when the app uses the platform's current features, and they can't ask for features they don't know about.
3. **Add any optional feature the idea clearly calls for**, like a slash command for a quick action, a modal for a form, or Workflow Builder steps for a process people already automate.
4. **Play it back in about 150-250 words**, written around the problem rather than the feature list. Say how people reach the app, what it does when they do, and what it looks like. For example: "Your team opens the app's Home tab and sees buttons for the common requests" rather than "App Home with `views.publish`". Mark each default as your call, so the developer can reject it. End by asking what's wrong or missing.

---

## Step 4: Make It Theirs

Ask 2-4 questions, one per message, picking whichever ones are still open:

- **The moment it helps.** "Walk me through the last time this came up. What would the app have done?" This gives you the key scenarios.
- **What it connects to.** "Which tools or data does it need to reach?" These become the agent's tools or the app's integrations.
- **Name and voice.** "What should it be called, and how should it sound?" Offer a guess they can correct. Slack's guidance is that an agent's name says what it does ("Deal Desk", "Support Scout") rather than sounding like a person, so suggest a name like that even when the voice has personality.
- **What to cut.** "Is there anything in what I described that you don't want?"

Ask which language they want (JavaScript or Python) only if they haven't said, and only if they care. Otherwise leave the question to `slack:create-slack-app`. Don't ask about scopes, events, Socket Mode, or manifest settings: derive those from the features in the spec.

Play back each part as you understand it, then move to the next question.

---

## Step 5: Write the Spec

Write the spec to `<app-name>-spec.md` in the current directory, following `references/spec-template.md`. Fill every section from the conversation. Where you made the call, say so in the spec. Keep the developer's own words for the problem, the scenarios, and the voice.

- **Don't name AI models.** The template sets the default model, and model names go stale.
- **Don't invent Slack API methods or scopes.** For anything the features reference doesn't already name, check with the `slack:slack-api` or `slack:slack-docs` skill.

Show the developer a short summary of the spec and its path, then ask them to approve it or say what to change. Revise until they approve.

---

## Step 6: Hand Off to create-slack-app

Once the developer approves the spec:

1. **Pick the template the spec points to.** An agent starts from the Starter Agent template, or the Support Agent template when the idea is a helpdesk or support agent. An app that isn't an agent starts from the Starter Template.
2. **Use the `slack:create-slack-app` skill** to scaffold the project, passing `bolt-js` or `bolt-python` if the language is settled. It walks through the CLI, login, and choosing a workspace. When it asks which template or AI provider to use, recommend the one the spec names.
3. **Move the spec into the new project folder**, so it travels with the code.
4. **Build from the spec.** Work through it one scenario at a time. For any message, modal, or Home tab layout, use the `slack:block-kit` skill. To confirm the app works, use the `slack:test-slack-app` skill.

---

## Notes

- This skill plans. It does not write app code, and it does not own Block Kit JSON, scaffolding, or running the app.
- Don't ask for API keys or other credentials while planning. The `slack:create-slack-app` skill collects them when the project needs them.
- A spec is a plan, not a contract. If the developer changes their mind while building, update the spec to match.
