import json
from pathlib import Path

import pytest

from scripts.antigravity import copy_plugin

REPO_ROOT = Path(__file__).parent.parent.parent
PACKAGE_JSON = REPO_ROOT / "package.json"

SYNCED_PLUGIN_MANIFESTS = (
    REPO_ROOT / ".claude-plugin" / "plugin.json",
    REPO_ROOT / ".cursor-plugin" / "plugin.json",
    REPO_ROOT / ".codex-plugin" / "plugin.json",
    REPO_ROOT / ".antigravity-plugin" / "plugin.json",
)


def read_json(path: Path) -> dict:
    data: dict = json.loads(path.read_text())
    return data


@pytest.mark.parametrize("manifest", SYNCED_PLUGIN_MANIFESTS, ids=lambda p: p.parent.name)
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

    def test_omits_skills_field_to_use_default_dir(self) -> None:
        assert "skills" not in self.manifest
        assert (REPO_ROOT / "skills").is_dir()


class TestAntigravityStaging:
    def test_copies_only_manifest_and_skills(self, tmp_path: Path) -> None:
        copy_plugin(tmp_path)
        staged = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()}
        assert Path(".antigravity-plugin/plugin.json") in staged
        assert Path("skills/block-kit/SKILL.md") in staged
        assert all(path.parts[0] in {".antigravity-plugin", "skills"} for path in staged)
