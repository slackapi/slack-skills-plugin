import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.skill import discover_skills

REPO_ROOT = Path(__file__).parent.parent.parent
PACKAGE_JSON = REPO_ROOT / "package.json"
PLUGIN_PATH = REPO_ROOT / ".opencode" / "plugins" / "slack.js"
SKILLS_DIR = str(REPO_ROOT / "skills")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is required to load the OpenCode plugin")


def run_plugin(script: str) -> dict:
    """Import the plugin in Node, run ``script`` against it, and return what it prints as JSON."""
    module = f"""
import plugin, {{ loadSkills, SKILLS_DIR }} from {json.dumps(PLUGIN_PATH.as_uri())};
const out = await (async () => {{ {script} }})();
console.log(JSON.stringify(out));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", module],
        capture_output=True,
        text=True,
        check=True,
    )
    data: dict = json.loads(result.stdout)
    return data


class TestPackageEntry:
    def test_main_points_at_plugin(self) -> None:
        package = json.loads(PACKAGE_JSON.read_text())
        assert (REPO_ROOT / package["main"]).resolve() == PLUGIN_PATH
        assert (REPO_ROOT / package["exports"]["."]).resolve() == PLUGIN_PATH

    def test_package_is_an_es_module(self) -> None:
        assert json.loads(PACKAGE_JSON.read_text())["type"] == "module"

    def test_default_export_has_both_entrypoints(self) -> None:
        out = run_plugin(
            "return { id: plugin.id, server: typeof plugin.server, setup: typeof plugin.setup, dir: SKILLS_DIR };"
        )
        assert out == {"id": "slack", "server": "function", "setup": "function", "dir": SKILLS_DIR}


class TestLoadSkills:
    def test_matches_yaml_frontmatter(self) -> None:
        out = run_plugin("return Object.fromEntries(loadSkills().map((s) => [s.id, s]));")
        expected = {skill.path.parent.name: skill for skill in discover_skills()}
        assert set(out) == set(expected)
        for skill_id, skill in expected.items():
            assert out[skill_id]["name"] == skill.frontmatter.name
            assert out[skill_id]["description"] == skill.frontmatter.description
            assert out[skill_id]["content"] == skill.body
            assert out[skill_id]["path"] == str(skill.path)


class TestOpenCode1:
    def test_config_hook_adds_skills_dir_once(self) -> None:
        out = run_plugin("""
            const hooks = await plugin.server({});
            const config = { skills: { paths: ["/existing"] } };
            await hooks.config(config);
            await hooks.config(config);
            return config;
        """)
        assert out == {"skills": {"paths": ["/existing", SKILLS_DIR]}}

    def test_config_hook_creates_skills_paths(self) -> None:
        out = run_plugin("""
            const hooks = await plugin.server({});
            const config = {};
            await hooks.config(config);
            return config;
        """)
        assert out == {"skills": {"paths": [SKILLS_DIR]}}

    def test_config_hook_leaves_flat_skills_array(self) -> None:
        out = run_plugin("""
            const hooks = await plugin.server({});
            const config = { skills: ["/existing"] };
            await hooks.config(config);
            return config;
        """)
        assert out == {"skills": ["/existing"]}


class TestOpenCode2:
    def test_setup_adds_each_skill(self) -> None:
        out = run_plugin("""
            const added = [];
            await plugin.setup({ skill: { transform: async (cb) => cb({ add: (s) => added.push(s.id) }) } });
            return { added };
        """)
        assert sorted(out["added"]) == sorted(skill.path.parent.name for skill in discover_skills())

    def test_setup_skips_a_rejected_skill(self) -> None:
        out = run_plugin("""
            const added = [];
            const add = (s) => { if (s.id === "block-kit") throw new Error("rejected"); added.push(s.id); };
            console.error = () => {};
            await plugin.setup({ skill: { transform: async (cb) => cb({ add }) } });
            return { added };
        """)
        assert "block-kit" not in out["added"]
        assert len(out["added"]) == len(discover_skills()) - 1

    def test_setup_falls_back_to_directory_source(self) -> None:
        out = run_plugin("""
            const sources = [];
            await plugin.setup({ skill: { transform: async (cb) => cb({ source: (s) => sources.push(s) }) } });
            return { sources };
        """)
        assert out == {"sources": [{"type": "directory", "path": SKILLS_DIR}]}

    def test_setup_ignores_a_context_without_skills(self) -> None:
        out = run_plugin("await plugin.setup({}); return { ok: true };")
        assert out == {"ok": True}
