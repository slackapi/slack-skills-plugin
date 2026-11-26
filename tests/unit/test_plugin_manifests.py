import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
PACKAGE_JSON = REPO_ROOT / "package.json"

# Every plugin manifest that scripts/sync_versions.py keeps on the package.json version
PLUGIN_MANIFESTS = (
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
    REPO_ROOT / ".codex-plugin" / "plugin.json",
    REPO_ROOT / ".antigravity-plugin" / "plugin.json",
)


def read_json(path: Path) -> dict:
    data: dict = json.loads(path.read_text())
    return data


@pytest.mark.parametrize("manifest", PLUGIN_MANIFESTS, ids=lambda p: p.parent.name)
class TestPluginManifests:
    def test_name_is_slack(self, manifest: Path) -> None:
        assert read_json(manifest)["name"] == "slack"

    def test_version_matches_package_json(self, manifest: Path) -> None:
        assert read_json(manifest)["version"] == read_json(PACKAGE_JSON)["version"]


class TestAntigravityManifest:
    def setup_method(self) -> None:
        self.manifest = read_json(REPO_ROOT / ".antigravity-plugin" / "plugin.json")

    def test_uses_antigravity_schema(self) -> None:
        assert self.manifest["$schema"] == "https://antigravity.google/schemas/v1/plugin.json"

    def test_loads_default_skills_dir(self) -> None:
        # Antigravity loads skills/ from the plugin root by default. The skills field only adds extra directories.
        assert "skills" not in self.manifest
        assert (REPO_ROOT / "skills").is_dir()
