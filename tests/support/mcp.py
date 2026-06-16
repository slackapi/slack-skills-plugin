"""A minimal MCP client over the Streamable HTTP transport, using only the standard library."""

import http.client
import json
import urllib.request
from typing import Any, NotRequired, TypedDict

from tests.config import MCP_PROTOCOL_VERSION

#: Identifies this client to the MCP server during the `initialize` handshake.
DEFAULT_CLIENT_INFO = {"name": "slack-developer-skills-tests", "version": "0.1.0"}


class MCPTool(TypedDict):
    """A single tool entry as returned by the MCP `tools/list` method."""

    name: str
    description: NotRequired[str]
    inputSchema: NotRequired[dict[str, Any]]


class MCPClient:
    """Talks to one MCP server over Streamable HTTP. Establishes the session lazily."""

    def __init__(
        self,
        url: str,
        token: str,
        protocol_version: str = MCP_PROTOCOL_VERSION,
        client_info: dict[str, str] | None = None,
    ) -> None:
        self._url = url
        self._token = token
        self._protocol_version = protocol_version
        self._client_info = client_info or DEFAULT_CLIENT_INFO
        self._session_id: str | None = None
        self._initialized = False
        self._id = 0

    def list_tools(self) -> list[MCPTool]:
        """Return the server's advertised tools, following `nextCursor` pagination."""
        self._ensure_initialized()
        tools: list[MCPTool] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else None
            data = self._request("tools/list", params)
            if data is None:
                raise RuntimeError("MCP server returned no response to tools/list")
            result = data["result"]
            tools.extend(result["tools"])
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def _ensure_initialized(self) -> None:
        """Run the `initialize` + `notifications/initialized` handshake once per session."""
        if self._initialized:
            return
        self._request(
            "initialize",
            {
                "protocolVersion": self._protocol_version,
                "capabilities": {},
                "clientInfo": self._client_info,
            },
        )
        self._notify("notifications/initialized")
        self._initialized = True

    def _request(self, method: str, params: dict | None = None) -> dict | None:
        """Send a JSON-RPC request (carries an id, expects a response)."""
        self._id += 1
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            message["params"] = params
        return self._post(message)

    def _notify(self, method: str, params: dict | None = None) -> None:
        """Send a JSON-RPC notification (no id, no response expected)."""
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._post(message)

    def _post(self, data: dict) -> dict | None:
        """POST one JSON-RPC message, capturing the session id from the response headers."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        req = urllib.request.Request(self._url, data=json.dumps(data).encode(), headers=headers, method="POST")

        resp: http.client.HTTPResponse
        with urllib.request.urlopen(req, timeout=30) as resp:
            if new_session := resp.headers.get("mcp-session-id"):
                self._session_id = new_session
            # Notifications (no "id") and 202 Accepted carry no body to parse.
            if "id" not in data or resp.status == 202:
                return None

            if resp.info().get_content_type().startswith("text/event-stream"):
                return self._read_sse_response(resp)

            charset = resp.info().get_content_charset("utf-8")
            return json.loads(resp.read().decode(charset))

    @staticmethod
    def _read_sse_response(resp: http.client.HTTPResponse) -> dict | None:
        """Return the first SSE event whose data is a JSON-RPC response (has result/error)."""
        charset = resp.info().get_content_charset("utf-8")
        data_lines: list[str] = []
        for raw in resp:
            # SSE line terminators may be \n, \r, or \r\n — strip all of them.
            line = raw.decode(charset).rstrip("\r\n")
            if line == "":  # event boundary
                if data_lines:
                    msg = json.loads("\n".join(data_lines))
                    if "result" in msg or "error" in msg:
                        return msg
                    data_lines = []
                continue
            if line.startswith("data:"):
                data_lines.append(line[len("data:") :].lstrip())
        return None
