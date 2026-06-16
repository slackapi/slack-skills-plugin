"""Expose plugin skills and Slack MCP tools as comparable `ToolCall` objects."""

from deepeval.test_case import ToolCall

from tests.config import SLACK_MCP_TOKEN, SLACK_MCP_URL
from tests.skill import discover_skills
from tests.support.mcp import MCPClient

__all__ = ["get_all_skill_tools", "get_slack_mcp_tools"]


def get_all_skill_tools() -> list[ToolCall]:
    """Convert every discovered plugin skill into a `ToolCall`."""
    return [ToolCall(name=skill.metadata.name, description=skill.metadata.description) for skill in discover_skills()]


def get_slack_mcp_tools() -> list[ToolCall]:
    """Fetch the Slack MCP server's tools and adapt them into `ToolCall` objects."""
    tools = MCPClient(url=SLACK_MCP_URL, token=SLACK_MCP_TOKEN).list_tools()
    return [ToolCall(name=tool["name"], description=tool.get("description") or "") for tool in tools]
