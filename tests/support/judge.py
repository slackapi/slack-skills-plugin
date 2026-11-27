import json
import random
import subprocess
import tempfile
from typing import TypeVar

from deepeval.models import DeepEvalBaseLLM, GeminiModel
from pydantic import BaseModel

from tests.config import (
    EVAL_ANTIGRAVITY_BIN,
    EVAL_ANTIGRAVITY_MODEL,
    EVAL_CLAUDE_BIN,
    EVAL_CLAUDE_MODEL,
    EVAL_PROVIDER,
    GEMINI_API_KEY_POOL,
    GEMINI_MODEL,
    PLUGIN_NAME,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

STRUCTURED_OUTPUT_INSTRUCTION = "Answer the request with the structured output it asks for. Do not use any tools."


class AntigravityModel(DeepEvalBaseLLM):
    def __init__(self, model: str = EVAL_ANTIGRAVITY_MODEL, executable: str = EVAL_ANTIGRAVITY_BIN) -> None:
        self.executable = executable
        self.model_name = model
        super().__init__(model)

    def load_model(self) -> AntigravityModel:
        return self

    def get_model_name(self) -> str:
        return f"antigravity ({self.model_name or 'default'})"

    def command(self, prompt: str, schema: type[BaseModel]) -> list[str]:
        model = ["--model", self.model_name] if self.model_name else []
        return [
            self.executable,
            *model,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema.model_json_schema()),
            "--disable-slash-commands",
            f"--print={STRUCTURED_OUTPUT_INSTRUCTION}\n\n{prompt}",
        ]

    def enabled_plugin(self) -> str | None:
        result = subprocess.run(
            [self.executable, "plugin", "list", "--json"], capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"{self.executable} plugin list exited {result.returncode}: {result.stderr.strip()}")
        try:
            plugins = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"{self.executable} plugin list printed output that is not JSON: {result.stdout.strip()!r}"
            ) from error
        if not isinstance(plugins, list):
            raise RuntimeError(f"{self.executable} plugin list printed JSON that is not a list: {plugins!r}")
        for plugin in plugins:
            if isinstance(plugin, dict) and plugin.get("name") == PLUGIN_NAME and plugin.get("enabled"):
                return str(plugin.get("path", PLUGIN_NAME))
        return None

    def generate(self, prompt: str, schema: type[SchemaT]) -> tuple[SchemaT, float]:  # type: ignore[override]
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                self.command(prompt, schema),
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=180,
                check=False,
            )
        if result.returncode != 0:
            raise RuntimeError(
                f"{self.executable} exited {result.returncode}: {result.stderr.strip() or result.stdout.strip()}"
            )
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"{self.executable} printed output that is not JSON: {result.stdout.strip()!r}"
            ) from error
        if output.get("status") != "SUCCESS" or "structured_output" not in output:
            raise RuntimeError(f"{self.executable} returned no structured output: {output.get('response')!r}")
        return schema.model_validate(output["structured_output"]), 0.0

    async def a_generate(self, prompt: str, schema: type[SchemaT]) -> tuple[SchemaT, float]:  # type: ignore[override]
        return self.generate(prompt, schema)


class ClaudeCodeModel(DeepEvalBaseLLM):
    def __init__(self, model: str = EVAL_CLAUDE_MODEL, executable: str = EVAL_CLAUDE_BIN) -> None:
        self.executable = executable
        self.model_name = model
        super().__init__(model)

    def load_model(self) -> ClaudeCodeModel:
        return self

    def get_model_name(self) -> str:
        return f"claude-code ({self.model_name})"

    def command(self, schema: type[BaseModel]) -> list[str]:
        return [
            self.executable,
            "-p",
            "--model",
            self.model_name,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema.model_json_schema()),
            "--system-prompt",
            STRUCTURED_OUTPUT_INSTRUCTION,
            "--tools",
            "",
            "--setting-sources",
            "",
            "--no-session-persistence",
            "--safe-mode",
        ]

    def generate(self, prompt: str, schema: type[SchemaT]) -> tuple[SchemaT, float]:  # type: ignore[override]
        # Claude Code still tells the model its working directory, so run it somewhere that
        # isn't this repo, whose name would hint at the plugin's skills.
        with tempfile.TemporaryDirectory() as cwd:
            result = subprocess.run(
                self.command(schema),
                input=prompt,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=180,
                check=False,
            )
        if result.returncode != 0:
            raise RuntimeError(
                f"{self.executable} exited {result.returncode}: {result.stderr.strip() or result.stdout.strip()}"
            )
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"{self.executable} printed output that is not JSON: {result.stdout.strip()!r}"
            ) from error
        if output.get("is_error") or "structured_output" not in output:
            raise RuntimeError(f"{self.executable} returned no structured output: {output.get('result')!r}")
        return schema.model_validate(output["structured_output"]), float(output.get("total_cost_usd", 0.0))

    async def a_generate(self, prompt: str, schema: type[SchemaT]) -> tuple[SchemaT, float]:  # type: ignore[override]
        return self.generate(prompt, schema)


def make_judge_model() -> GeminiModel | AntigravityModel | ClaudeCodeModel:
    if EVAL_PROVIDER == "antigravity":
        return AntigravityModel()
    if EVAL_PROVIDER == "claude-code":
        return ClaudeCodeModel()
    return GeminiModel(model=GEMINI_MODEL, api_key=random.choice(GEMINI_API_KEY_POOL), temperature=0)
