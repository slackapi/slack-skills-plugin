---
name: slack-messaging
description: Guidance for composing well-formatted, effective Slack messages using standard markdown
---

# Slack Messaging Best Practices

This skill provides guidance for composing well-formatted, effective Slack messages.

## When to Use

Apply this skill whenever composing, drafting, or helping the user write a Slack message — including when using `slack_send_message`, `slack_send_message_draft`, or `slack_create_canvas`.

## Formatting

Slack MCP accepts standard markdown. Use familiar markdown syntax when composing messages:

| Format | Syntax |
|--------|--------|
| Bold | `**text**` |
| Italic | `_text_` or `*text*` |
| Strikethrough | `~text~` |
| Code (inline) | `` `code` `` |
| Code block | `` ```code``` `` |
| Quote | `> text` |
| Link | `[display text](url)` |
| Bulleted list | `- item` |
| Numbered list | `1. item` |

Not supported:

- Tables
- Headers `(#, ##, etc.)`
- Images via markdown `(![alt](url))`

## Message Structure Guidelines

- **Lead with the point.** Put the most important information in the first line. Many people read Slack on mobile or in notifications where only the first line shows.
- **Keep it short.** Aim for 1-3 short paragraphs. If the message is long, consider using a Canvas instead.
- **Use line breaks generously.** Walls of text are hard to read. Separate distinct thoughts with blank lines.
- **Use bullet points for lists.** Anything with 3+ items should be a list, not a run-on sentence.
- **Bold key information.** Use `*bold*` for names, dates, deadlines, and action items so they stand out when scanning.

## Thread vs. Channel Etiquette

- **Reply in threads** when responding to a specific message to keep the main channel clean.
- **Use `reply_broadcast`** (also post to channel) only when the reply contains information everyone needs to see.
- **Post in the channel** (not a thread) when starting a new topic, making an announcement, or asking a question to the whole group.
- **Don't start a new thread** to continue an existing conversation — find and reply to the original message.

## Tone and Audience

- Match the tone to the channel — `#general` is usually more formal than `#random`.
- Use emoji reactions instead of reply messages for simple acknowledgments (though note: the MCP tools can't add reactions, so suggest the user do this manually if appropriate).
- When writing announcements, use a clear structure: context, key info, call to action.
