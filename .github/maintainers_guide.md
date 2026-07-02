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

Install necessary Python runtime for development/testing.

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

Follow the [conventional commit specification][conv-commits]. PR titles and commit messages use prefixes like `feat:`, `fix:`, `chore:`, `docs:`, etc. First letter after the prefix is lowercase unless it's a proper noun.

### 🎁 Updating Changesets

This project uses [Changesets](https://github.com/changesets/changesets) to track changes and automate releases.

Each changeset describes a change to the package and its [semver][semver] impact, and a new changeset should be added when updating the package with some change that affects consumers:

```sh
make changeset
```

Alternatively, hand-write a file named `.changeset/<anything>.md`, with this format:

```md
---
"slack": minor
---

Add the channel-digest command
```

The frontmatter key is always `"slack"`; the value is the [semver][semver] bump level, like `patch`, `minor`, or `major`. The body becomes the changelog entry, so write it for a reader of the release notes.

Updates to documentation, tests, or CI might not require new entries.

When a PR containing changesets is merged to `main`, a different PR is opened or updated using [changesets/action](https://github.com/changesets/action) which consumes the pending changesets, bumps the package version, and updates the `CHANGELOG` in preparation to release.

### 🚀 Releases

Releasing can feel intimidating at first, but don't fret! Venture on!

New official package versions are published when the release PR created from changesets is merged. Follow these steps to build confidence:

1. **Run the tests locally**: Before merging the release PR please run all the tests especially the eval ones. If they no longer pass we may need fix it before releasing the changes.

2. **Check GitHub**: Please check if issues or pull requests are still open either decide to postpone the release or save those changes for a future update.

3. **Review the release PR**: Verify that the version bump matches expectations, `CHANGELOG` entries are clear, and CI checks pass.

4. **Merge and approve**: Merge the release PR. It may take up to 24 hours before you see you release in the [Claude Plugins](https://claude.com/plugins/slack) directory.

5. **Communicate the release**:
   - **External**: Post in relevant channels (e.g. #lang-javascript, #tools-bolt) on [Slack Community](https://community.slack.com/). Include a link to the release notes.

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
