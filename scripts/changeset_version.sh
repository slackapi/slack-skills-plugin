#!/usr/bin/env bash
# The `version` command for changesets/action.
#
# `changeset version` consumes the accumulated changesets: it bumps the ephemeral
# package.json, writes CHANGELOG.md, and deletes the consumed changeset files. We
# then sync the new version into the two plugin manifests so the "Version Packages"
# PR carries the bump everywhere it matters. The action commits all of this.
set -euo pipefail

CHANGESETS_CLI="@changesets/cli@^2.27"

npx --yes "${CHANGESETS_CLI}" version
python scripts/sync_plugin_versions.py
