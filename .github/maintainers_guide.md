# Maintainers Guide

This document describes tools, tasks, and workflows needed to maintain the
`slackapi/slack-mcp-plugin` repository. This is a skills plugin
marketplace, so the primary maintenance work is keeping skill content accurate
and plugin versions correct rather than managing build artifacts or package
registries.

## Tools

Maintaining this repo requires:

- **[Claude Code][claude-code]**: the primary development and maintenance tool.
  Most tasks (authoring skills, reviewing diffs) are performed through Claude
  Code rather than traditional CLI tooling.
- **Git**: standard version control.
- **[GitHub CLI (`gh`)][gh-cli]**: for creating PRs as drafts and managing
  issues.

### Python (and friends)

We recommend using [pyenv](https://github.com/pyenv/pyenv) for Python runtime management. If you use macOS, follow the following steps:

```sh
brew update
brew install pyenv
```

Install necessary Python runtimes for development/testing. You can rely on GitHub Actions workflows for testing with various major versions. <https://github.com/slackapi/bolt-python/tree/main/.github/workflows>

```sh
$ pyenv install 3.14 # select the latest patch version
$ pyenv local 3.14

$ pyenv rehash
```

Then, you can create a new Virtual Environment this way:

```sh
python -m venv .venv
source .venv/bin/activate
```

---

## Versioning

Follow the [conventional commit specification][conv-commits]. PR titles and
commit messages use prefixes like `feat:`, `fix:`, `chore:`, `docs:`, etc.
First letter after the prefix is lowercase unless it's a proper noun.

### Releasing (changesets)

Releases are automated with [changesets][changesets] via
`.github/workflows/release.yml`. There is **no manual version bump or tagging** —
both `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json` are bumped for you.
The repo stays Node-free on disk: Node runs only in the release workflow, and the
`package.json` changesets needs is generated on the fly (`scripts/seed_package_json.py`)
and gitignored. `.claude-plugin/plugin.json` is the version source of truth.

**Contributors** add a changeset to any PR with a user-facing change — `make changeset`
or a hand-written `.changeset/<name>.md` (format and bump-level guidance in
[`.changeset/README.md`](../.changeset/README.md)).

**Maintainers** cut a release by merging PRs:

1. Merging a feature PR to `main` causes the release workflow to open (or update) a
   **"chore: release"** PR. It runs `changeset version`, which computes the next semver,
   writes `CHANGELOG.md`, syncs the version into both plugin manifests
   (`scripts/sync_plugin_versions.py`), and removes the consumed changesets. Review this
   PR like any other — it's where you confirm the resulting version and changelog.
2. Merge the "chore: release" PR. With no changesets left, the workflow runs
   `changeset publish`: the package is `private`, so npm is skipped, a `v<version>` git
   tag is created, and a GitHub release is published with notes drawn from `CHANGELOG.md`.

**One-time setup:** enable **Settings → Actions → General → "Allow GitHub Actions to
create and approve pull requests"** so the action can open the release PR. (Note: PRs
opened by the default `GITHUB_TOKEN` don't trigger `ci-build.yml`; the release PR is
mechanical, so this is acceptable.)

## Everything Else

### CODEOWNERS

All files are owned by `@slackapi/platform-devxp`. Any PR to this repo will
automatically request review from this team.

### Dependabot

Dependabot is configured for GitHub Actions dependencies only (daily cadence).
Patch and minor updates are auto-approved and auto-merged via the
`.github/workflows/dependencies.yml` workflow.

### Issue Triage

- Bug reports about incorrect Block Kit output should be investigated by
  checking whether the relevant live `docs.slack.dev` page has changed.
- Feature requests for new skills should be discussed in the issue before
  implementation begins.
- Labels: `bug` for confirmed issues, `enhancement` for feature requests,
  `build` for CI/tooling changes.

---

[claude-code]: https://claude.ai/code
[gh-cli]: https://cli.github.com
[conv-commits]: https://www.conventionalcommits.org
[semver]: https://semver.org
[changesets]: https://github.com/changesets/changesets
