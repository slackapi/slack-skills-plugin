import json
import subprocess
from typing import Any

import pytest
from pydantic import BaseModel

from tests.support import judge
from tests.support.judge import ClaudeCodeModel


class Pick(BaseModel):
    tool_name: str


def fake_run(stdout: str, returncode: int = 0) -> Any:
    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        run.cmd = cmd  # type: ignore[attr-defined]
        run.input = kwargs["input"]  # type: ignore[attr-defined]
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="boom")

    return run


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
    def test_claude_code_provider_returns_claude_code_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(judge, "EVAL_PROVIDER", "claude-code")

        assert isinstance(judge.make_judge_model(), ClaudeCodeModel)
