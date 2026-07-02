#!/usr/bin/env bash
set -euo pipefail

npx changeset version
python scripts/sync_versions.py
