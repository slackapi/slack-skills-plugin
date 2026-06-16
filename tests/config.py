import os
from pathlib import Path

# Filesystem
SKILLS_ROOT = Path(__file__).parent.parent / "skills"

# Skill inventory (single source of truth)
EXPECTED_SKILLS = ("create-slack-app", "block-kit", "slack-api", "slack-cli")

# Ollama judge model
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL_NAME", "gemma4")

# Slack MCP server
SLACK_MCP_URL = "https://mcp.slack.com/mcp"
SLACK_MCP_TOKEN = os.environ.get("SLACK_MCP_TOKEN", "")
MCP_PROTOCOL_VERSION = "2025-06-18"
