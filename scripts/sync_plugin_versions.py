"""Sync the version from ``package.json`` into the plugin manifests.

``changeset version`` only knows how to bump ``package.json``. After it runs, this
script copies the resulting version into the two manifests that are the real
distribution artifacts — ``.claude-plugin/plugin.json`` and
``.cursor-plugin/plugin.json`` — so the "Version Packages" PR carries the bump in
both. Key order and 2-space formatting are preserved (matching ``scripts/cursor.py``).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent

PACKAGE_JSON_PATH = REPO_ROOT / "package.json"
PLUGIN_MANIFESTS = (
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
)


def read_version(package_path: Path) -> str:
    """Return the ``version`` field from ``package.json``."""
    return json.loads(package_path.read_text())["version"]


def write_version(manifest_path: Path, version: str) -> None:
    """Set the ``version`` field of a manifest, preserving order and formatting."""
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info(f"Set {manifest_path} version to {version}")


def sync(
    package_path: Path = PACKAGE_JSON_PATH,
    manifests: tuple[Path, ...] = PLUGIN_MANIFESTS,
) -> str:
    """Copy ``package.json``'s version into every manifest. Returns that version."""
    version = read_version(package_path)
    for manifest_path in manifests:
        write_version(manifest_path, version)
    return version


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sync()


if __name__ == "__main__":
    main()
