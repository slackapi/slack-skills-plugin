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


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    version = read_version(CLAUDE_PLUGIN_PATH)

    package = {"name": PACKAGE_NAME, "version": version, "private": True}

    PACKAGE_JSON_PATH.write_text(json.dumps(package, indent=2) + "\n")

    logger.info(f"Seeded {PACKAGE_JSON_PATH} at version {version}")


if __name__ == "__main__":
    main()
