import json
import subprocess
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).parents[2]
PLUGIN = REPO_ROOT / ".opencode" / "plugins" / "slack.js"
EXPECTED_SKILLS = {
    "block-kit",
    "create-slack-app",
    "slack-api",
    "slack-cli",
    "slack-docs",
    "slack-messaging",
    "slack-search",
    "test-slack-app",
}
EXPECTED_COMMANDS = {
    "slack-channel-digest",
    "slack-draft-announcement",
    "slack-find-discussions",
    "slack-standup",
    "slack-summarize-channel",
}

# A minimal stand-in for the OpenCode 2 plugin context: each domain's transform
# runs the callback against an in-memory editor, and session.prompt records calls.
FAKE_CONTEXT = """
const state = { skills: new Map(PRESET.skills), commands: new Map(), mcp: new Map(PRESET.mcp), prompts: [] };
const mapEditor = (map) => ({
  get: (id) => map.get(id),
  add: (entry) => map.set(entry.id ?? entry.name, entry),
  set: (name, config) => map.set(name, config),
});
const ctx = {
  skill: { transform: async (cb) => cb(mapEditor(state.skills)) },
  command: { transform: async (cb) => cb(mapEditor(state.commands)) },
  mcp: { transform: async (cb) => cb(mapEditor(state.mcp)) },
  session: { prompt: async (input) => { state.prompts.push(input); } },
};
"""


def run_setup(preset: dict[str, Any] | None = None, script: str = "") -> dict[str, Any]:
    """Load the default export and run its V2 setup against the fake context."""
    preset = preset or {"skills": [], "mcp": []}
    runner = f"""
import plugin from {json.dumps(PLUGIN.as_uri())};
const PRESET = {json.dumps(preset)};
{FAKE_CONTEXT}
await plugin.setup(ctx);
{script}
process.stdout.write(JSON.stringify({{
  id: plugin.id,
  hasServer: typeof plugin.server === "function",
  skills: Object.fromEntries(state.skills),
  commands: Object.fromEntries([...state.commands].map(([name, c]) => [name, {{ description: c.description }}])),
  mcp: Object.fromEntries(state.mcp),
  prompts: state.prompts,
}}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return cast(dict[str, Any], json.loads(result.stdout))


class TestOpenCodeV2Plugin:
    def test_default_export_carries_v2_setup_and_v1_server_entrypoints(self) -> None:
        # Act
        output = run_setup()

        # Assert
        assert output["id"] == "slack.skills"
        assert output["hasServer"] is True

    def test_setup_registers_exactly_the_canonical_skills_from_the_root(self) -> None:
        # Act
        skills = run_setup()["skills"]

        # Assert
        assert set(skills) == EXPECTED_SKILLS
        for skill_id, skill in skills.items():
            assert Path(skill["path"]) == REPO_ROOT / "skills" / skill_id / "SKILL.md"
            assert skill["description"]
            assert skill["content"]

    def test_setup_registers_exactly_the_five_slack_commands(self) -> None:
        # Act
        commands = run_setup()["commands"]

        # Assert
        assert set(commands) == EXPECTED_COMMANDS
        assert all(command["description"] for command in commands.values())

    def test_command_execution_prompts_the_template_with_arguments(self) -> None:
        # Arrange
        invoke = """
const command = state.commands.get("slack-summarize-channel");
await command.execute({ sessionID: "ses_test", prompt: { text: "engineering" }, delivery: "queue" });
"""

        # Act
        prompts = run_setup(script=invoke)["prompts"]

        # Assert
        assert len(prompts) == 1
        assert prompts[0]["sessionID"] == "ses_test"
        assert prompts[0]["delivery"] == "queue"
        assert "engineering" in prompts[0]["text"]
        assert "$ARGUMENTS" not in prompts[0]["text"]

    def test_setup_registers_remote_slack_mcp_with_v2_oauth_fields(self) -> None:
        # Act
        slack = run_setup()["mcp"]["slack"]

        # Assert
        assert slack == {
            "type": "remote",
            "url": "https://mcp.slack.com/mcp",
            "oauth": {
                "client_id": "{env:SLACK_OPENCODE_CLIENT_ID}",
                "redirect_uri": "http://127.0.0.1:19876/mcp/oauth/callback",
                "callback_port": 19876,
            },
        }

    def test_existing_slack_mcp_and_skill_are_preserved(self) -> None:
        # Arrange
        user_server = {"type": "remote", "url": "https://example.test/mcp", "oauth": False}
        user_skill = {"id": "block-kit", "name": "block-kit", "description": "mine", "content": "mine"}
        preset = {"skills": [["block-kit", user_skill]], "mcp": [["slack", user_server]]}

        # Act
        output = run_setup(preset)

        # Assert
        assert output["mcp"]["slack"] == user_server
        assert output["skills"]["block-kit"] == user_skill
