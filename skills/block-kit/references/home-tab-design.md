# App Home Design

Guidance on Home tabs that people return to. Like `design-principles.md`, this covers
_appropriateness_, not validity. For the view object and publishing, see
`https://docs.slack.dev/surfaces/app-home.md`. Apply these principles unless the developer
explicitly asks otherwise.

A Home tab is one view of up to 100 blocks, published per user with `views.publish`. Unlike a
message, it's persistent and personal: each user sees their own version, and it should be up to
date whenever they open it.

## Put the most important thing at the top

- **Lead with what this user needs now**: items waiting on them, today's status, or the one
  action they come here for. Slack's guidance is that the most important content and the entry
  points to your app's core features belong at the top.
- **Then the rest, in sections**, each with a `header`: recent activity, settings, help.
  Separate genuinely different sections with a `divider`, not every block.
- **Don't open with a welcome banner** after the first visit. Returning users came for the
  content, not the introduction.

## Keep actions few

- **Limit the visible calls to action.** Put the main one or two actions in an `actions` block
  near the top, give each row its own button for its action ("Open", "Read"), and move rare
  actions into an `overflow` menu.
- **Put settings behind a button** that opens a modal (see `modal-design.md`), rather than laying
  out every setting on the Home tab. Show admin-only settings only to admins.
- **Open details in a modal** rather than expanding the Home tab. A "Read" or "Open" button that
  opens a modal keeps the Home tab short.

## Empty and first-run states

- **Teach by example in empty states.** Instead of "No routines", say what it would look like and
  how to start: `_None yet. Ask me for one: "every weekday at 8am, tell me what needs me today."_`
- **Onboard on the first visit.** Use the `app_home_opened` event to detect a new user and show a
  short setup: what the app does, the one thing to try first, a button to start, and a way to
  dismiss it. Replace it with the normal Home tab once they've done it.
- **Welcome back long-absent users** with what changed or what's waiting, not the full
  onboarding again.

## Keep it current

- **Publish on `app_home_opened`** so the view is fresh when the user looks, and publish again
  when the user's data changes (an item resolved, a setting saved).
- **Show freshness where it matters**: "Updated 2 min ago" in a `context` block at the top, using
  a `date` element or `<!date^…>` so it's localized.
- **Make status rows self-explanatory**: name, state, and the last outcome. For example,
  `*Daily digest* · paused` and `_Last run Tue 8:00 AM: nothing to report_`.
- **Don't show stale controls.** After an action completes, publish a view that reflects it,
  rather than leaving a button that does nothing.

## Different people, different Home tabs

The Home tab is published per user, so it can, and often should, differ by role.

- **Show each user only what they're allowed to see.** Decide on the server what each role
  (owner, admin, member, guest) gets, and build the view from that. Hiding a button isn't access
  control; the action handler must check permissions too.
- **Let owners and admins preview other roles' views**: a "View as Member" button that publishes
  the reduced view to them, with a `context` line saying they're previewing and a button back.

## A review surface for agents

When an app or agent acts on a user's behalf, the Home tab is where the user checks what it did.

- **List recent actions and conversations**, newest first, each with who, where, when, and a
  short excerpt, and a button to read the full record in a modal.
- **Show pending items** (approvals waiting, failed runs) above the history, with a direct action
  for each.
- **Give users a place to manage trust**: revoke an "Always Allow", reconnect an app, or pause a
  routine.

## Long content

- **Split long text across `section` blocks** under the 3,000-character limit per text field. In a
  modal, also stay under the 100-block view limit, and add a `context` line such as "File
  continues beyond what this view can show" with a link to the full content.
- **Link out rather than paging inside the Home tab.** A short, current summary plus a link beats
  a long view the user has to scroll through.

## Quick self-review

1. Is the most important content for this user at the top, with at most one or two main actions?
2. What does a brand-new user see, and what does the view show when a section is empty?
3. Is the view published on open and whenever the data changes, with no stale controls?
4. Does each role see only what it should, with permissions checked in the handlers?
5. If the app acts on users' behalf, can they review and manage what it did here?
