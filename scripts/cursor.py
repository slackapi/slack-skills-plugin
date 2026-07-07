import argparse
import json
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

INCLUDE: set[str] = {
    ".claude-plugin/**/*",
    ".cursor-plugin/**/*",
    ".mcp.json",
    ".cursor-mcp.json",
    "skills/**/*",
    "commands/**/*",
}
EXCLUDE: set[str] = {
    "**/.DS_Store",
    "**/__pycache__/**",
    "**/*.pyc",
}

REPO_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_HOME_DIR = Path.home() / ".claude"
CLAUDE_INSTALLED_PLUGINS_PATH = CLAUDE_HOME_DIR / "plugins" / "installed_plugins.json"
CLAUDE_SETTINGS_PATH = CLAUDE_HOME_DIR / "settings.json"

CURSOR_PLUGINS_PATH = Path.home() / ".cursor" / "plugins"

MARKETPLACE_NAME = "local"


def get_plugin_key(plugin_name: str) -> str:
    return f"{plugin_name}@{MARKETPLACE_NAME}"


def get_target_path(plugin_key: str) -> Path:
    return CURSOR_PLUGINS_PATH / plugin_key


def plugin_name() -> str:
    """Read the plugin name from the Cursor plugin file so renames are picked up."""
    cursor_plugin = json.loads(
        (REPO_ROOT / ".cursor-plugin" / "plugin.json").read_text()
    )
    name: str = cursor_plugin["name"]
    return name


def plugin_files() -> set[Path]:
    included = {
        path
        for pattern in INCLUDE
        for path in REPO_ROOT.glob(pattern)
        if path.is_file()
    }
    excluded = {path for pattern in EXCLUDE for path in REPO_ROOT.glob(pattern)}
    return included - excluded


def load_json(path: Path) -> dict:
    if not path.exists() or not path.read_text().strip():
        return {}
    data: dict = json.loads(path.read_text())
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def install() -> None:
    name = plugin_name()
    plugin_key = get_plugin_key(name)
    target = get_target_path(plugin_key)

    files = plugin_files()
    if not files:
        logger.warning(f"No plugin files found under {REPO_ROOT}; nothing to install")
        return

    shutil.rmtree(target, ignore_errors=True)
    for source in files:
        dest = target / source.relative_to(REPO_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    logger.info(f"Copied {len(files)} plugin files to {target}")

    installed = load_json(CLAUDE_INSTALLED_PLUGINS_PATH)
    installed.setdefault("plugins", {})[plugin_key] = [
        {"scope": "user", "installPath": str(target)}
    ]
    save_json(CLAUDE_INSTALLED_PLUGINS_PATH, installed)
    logger.info(f"Registered '{plugin_key}' in {CLAUDE_INSTALLED_PLUGINS_PATH}")

    settings = load_json(CLAUDE_SETTINGS_PATH)
    settings.setdefault("enabledPlugins", {})[plugin_key] = True
    save_json(CLAUDE_SETTINGS_PATH, settings)
    logger.info(f"Enabled '{plugin_key}' in {CLAUDE_SETTINGS_PATH}")

    logger.info(
        f"Installed '{plugin_key}'. Reload plugins in Cursor to pick up the changes."
    )


def uninstall() -> None:
    name = plugin_name()
    plugin_key = get_plugin_key(name)
    target = get_target_path(plugin_key)

    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
        logger.info(f"Removed plugin files from {target}")
    else:
        logger.warning(f"No plugin files found at {target}; nothing to remove")

    installed = load_json(CLAUDE_INSTALLED_PLUGINS_PATH)
    if installed.get("plugins", {}).pop(plugin_key, None) is not None:
        save_json(CLAUDE_INSTALLED_PLUGINS_PATH, installed)
        logger.info(f"Deregistered '{plugin_key}' from {CLAUDE_INSTALLED_PLUGINS_PATH}")
    else:
        logger.warning(
            f"'{plugin_key}' was not registered in {CLAUDE_INSTALLED_PLUGINS_PATH}; nothing to remove"
        )

    settings = load_json(CLAUDE_SETTINGS_PATH)
    if settings.get("enabledPlugins", {}).pop(plugin_key, None) is not None:
        save_json(CLAUDE_SETTINGS_PATH, settings)
        logger.info(f"Disabled '{plugin_key}' in {CLAUDE_SETTINGS_PATH}")
    else:
        logger.warning(
            f"'{plugin_key}' was not enabled in {CLAUDE_SETTINGS_PATH}; nothing to remove"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=(
            "Install or remove this plugin in a local Cursor for development. "
            f"Copies the plugin files into {CURSOR_PLUGINS_PATH}, then registers and "
            f"enables it via {CLAUDE_HOME_DIR}"
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "install", help=f"Install this plugin into local Cursor ({CURSOR_PLUGINS_PATH})"
    ).set_defaults(func=install)
    subcommands.add_parser(
        "uninstall", help="Uninstall this plugin from local Cursor"
    ).set_defaults(func=uninstall)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()
