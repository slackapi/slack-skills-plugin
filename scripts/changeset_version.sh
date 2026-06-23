#!/usr/bin/env bash
set -euo pipefail

npx --yes @changesets/cli version
python scripts/sync_versions.py
