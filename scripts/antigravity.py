import argparse
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

INCLUDE: set[str] = {
    ".antigravity-plugin/**/*",
    "skills/**/*",
}
EXCLUDE: set[str] = {
    "**/.DS_Store",
    "**/__pycache__/**",
    "**/*.pyc",
}

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / ".antigravity-plugin" / "plugin.json"


def plugin_name() -> str:
    """Read the plugin name from the Antigravity manifest so renames are picked up."""
    name: str = json.loads(MANIFEST_PATH.read_text())["name"]
    return name


def plugin_files() -> set[Path]:
    included = {path for pattern in INCLUDE for path in REPO_ROOT.glob(pattern) if path.is_file()}
    excluded = {path for pattern in EXCLUDE for path in REPO_ROOT.glob(pattern)}
    return included - excluded


def copy_plugin(target: Path) -> int:
    """Copy only the files Antigravity loads, so .venv symlinks and .env secrets stay behind."""
    files = plugin_files()
    for source in files:
        dest = target / source.relative_to(REPO_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    return len(files)


def run_agy(*args: str) -> None:
    if shutil.which("agy") is None:
        sys.exit("agy not found on PATH. Install the Antigravity CLI first: https://antigravity.google/docs/install?tab=cli")
    subprocess.run(["agy", *args], check=True)


def install() -> None:
    with tempfile.TemporaryDirectory() as staging:
        target = Path(staging) / plugin_name()
        count = copy_plugin(target)
        logger.info(f"Staged {count} plugin files in {target}")
        run_agy("plugin", "install", str(target))
    logger.info("Start a new agy session to pick up the changes.")


def uninstall() -> None:
    run_agy("plugin", "uninstall", plugin_name())


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=(
            "Install or remove this plugin in the local Antigravity CLI for development. "
            "Stages the plugin files in a temporary folder, then runs `agy plugin install` on it."
        ),
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("install", help="Install this plugin into the local Antigravity CLI").set_defaults(
        func=install
    )
    subcommands.add_parser("uninstall", help="Uninstall this plugin from the local Antigravity CLI").set_defaults(
        func=uninstall
    )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    args = parser.parse_args()
    args.func()


if __name__ == "__main__":
    main()
