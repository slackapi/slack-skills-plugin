from typing import TypedDict

import pytest
from deepeval.test_case import ToolCall
from pydantic import BaseModel

from tests.config import OLLAMA_MODEL, SLACK_MCP_TOKEN
from tests.support.ollama import NoThinkOllamaModel
from tests.support.tools import get_all_skill_tools, get_slack_mcp_tools


class Scenario(TypedDict):
    id: str
    prompt: str
    expected_tool: str


class ToolChoice(BaseModel):
    """Structured output: the single tool the model picks for a request."""

    tool_name: str


SCENARIOS: list[Scenario] = [
    {
        "id": "send-message-hello-team",
        "prompt": "Send a message saying 'hello team' to the #general channel",
        "expected_tool": "slack_send_message",
    },
    {
        "id": "read-channel-engineering",
        "prompt": "Read the last 10 messages in the #engineering channel",
        "expected_tool": "slack_read_channel",
    },
    {
        "id": "search-deployment-incident",
        "prompt": "Search public channels for messages about the deployment incident last week",
        "expected_tool": "slack_search_public",
    },
    {
        "id": "search-channels-mobile",
        "prompt": "Find which channels are about the mobile project",
        "expected_tool": "slack_search_channels",
    },
    {
        "id": "read-profile-user",
        "prompt": "Look up the profile of user U1234567890",
        "expected_tool": "slack_read_user_profile",
    },
    {
        "id": "list-members-platform-team",
        "prompt": "Who are the members of the #platform-team channel?",
        "expected_tool": "slack_list_channel_members",
    },
    {
        "id": "send-message-release-shipped",
        "prompt": "Let the team in #releases know that v2.1 shipped today",
        "expected_tool": "slack_send_message",
    },
    {
        "id": "search-api-migration",
        "prompt": "Search our public channels for what the team has discussed about the API migration",
        "expected_tool": "slack_search_public",
    },
    {
        "id": "search-channels-design-system",
        "prompt": "Which channels should I join to follow the design system work?",
        "expected_tool": "slack_search_channels",
    },
    {
        "id": "skill-slack-cli-socket-mode",
        "prompt": "Search the Slack developer documentation for how to use socket mode",
        "expected_tool": "slack-cli",
    },
    {
        "id": "skill-block-kit-modal",
        "prompt": "Build a Slack modal dialog with a dropdown menu and a date picker",
        "expected_tool": "block-kit",
    },
    {
        "id": "skill-create-app-template",
        "prompt": "Create a new Slack app project with a slash command from a template",
        "expected_tool": "create-slack-app",
    },
    {
        "id": "ambiguous-post-message-deploy",
        "prompt": "Post a message in #general announcing that the deploy just finished",
        "expected_tool": "slack_send_message",
    },
    {
        "id": "ambiguous-list-members-platform",
        "prompt": "List the members of the #platform-team channel",
        "expected_tool": "slack_list_channel_members",
    },
    {
        "id": "ambiguous-pull-history-engineering",
        "prompt": "Pull the recent message history from the #engineering channel",
        "expected_tool": "slack_read_channel",
    },
    {
        "id": "ambiguous-user-info-profile",
        "prompt": "Fetch the profile details for user U1234567890",
        "expected_tool": "slack_read_user_profile",
    },
    {
        "id": "ambiguous-add-reaction-releases",
        "prompt": "Add a :tada: reaction to the latest message in #releases",
        "expected_tool": "slack_add_reaction",
    },
    {
        "id": "ambiguous-reply-in-thread",
        "prompt": "Post a reply in the thread on the outage message in #incidents",
        "expected_tool": "slack_send_message",
    },
    {
        "id": "ambiguous-read-thread-replies",
        "prompt": "Show me all the replies in that thread in #support",
        "expected_tool": "slack_read_thread",
    },
    {
        "id": "ambiguous-lookup-user-by-email",
        "prompt": "Find the Slack user with the email jane@example.com",
        "expected_tool": "slack_search_users",
    },
    {
        "id": "ambiguous-schedule-message-standup",
        "prompt": "Schedule a message in #standup for tomorrow at 9am",
        "expected_tool": "slack_schedule_message",
    },
    {
        "id": "skill-slack-api-scopes",
        "prompt": "What OAuth scopes does the chat.postMessage method require?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-which-method-topic",
        "prompt": "Which Slack Web API method sets a channel's topic, and what scope does it need?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-pagination",
        "prompt": "How do I handle next_cursor pagination when calling conversations.list?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-missing-scope",
        "prompt": "A call to users.info is returning a missing_scope error, what scope do I need to add?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-docs-url",
        "prompt": "What arguments does https://docs.slack.dev/reference/methods/conversations.history take?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-rate-limit",
        "prompt": "I'm getting a ratelimited error with a Retry-After header on chat.update, how should I back off?",
        "expected_tool": "slack-api",
    },
    {
        "id": "skill-slack-api-call-with-curl",
        "prompt": "How do I call the conversations.history endpoint with curl?",
        "expected_tool": "slack-api",
    },
]


def build_prompt(available_tools: list[ToolCall], prompt: str) -> str:
    tools_list = "\n".join(f"- {t.name}: {t.description}" for t in available_tools)
    return f"""\
You have access to the following tools:

{tools_list}

User request: {prompt}

Pick the single best tool for this request and respond with its exact name."""


@pytest.mark.skipif(not SLACK_MCP_TOKEN, reason="SLACK_MCP_TOKEN not set")
class TestToolSelection:
    """Assert the model selects the expected tool for each scenario."""

    model: NoThinkOllamaModel
    available_tools: list[ToolCall]

    @classmethod
    def setup_class(cls):
        # Fetch tools once for the whole class: the MCP list is one network
        # round-trip, and skills are read from disk.
        cls.model = NoThinkOllamaModel(model=OLLAMA_MODEL)
        cls.available_tools = get_slack_mcp_tools() + get_all_skill_tools()

    @pytest.mark.parametrize(
        "scenario",
        SCENARIOS,
        ids=[s["id"] for s in SCENARIOS],
    )
    def test_tool_selection(self, scenario: Scenario):
        expected_name = scenario["expected_tool"]
        available_names = {t.name for t in self.available_tools}
        assert expected_name in available_names, f"Tool {expected_name} not found in available tools"

        # Ask the model which tool it would use, then score its actual pick
        # against the expected one.
        choice, _ = self.model.generate(build_prompt(self.available_tools, scenario["prompt"]), schema=ToolChoice)

        assert choice.tool_name == expected_name, (
            f"Expected {repr(expected_name)} for prompt {repr(scenario['prompt'])}, got {repr(choice.tool_name)}"
        )
