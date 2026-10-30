---
"slack": patch
---

Request the Slack MCP server's full scope set in Claude Code, including `files:write`, so the file upload tools (`slack_get_file_upload_url` and `slack_complete_file_upload`) are available. Claude Code doesn't request a server's advertised scopes unless `oauth.scopes` is set, so until now the plugin's token never had `files:write`. Reconnect the Slack server in `/mcp` after updating to pick up the new scopes.
