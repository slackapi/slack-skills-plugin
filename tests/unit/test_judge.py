import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from tests.support import judge
from tests.support.judge import AntigravityModel, ClaudeCodeModel

REPO_ROOT = Path(__file__).resolve().parents[2]


class Pick(BaseModel):
    tool_name: str


def fake_run(stdout: str, returncode: int = 0) -> Any:
    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        run.cmd = cmd  # type: ignore[attr-defined]
        run.input = kwargs.get("input")  # type: ignore[attr-defined]
        run.cwd = kwargs.get("cwd")  # type: ignore[attr-defined]
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="boom")

    return run


class TestAntigravityModel:
    def test_parses_structured_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        output = {"status": "SUCCESS", "structured_output": {"tool_name": "block-kit"}}
        run = fake_run(json.dumps(output))
        monkeypatch.setattr(subprocess, "run", run)

        choice, cost = AntigravityModel(model="gemini-3.8-flash-low", executable="my-agy").generate(
            "pick one", schema=Pick
        )

        assert choice == Pick(tool_name="block-kit")
        assert cost == 0.0
        assert run.cmd[:3] == ["my-agy", "--model", "gemini-3.8-flash-low"]
        assert run.cmd[-1] == f"--print={judge.STRUCTURED_OUTPUT_INSTRUCTION}\n\npick one"

    def test_runs_outside_the_repo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        run = fake_run(json.dumps({"status": "SUCCESS", "structured_output": {"tool_name": "block-kit"}}))
        monkeypatch.setattr(subprocess, "run", run)

        AntigravityModel(model="").generate("pick one", schema=Pick)

        assert run.cwd is not None
        assert not Path(run.cwd).resolve().is_relative_to(REPO_ROOT)

    def test_blank_model_uses_the_cli_default(self) -> None:
        assert "--model" not in AntigravityModel(model="").command("pick one", Pick)

    def test_turns_off_slash_commands_and_sets_schema(self) -> None:
        cmd = AntigravityModel(model="").command("pick one", Pick)

        assert "--disable-slash-commands" in cmd
        assert json.loads(cmd[cmd.index("--json-schema") + 1]) == Pick.model_json_schema()

    def test_nonzero_exit_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run("", returncode=1))

        with pytest.raises(RuntimeError, match="exited 1: boom"):
            AntigravityModel(model="").generate("pick one", schema=Pick)

    def test_missing_structured_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps({"status": "SUCCESS", "response": ""})))

        with pytest.raises(RuntimeError, match="no structured output"):
            AntigravityModel(model="").generate("pick one", schema=Pick)

    def test_non_success_status_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        output = {"status": "ERROR", "structured_output": {"tool_name": "block-kit"}, "response": "quota reached"}
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps(output)))

        with pytest.raises(RuntimeError, match="quota reached"):
            AntigravityModel(model="").generate("pick one", schema=Pick)

    def test_non_json_output_raises_with_the_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run("Update available!"))

        with pytest.raises(RuntimeError, match="not JSON: 'Update available!'"):
            AntigravityModel(model="").generate("pick one", schema=Pick)

    def test_enabled_plugin_returns_its_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        plugins = [{"name": judge.PLUGIN_NAME, "enabled": True, "path": "/plugins/slack"}]
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps(plugins)))

        assert AntigravityModel(model="").enabled_plugin() == "/plugins/slack"

    def test_disabled_or_missing_plugin_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        plugins = [{"name": judge.PLUGIN_NAME, "enabled": False}, {"name": "other", "enabled": True}]
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps(plugins)))

        assert AntigravityModel(model="").enabled_plugin() is None

    def test_enabled_plugin_empty_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run(""))

        with pytest.raises(RuntimeError, match="plugin list printed output that is not JSON"):
            AntigravityModel(model="").enabled_plugin()

    def test_enabled_plugin_non_json_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run("Update available!"))

        with pytest.raises(RuntimeError, match="plugin list printed output that is not JSON"):
            AntigravityModel(model="").enabled_plugin()

    def test_enabled_plugin_non_list_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps({"plugins": []})))

        with pytest.raises(RuntimeError, match="not a list"):
            AntigravityModel(model="").enabled_plugin()


class TestClaudeCodeModel:
    def test_parses_structured_output_and_cost(self, monkeypatch: pytest.MonkeyPatch) -> None:
        run = fake_run(json.dumps({"structured_output": {"tool_name": "slack-docs"}, "total_cost_usd": 0.003}))
        monkeypatch.setattr(subprocess, "run", run)

        choice, cost = ClaudeCodeModel(model="haiku", executable="my-claude").generate("pick one", schema=Pick)

        assert choice == Pick(tool_name="slack-docs")
        assert cost == 0.003
        assert run.cmd[:4] == ["my-claude", "-p", "--model", "haiku"]
        assert run.input == "pick one"

    def test_turns_off_tools_settings_and_mcp(self) -> None:
        cmd = ClaudeCodeModel(model="haiku").command(Pick)

        assert cmd[cmd.index("--tools") + 1] == ""
        assert cmd[cmd.index("--setting-sources") + 1] == ""
        assert json.loads(cmd[cmd.index("--json-schema") + 1]) == Pick.model_json_schema()

    def test_nonzero_exit_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run("", returncode=1))

        with pytest.raises(RuntimeError, match="exited 1: boom"):
            ClaudeCodeModel(model="haiku").generate("pick one", schema=Pick)

    def test_missing_structured_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run(json.dumps({"is_error": True, "result": "Not logged in"})))

        with pytest.raises(RuntimeError, match="Not logged in"):
            ClaudeCodeModel(model="haiku").generate("pick one", schema=Pick)

    def test_non_json_output_raises_with_the_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", fake_run("Update available!"))

        with pytest.raises(RuntimeError, match="not JSON: 'Update available!'"):
            ClaudeCodeModel(model="haiku").generate("pick one", schema=Pick)

    def test_turns_off_customizations(self) -> None:
        assert "--safe-mode" in ClaudeCodeModel(model="haiku").command(Pick)


class TestMakeJudgeModel:
    def test_antigravity_provider_returns_antigravity_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(judge, "EVAL_PROVIDER", "antigravity")

        assert isinstance(judge.make_judge_model(), AntigravityModel)

    def test_claude_code_provider_returns_claude_code_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(judge, "EVAL_PROVIDER", "claude-code")

        assert isinstance(judge.make_judge_model(), ClaudeCodeModel)
