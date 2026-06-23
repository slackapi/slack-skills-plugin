import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load(module_name: str):
    """Import a script from scripts/ by path (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS_DIR / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed_package_json = _load("seed_package_json")
sync_plugin_versions = _load("sync_plugin_versions")


def _write_manifest(path: Path, version: str, **extra) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"name": "slack", "version": version, **extra}, indent=2) + "\n")


class TestSeedPackageJson:
    def test_seeds_from_plugin_version(self, tmp_path):
        plugin = tmp_path / ".claude-plugin" / "plugin.json"
        _write_manifest(plugin, "2.3.4")
        package = tmp_path / "package.json"

        returned = seed_package_json.seed(plugin_path=plugin, package_path=package)

        data = json.loads(package.read_text())
        assert returned == "2.3.4"
        assert data == {"name": "slack", "version": "2.3.4", "private": True}

    def test_private_so_publish_skips_npm(self, tmp_path):
        plugin = tmp_path / "plugin.json"
        _write_manifest(plugin, "1.0.0")
        package = tmp_path / "package.json"

        seed_package_json.seed(plugin_path=plugin, package_path=package)

        assert json.loads(package.read_text())["private"] is True

    def test_idempotent(self, tmp_path):
        plugin = tmp_path / "plugin.json"
        _write_manifest(plugin, "1.0.0")
        package = tmp_path / "package.json"

        seed_package_json.seed(plugin_path=plugin, package_path=package)
        first = package.read_text()
        seed_package_json.seed(plugin_path=plugin, package_path=package)

        assert package.read_text() == first


class TestSyncPluginVersions:
    def test_syncs_into_all_manifests(self, tmp_path):
        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "slack", "version": "9.9.9"}) + "\n")
        claude = tmp_path / ".claude-plugin" / "plugin.json"
        cursor = tmp_path / ".cursor-plugin" / "plugin.json"
        _write_manifest(claude, "1.1.0")
        _write_manifest(cursor, "1.1.0")

        returned = sync_plugin_versions.sync(package_path=package, manifests=(claude, cursor))

        assert returned == "9.9.9"
        assert json.loads(claude.read_text())["version"] == "9.9.9"
        assert json.loads(cursor.read_text())["version"] == "9.9.9"

    def test_preserves_other_fields_and_key_order(self, tmp_path):
        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "slack", "version": "2.0.0"}) + "\n")
        manifest = tmp_path / "plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            json.dumps({"name": "slack", "description": "d", "version": "1.0.0"}, indent=2) + "\n"
        )

        sync_plugin_versions.sync(package_path=package, manifests=(manifest,))

        data = json.loads(manifest.read_text())
        assert data == {"name": "slack", "description": "d", "version": "2.0.0"}
        # version stays in its original position (last key)
        assert list(data) == ["name", "description", "version"]

    def test_trailing_newline(self, tmp_path):
        package = tmp_path / "package.json"
        package.write_text(json.dumps({"name": "slack", "version": "2.0.0"}) + "\n")
        manifest = tmp_path / "plugin.json"
        _write_manifest(manifest, "1.0.0")

        sync_plugin_versions.sync(package_path=package, manifests=(manifest,))

        assert manifest.read_text().endswith("}\n")


class TestVersionRoundTrip:
    def test_seed_then_sync_propagates_version(self, tmp_path):
        # Mirrors the workflow: seed package.json from plugin.json, (a bump would
        # happen here), then sync package.json's version back into the manifests.
        claude = tmp_path / ".claude-plugin" / "plugin.json"
        cursor = tmp_path / ".cursor-plugin" / "plugin.json"
        _write_manifest(claude, "1.1.0")
        _write_manifest(cursor, "1.1.0")
        package = tmp_path / "package.json"

        seed_package_json.seed(plugin_path=claude, package_path=package)
        # Simulate `changeset version` bumping package.json.
        bumped = json.loads(package.read_text())
        bumped["version"] = "1.2.0"
        package.write_text(json.dumps(bumped, indent=2) + "\n")

        sync_plugin_versions.sync(package_path=package, manifests=(claude, cursor))

        assert json.loads(claude.read_text())["version"] == "1.2.0"
        assert json.loads(cursor.read_text())["version"] == "1.2.0"
