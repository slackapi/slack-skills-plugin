# Changesets

This folder drives the release process. Each user-facing change ships with a
**changeset** — a small markdown file describing the change and how it bumps the
version. On merge to `main`, the release workflow consumes accumulated changesets,
opens a "Version Packages" PR, and (once that PR is merged) tags the release and
publishes a GitHub release.

See [Versioning](../.github/maintainers_guide.md#versioning) for the full flow.

## Adding a changeset

You do **not** need Node.js installed. Either run the helper:

```sh
make changeset
```

…or hand-write a file named `.changeset/<anything>.md` (the name is arbitrary; one
per PR is conventional) with this format:

```md
---
"slack": minor
---

Add the channel-digest command
```

- The frontmatter key is the package name, always `"slack"` (this repo ships a single
  package). The value is the semver bump level: `patch`, `minor`, or `major`.
- The body becomes the changelog entry, so write it for a reader of the release notes:
  **what** changed and, when relevant, **why**.

## Choosing a bump level

- `patch` — bug fixes and docs/internal changes that don't alter behavior for users.
- `minor` — new skills, commands, or capabilities (backwards compatible).
- `major` — breaking changes to existing behavior.

A PR with no user-facing change (e.g. CI tweaks) needs no changeset.
