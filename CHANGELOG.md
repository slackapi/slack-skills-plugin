# slack

## 1.1.1

### Patch Changes

- c4caf79: Add rumdl Markdown linting to `make lint`/`make format` and clean up formatting across the skill and command docs.
- 3906698: Automate release announcements to the internal maintainers' Slack channel from the release workflow.
- 7bd09ea: Drop the `--experiment=sandboxes` flag from `slack sandbox` invocations in the `create-slack-app` skill. The experiment has been removed from `slack-cli`, so the flag now surfaces an unknown-experiment warning that can confuse users and agents.
- 9ea300a: Fix the `homepage` field in `.claude-plugin/plugin.json` to point to this repository instead of `slackapi/slack-mcp-cursor-plugin`, which does not exist and returned a 404.
- 9635a2f: Publish GitHub Releases from the release workflow so each tag has release notes.
- 46f5c53: Update the `homepage` field in `.claude-plugin/plugin.json` and repo links in docs to point to `slackapi/slack-skills-plugin`, the repository's new name.
