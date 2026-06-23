"""Seed an ephemeral root ``package.json`` for the release workflow.

Changesets (and the ``changesets/action``) are Node tools that require a
``package.json`` at the repo root to operate. We don't want a Node artifact
committed here, so the release workflow generates one on the fly, seeded from the
real source of truth: the ``version`` in ``.claude-plugin/plugin.json``. The file
is gitignored and never enters a commit or PR.

The package is marked ``private`` so ``changeset publish`` skips npm and only
creates the git tag + GitHub release.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_PLUGIN_PATH = REPO_ROOT / ".claude-plugin" / "plugin.json"
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"

# Must match the package name used in changeset frontmatter (``"slack": minor``).
PACKAGE_NAME = "slack"


def read_version(plugin_path: Path) -> str:
    """Return the ``version`` field from a plugin manifest."""
    manifest = json.loads(plugin_path.read_text())
    return manifest["version"]


def seed(plugin_path: Path = CLAUDE_PLUGIN_PATH, package_path: Path = PACKAGE_JSON_PATH) -> str:
    """Write an ephemeral ``package.json`` seeded from the plugin manifest.

    Returns the version that was written.
    """
    version = read_version(plugin_path)
    package = {"name": PACKAGE_NAME, "version": version, "private": True}
    package_path.write_text(json.dumps(package, indent=2) + "\n")
    logger.info(f"Seeded {package_path} at version {version}")
    return version


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    seed()


if __name__ == "__main__":
    main()
