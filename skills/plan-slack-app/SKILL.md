---
name: plan-slack-app
description: 'Use when a developer wants to plan, design, or write a spec for a Slack app or agent before any code exists, or describes an idea, a problem to solve, or what an app in Slack should do for their team: "plan a Slack app for...", "an idea for a Slack agent that...", "what should a Slack bot for this do?", "write a spec for a Slack agent". Produces a product spec covering the agent view, App Home, streaming, and Block Kit. Scaffolding is `create-slack-app`.'
---

# Plan Slack App

Help a developer turn an idea into a plan for a Slack app or agent before anything is scaffolded. Most developers know their problem, or roughly what the app should do, but not which Slack features exist. So don't ask them to choose features. Start from a full, current Slack app shell, fold their idea into it, then ask a few plain questions to make it their own.

The output is a product spec: one markdown file a coding agent can build from. The `slack:create-slack-app` skill then scaffolds the project, and the spec travels with it into the build.

Nothing gets scaffolded until the developer approves the spec. That includes running `slack create`, installing dependencies, and invoking `slack:create-slack-app`. Reading and exploring are fine.

---

## Asking Questions

Ask every question with AskUserQuestion, one question per call, including approvals. A developer who skims can miss a question at the end of a long message, and the prompt makes the next step obvious.

- Offer 2-3 short options drawn from what the developer has already said, with the one you'd pick first and marked "(Recommended)". The tool's own free-text choice lets them answer in their own words, so don't add an "Other" option.
- **Put what they're approving inside the question.** The approval in **Step 5: Write the Spec** carries the spec summary in the option's `preview`, so the developer sees it next to the choice. Text written before a question can end up somewhere the developer doesn't see it, like the agent's own reasoning. Otherwise, keep the text before a question to a line or two.
- If the coding agent has no question tool, end the message with the question on its own line, in bold.

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

Ask one open question about the problem, not the app. For example: "What problem should this app solve, and who runs into it?" Offer one or two guesses from the developer's request as options, plus one option to skip the questions and use sensible defaults.

If they opt out of the questions, choose the shell defaults from Step 3, write the spec from those defaults, and go to Step 5 for approval. Opting out skips the questions, not the approval.

Match the developer's words, and don't use Slack feature names they haven't used themselves. If they say "just guess" or "what do you think?", propose something concrete.

---

## Step 3: Fold the Idea into a Slack App Shell

Read `references/slack-app-features.md`. It lists the current Slack features an app or agent can use, what each one gives the people using it, and which are on by default.

1. **Decide whether this is an agent.** If people will talk to it, ask it things, or hand it work, it's an agent: use the agent defaults. If it reacts to events, collects input through forms, or posts updates, it's an app: use the app defaults.
2. **Start from every default for that shape.** A developer gets the most out of Slack when the app uses the platform's current features, and they can't ask for features they don't know about.
3. **Add any optional feature the idea clearly calls for**, like a slash command for a quick action, a modal for a form, or Workflow Builder steps for a process people already automate.
Don't show the shell as a separate outline for approval. It shapes the options you offer in Step 4, and the developer reviews all of it once, in the spec summary.

---

## Step 4: Make It Theirs

Ask whichever of these are still open, one at a time:

- **The moment it helps.** "Walk me through the last time this came up. What would the app have done?" This gives you the key scenarios.
- **What it connects to.** "Which tools or data does it need to reach?" These become the agent's tools or the app's integrations.
- **Name and voice.** "What should it be called, and how should it sound?" Offer a guess they can correct. Slack's guidance is that an agent's name says what it does ("Deal Desk", "Support Scout") rather than sounding like a person, so suggest a name like that even when the voice has personality.

Ask which language they want (JavaScript or Python) only if they haven't said, and only if they care. Otherwise leave the question to `slack:create-slack-app`. Don't ask about scopes, events, Socket Mode, or manifest settings: derive those from the features in the spec.

Ask one question per topic. When the developer names a source or a tool, like a runbook or a set of repos, don't follow up on its format, hosting, or access. Those are build details, so list them under Open Questions in the spec and move on.

---

## Step 5: Write the Spec

Write the spec to `<app-name>-spec.md` in the current directory, following `references/spec-template.md`. Fill every section from the conversation. Where you made the call, say so in the spec. Keep the developer's own words for the problem, the scenarios, and the voice.

- **Don't name AI models.** The template sets the default model, and model names go stale.
- **Don't invent Slack API methods or scopes.** For anything the features reference doesn't already name, check with the `slack:slack-api` or `slack:slack-docs` skill.

Then ask for approval with AskUserQuestion. Put the spec's path in the question, like "Approve the spec in `status-check-spec.md`?", and give three options:

- **Approve and set up the app** (recommended), described as: "Next, a few setup questions, like language and workspace, before anything is created." Put the spec summary in this option's `preview`.
- **Change something.**
- **Approve, set up later.**

The summary is a short outline the developer can review at a glance, written around the problem rather than the feature list, under 15 lines:

```markdown
## SDK Triage: suggested answers for new GitHub issues

**Who:** the SDK team, in #triage-sdk

**How people reach it**
- Every new issue or PR posted to the channel
- Replies in the thread to dig deeper

**What it does**
- Adds :eyes: so the team knows it's looking
- Replies in the thread with an answer ready to paste into GitHub

_My calls: thumbs up and down on each answer, an AI disclaimer footer._
```

Describe what people see, like "buttons for the common requests on the app's Home tab", not "App Home with `views.publish`". Put every default you chose in the italic "My calls" line, so the developer can reject it. If the question tool has no preview, write the summary as text in the reply, then ask.

Revise until they approve.

---

## Step 6: Hand Off to create-slack-app

Once the developer approves the spec:

1. **Pick the template the spec points to.** An agent starts from the Starter Agent template, or the Support Agent template when the idea is a helpdesk or support agent. An app that isn't an agent starts from the Starter Template.
2. **Use the `slack:create-slack-app` skill** to scaffold the project. Pass `bolt-js` or `bolt-python` as its only argument when the developer has chosen a language, and pass no argument otherwise, so it asks. It walks through the CLI, login, and choosing a workspace. When it asks which template or AI provider to use, recommend the one the spec names, and suggest a project folder named after the app.
3. **Move the spec into the new project folder**, so it travels with the code.
4. **Ask before building.** Approving the spec covers scaffolding only. Ask whether to start building from the spec, with options to start with the first scenario or stop here. If they start, work through the spec one scenario at a time. For any message, modal, or Home tab layout, use the `slack:block-kit` skill. To confirm the app works, use the `slack:test-slack-app` skill.

---

## Notes

- Don't put emoji in headings, in the summary or the spec. Terminals draw emoji at different widths, which can misalign the text that follows, and plain headings scan faster.
- This skill plans. Building starts only when the developer says so in Step 6, and Block Kit JSON, scaffolding, and running the app belong to the skills named there.
- Don't ask for API keys or other credentials while planning. The `slack:create-slack-app` skill collects them when the project needs them.
- A spec is a plan, not a contract. If the developer changes their mind while building, update the spec to match.
