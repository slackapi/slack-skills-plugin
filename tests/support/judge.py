import json
import random
import subprocess
import tempfile
from typing import TypeVar

from deepeval.models import DeepEvalBaseLLM, GeminiModel
from pydantic import BaseModel

from tests.config import (
    EVAL_CLAUDE_BIN,
    EVAL_CLAUDE_MODEL,
    EVAL_PROVIDER,
    GEMINI_API_KEY_POOL,
    GEMINI_MODEL,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

CLAUDE_CODE_SYSTEM_PROMPT = "Answer the request with the structured output it asks for. Do not use any tools."


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
            CLAUDE_CODE_SYSTEM_PROMPT,
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


def make_judge_model() -> GeminiModel | ClaudeCodeModel:
    if EVAL_PROVIDER == "claude-code":
        return ClaudeCodeModel()
    return GeminiModel(model=GEMINI_MODEL, api_key=random.choice(GEMINI_API_KEY_POOL), temperature=0)
