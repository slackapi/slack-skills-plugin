from deepeval import assert_test
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from tests.config import OLLAMA_MODEL
from tests.skill import load_skill
from tests.support.ollama import NoThinkOllamaModel

PROMPT = "How do I create and deploy a new Slack app using the CLI?"


class TestSlackCli:
    def setup_method(self):
        self.skill = load_skill("slack-cli")
        self.model = NoThinkOllamaModel(model=OLLAMA_MODEL)

    def test_skill_is_usable(self):
        skill_tool = ToolCall(
            name=self.skill.frontmatter.name,
            description=self.skill.frontmatter.description,
            input_parameters={"request": PROMPT},
            output=self.skill.body,
        )

        expected_tool = ToolCall(
            name=self.skill.frontmatter.name,
            input_parameters={"request": PROMPT},
            output=self.skill.body,
        )

        response, _ = self.model.generate(
            f"You have access to the following skill:\n\n"
            f"Name: {skill_tool.name}\n"
            f"Description: {skill_tool.description}\n\n"
            f"User request: {PROMPT}"
        )

        test_case = LLMTestCase(
            input=PROMPT,
            actual_output=response,
            tools_called=[skill_tool],
            expected_tools=[expected_tool],
        )

        metric = ToolCorrectnessMetric(model=self.model, threshold=0.8)
        assert_test(test_case, [metric])
