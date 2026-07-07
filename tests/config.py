import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (if present) before reading the environment
load_dotenv(Path(__file__).parent.parent / ".env")

# Filesystem
SKILLS_ROOT = Path(__file__).parent.parent / "skills"

# Plugin namespace (single source of truth: the plugin manifest)
PLUGIN_MANIFEST = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
PLUGIN_NAME = json.loads(PLUGIN_MANIFEST.read_text())["name"]

# Skill inventory (single source of truth)
EXPECTED_SKILLS = ("create-slack-app", "block-kit", "slack-api", "slack-cli")

# Gemini judge model
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")

# Slack MCP server
SLACK_MCP_URL = "https://mcp.slack.com/mcp"
SLACK_MCP_TOKEN = os.environ.get("SLACK_MCP_TOKEN", "")
