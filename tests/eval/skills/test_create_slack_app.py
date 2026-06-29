import pytest
from deepeval import assert_test
from deepeval.metrics import ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

from tests.config import GEMINI_API_KEY
from tests.skill import load_skill
from tests.support.judge import make_judge_model

PROMPT = "Create a new Slack app with a slash command and event subscription"


class TestCreateSlackApp:
    def setup_method(self):
        if not GEMINI_API_KEY:
            pytest.fail("GEMINI_API_KEY not set")
        self.skill = load_skill("create-slack-app")
        self.model = make_judge_model()

    def test_skill_is_usable(self):
        skill_tool = ToolCall(
            name=self.skill.metadata.name,
            description=self.skill.metadata.description,
            input_parameters={"request": PROMPT},
            output=self.skill.body,
        )

        expected_tool = ToolCall(
            name=self.skill.metadata.name,
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
