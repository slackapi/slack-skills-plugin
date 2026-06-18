import argparse
import json
import logging
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_DIR = Path.home() / ".claude"
INSTALLED = CLAUDE_DIR / "plugins" / "installed_plugins.json"
SETTINGS = CLAUDE_DIR / "settings.json"

MARKETPLACE_NAME = "slack-dev"

logger = logging.getLogger("cursor")


def get_plugin_key(plugin_name: str):
    return f"{plugin_name}@{MARKETPLACE_NAME}"


def get_target_path():
    return Path.home() / ".cursor" / "plugins" / MARKETPLACE_NAME


def plugin_name() -> str:
    """Read the plugin name from the Cursor manifest so renames are picked up."""
    manifest = json.loads((REPO_ROOT / ".cursor-plugin" / "plugin.json").read_text())
    return manifest["name"]


PLUGIN_PATHS = (
    ".claude-plugin",
    ".cursor-plugin",
    ".mcp.json",
    ".cursor-mcp.json",
    "skills",
    "commands",
)
IGNORED_NAMES = frozenset({".DS_Store", "__pycache__"})


def is_ignored(path: Path) -> bool:
    return path.suffix == ".pyc" or bool(IGNORED_NAMES & set(path.parts))


def plugin_files() -> list[Path]:
    files = []
    for name in PLUGIN_PATHS:
        source = REPO_ROOT / name
        if not source.exists():
            continue
        if source.is_file():
            files.append(source)
            continue
        for path in source.rglob("*"):
            if path.is_file() and not is_ignored(path):
                files.append(path)
    return files


def load_json(path: Path) -> dict:
    if not path.exists() or not path.read_text().strip():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def sync() -> None:
    name = plugin_name()
    plugin_key = get_plugin_key(name)
    target = get_target_path()

    shutil.rmtree(target, ignore_errors=True)
    files = plugin_files()
    if not files:
        logger.warning(f"No plugin files found under {REPO_ROOT} — nothing to sync")
        return
    for source in files:
        dest = target / source.relative_to(REPO_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    logger.info(f"Copied {len(files)} files to {target}")

    installed = load_json(INSTALLED)
    installed.setdefault("plugins", {})[plugin_key] = [{"scope": "user", "installPath": str(target)}]
    save_json(INSTALLED, installed)
    logger.info(f"Registered '{plugin_key}' in {INSTALLED}")

    settings = load_json(SETTINGS)
    settings.setdefault("enabledPlugins", {})[plugin_key] = True
    save_json(SETTINGS, settings)
    logger.info(f"Enabled '{plugin_key}' in {SETTINGS}")

    logger.info("Reload plugins in Cursor to pick up the changes.")


def wipe() -> None:
    name = plugin_name()
    plugin_key = get_plugin_key(name)
    target = get_target_path()

    shutil.rmtree(target, ignore_errors=True)
    logger.info(f"Removed {target}")

    installed = load_json(INSTALLED)
    if installed.get("plugins", {}).pop(plugin_key, None) is not None:
        save_json(INSTALLED, installed)
        logger.info(f"Wiped '{plugin_key}' from {INSTALLED}")
    else:
        logger.warning(f"'{plugin_key}' already wiped from {INSTALLED}")

    settings = load_json(SETTINGS)
    if settings.get("enabledPlugins", {}).pop(plugin_key, None) is not None:
        save_json(SETTINGS, settings)
        logger.info(f"Wiped '{plugin_key}' from {SETTINGS}")
    else:
        logger.warning(f"'{plugin_key}' already wiped from {SETTINGS}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cursor.py",
        description=(
            "Install or remove this plugin in a local Cursor for development. "
            "Copies the plugin files into ~/.cursor/plugins, then registers and "
            "enables it via ~/.claude/."
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("sync", help="Install this plugin into a local Cursor (~/.cursor/plugins)").set_defaults(
        func=sync
    )
    subcommands.add_parser("wipe", help="Remove this plugin from a local Cursor install").set_defaults(func=wipe)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()
