# App Home Design

Guidance on Home tabs that people return to. It builds on `design-principles.md`. For the view
object and publishing, see `https://docs.slack.dev/surfaces/app-home.md`. Apply these principles
unless the developer explicitly asks otherwise.

The Home tab is the App Home's persistent, personal view: each person sees their own version, and
it should be up to date whenever they open it.

## Put the most important thing at the top

- **Lead with what this person needs now**: items waiting on them, today's status, or the one
  action they come here for, along with entry points to your app's core features.
- **Follow with the rest in sections**, each with a `header`: recent activity, settings, help.
- **Skip the welcome banner after the first visit.** Returning people came for the content, not
  the introduction.

## Keep actions few

- **Limit the visible calls to action.** Put the main one or two actions in an `actions` block
  near the top, give each row its own button for its action ("Open", "Read"), and move rare
  actions into an `overflow` menu.
- **Put settings behind a button that opens a modal** (see `modal-design.md`), rather than laying
  out every setting on the Home tab. Show admin-only settings only to admins.
- **Open details in a modal** rather than expanding the Home tab. A "Read" or "Open" button that
  opens a modal keeps the Home tab short.

## Empty and first-run states

- **Teach by example in empty states.** Instead of "No routines", say what one would look like and
  how to start: `_None yet. Ask me for one: "every weekday at 8am, tell me what needs me today."_`
- **Onboard on the first visit** with a short setup: what the app does, the one thing to try
  first, a button to start, and a way to dismiss it. Replace it with the normal Home tab once
  they've done it.
- **Welcome back long-absent people** with what changed or what's waiting, not the full onboarding
  again.

## Keep it current

- **Refresh the view when someone opens it**, and again when their data changes (an item
  resolved, a setting saved).
- **Show freshness where it matters**: "Updated 2 min ago" in a `context` block at the top, as a
  localized date.
- **Make status rows self-explanatory**: name, state, and the last outcome. For example,
  `*Daily digest* · paused` and `_Last run Tue 8:00 AM: nothing to report_`.
- **Remove stale controls.** After an action completes, show a view that reflects it, rather than
  leaving a button that does nothing.

## Different people, different Home tabs

Each person gets their own Home tab, so it can, and often should, differ by role.

- **Show each person only what they're allowed to see.** Decide on the server what each role
  (owner, admin, member, guest) gets, and build the view from that. Hiding a button isn't access
  control; the action handler must check permissions too.
- **Let owners and admins preview other roles' views**: a "View as Member" button that shows them
  the reduced view, with a `context` line saying they're previewing and a button back.

## A review surface for agents

When an app or agent acts on someone's behalf, the Home tab is where they check what it did.

- **List recent actions and conversations**, newest first, each with who, where, when, and a
  short excerpt, and a button to read the full record in a modal.
- **Show pending items above the history** (approvals waiting, failed runs), with a direct action
  for each.
- **Give people a place to manage trust**: revoke an "Always Allow", reconnect an app, or pause a
  routine.

## Long content

- **Link out rather than paging inside the Home tab.** A short, current summary plus a link beats
  a long view people have to scroll through.
- **Split long text across `section` blocks** when you do show it, and add a `context` line such
  as "File continues beyond what this view can show" with a link to the full content.

## Implementation notes

- **Publish with `views.publish`**, per person, on the `app_home_opened` event and whenever their
  data changes. The view holds up to 100 blocks.
- **Detect a first visit or a long absence** from `app_home_opened`, using your own record of when
  the person last opened it.
- **Localize timestamps** with a `date` element in `rich_text` or mrkdwn's `<!date^…>` syntax.
- **Keep each text field under 3,000 characters.**
- **Publish a role preview to the admin's own user ID**, and check the real role in every
  handler.

## Quick self-review

1. Is the most important content for this person at the top, with at most one or two main
   actions?
2. What does a brand-new person see, and what does the view show when a section is empty?
3. Is the view published on open and whenever the data changes, with no stale controls?
4. Does each role see only what it should, with permissions checked in the handlers?
5. If the app acts on people's behalf, can they review and manage what it did here?
