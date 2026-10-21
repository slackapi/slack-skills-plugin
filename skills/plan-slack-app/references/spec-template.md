# Spec Template

The shape of the spec written in **Step 5: Write the Spec**. Replace each `<placeholder>` with what the conversation settled, and drop a section only when it truly doesn't apply (for example, Voice for an app that only posts reports). Mark anything you decided rather than the developer with "(my call)".

````markdown
# <App Name>: <one-line description>

## Overview

- **Problem:** <the problem, in the developer's words>
- **Who it's for:** <the people who use it, and where in Slack they are>
- **What success looks like:** <how the developer will know it's working>
- **Shape:** <agent or app>

## Voice

<Two or three sentences on how it sounds, with one or two example lines it would say. Skip for an app that doesn't converse.>

## How People Reach It

<One bullet per entry point from the shell: agent view, DMs, channel mentions, App Home, slash commands, shortcuts. For each, what the person does and what happens next.>

## How It Responds

<Thread replies, reactions, status, streaming, progress, feedback, approvals, Block Kit messages, modals: whichever the shell includes, and how each one behaves for this app.>

## What It Can Do

<One bullet per capability or tool, like "Create a ticket in Jira with the conversation as context". Mark simulated or stubbed tools as such.>

## Key Scenarios

<Two or three scenarios from the conversation. For each, a short example exchange:>

```text
User (in #help-it): @<App Name> <message>
  :eyes:
<App Name> (in thread): <reply>
```

## When Things Go Wrong

<What it says when a tool fails, when it lacks access to something, and when it can't do what was asked. Keep finished work, name the limit plainly, and offer 2-3 next steps.>

## Agent Instructions

<For an agent, the system prompt: role, voice, what it can do, how it works through a request, when it asks before acting, how it cites sources, and when it hands off to a person. Skip for an app that isn't an agent.>

## Slack Setup

- **Language:** <JavaScript or Python, or "ask when scaffolding">
- **Template:** <Starter Agent, Support Agent, or Starter Template>
- **AI provider:** <the provider, or "template default">
- **Features:** <the features from the shell this app uses>
- **Scopes and events:** <derived from the features, as a starting list>

## Not Now

<What the developer cut, and ideas for later.>
````
