import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent

# package.json (committed at the repo root) is the version source of truth; changesets
# bumps it, then this script synchronizes the version out to everywhere else its defined.
PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
CLAUDE_PLUGIN_PATH = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR_PLUGIN_PATH = REPO_ROOT / ".cursor-plugin" / "plugin.json"
CODEX_PLUGIN_PATH = REPO_ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
AGENT_SETUP_PROMPT_PATH = REPO_ROOT / "public" / "agent-setup" / "prompt.md"
SKILLS_SOURCE_PATTERN = re.compile(r"(https://github\.com/slackapi/slack-skills-plugin/tree/)v[^\s)]+")


def read_version(package_path: Path) -> str:
    """Return the ``version`` field from ``package.json``."""
    version: str = json.loads(package_path.read_text())["version"]
    return version


def write_version(plugin_path: Path, version: str) -> None:
    """Set the ``version`` field of a JSON plugin manifest."""
    manifest = json.loads(plugin_path.read_text())
    manifest["version"] = version
    plugin_path.write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info(f"Set {plugin_path} version to {version}")


def write_marketplace_ref(marketplace_path: Path, version: str) -> None:
    """Point the ``slack`` entry of a Claude Code marketplace at the release tag for ``version``."""
    marketplace = json.loads(marketplace_path.read_text())
    tag = f"v{version}"
    for plugin in marketplace["plugins"]:
        if plugin["name"] == "slack":
            plugin["source"]["ref"] = tag
    marketplace_path.write_text(json.dumps(marketplace, indent=2) + "\n")
    logger.info(f"Set {marketplace_path} ref to {tag}")


def write_agent_setup_ref(prompt_path: Path, version: str) -> None:
    """Point the agent setup prompt's ``npx skills add`` source at the release tag for ``version``."""
    tag = f"v{version}"
    prompt, count = SKILLS_SOURCE_PATTERN.subn(rf"\g<1>{tag}", prompt_path.read_text())
    if count == 0:
        raise ValueError(f"{prompt_path} has no slack-skills-plugin tree URL to point at {tag}")
    prompt_path.write_text(prompt)
    logger.info(f"Set {prompt_path} skills source to {tag}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    version = read_version(PACKAGE_JSON_PATH)
    write_version(CLAUDE_PLUGIN_PATH, version)
    write_version(CURSOR_PLUGIN_PATH, version)
    write_version(CODEX_PLUGIN_PATH, version)
    write_marketplace_ref(CLAUDE_MARKETPLACE_PATH, version)
    write_agent_setup_ref(AGENT_SETUP_PROMPT_PATH, version)


if __name__ == "__main__":
    main()
