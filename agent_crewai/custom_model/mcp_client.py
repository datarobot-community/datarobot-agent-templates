# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
MCP integration for CrewAI using MCPServerAdapter.

This module provides MCP server connection management for CrewAI agents.
"""

import os
from contextlib import contextmanager
from typing import Any, Generator, List

from crewai_tools import MCPServerAdapter


class MCPConfig:
    """Configuration for MCP server connection."""

    def __init__(self, api_base: str | None = None, api_key: str | None = None) -> None:
        """Initialize MCP configuration from environment variables and runtime parameters."""
        self.external_mcp_url = os.environ.get("EXTERNAL_MCP_URL")
        self.mcp_deployment_id = os.environ.get("MCP_DEPLOYMENT_ID")
        self.api_base = api_base or os.environ.get(
            "DATAROBOT_ENDPOINT", "https://app.datarobot.com"
        )
        self.api_key = api_key or os.environ.get("DATAROBOT_API_TOKEN")
        self.server_config = self._get_server_config()

    def _get_server_config(self) -> dict[str, Any] | None:
        """
        Get MCP server configuration.

        Returns:
            Server configuration dict with url, transport, and optional headers, or None if not configured.
        """
        if self.external_mcp_url:
            # External MCP URL - no authentication needed
            return {"url": self.external_mcp_url, "transport": "streamable-http"}
        elif self.mcp_deployment_id and self.api_key:
            # DataRobot deployment ID - requires authentication
            # DATAROBOT_ENDPOINT already includes /api/v2, so just add the deployment path
            base_url = self.api_base.rstrip("/")
            url = f"{base_url}/deployments/{self.mcp_deployment_id}/directAccess/mcp"

            auth_header = (
                self.api_key
                if self.api_key.startswith("Bearer ")
                else f"Bearer {self.api_key}"
            )

            return {
                "url": url,
                "transport": "streamable-http",
                "headers": {"Authorization": auth_header},
            }

        return None


@contextmanager
def mcp_tools_context(
    api_base: str | None = None, api_key: str | None = None
) -> Generator[List[Any], None, None]:
    """Context manager for MCP tools that handles connection lifecycle."""
    config = MCPConfig(api_base=api_base, api_key=api_key)

    # If no MCP server configured, return empty tools list
    if not config.server_config:
        print("No MCP server configured, using empty tools list", flush=True)
        yield []
        return

    print(f"Connecting to MCP server: {config.server_config['url']}", flush=True)

    try:
        # Use MCPServerAdapter as context manager with the server config
        with MCPServerAdapter(config.server_config) as tools:
            print(
                f"Successfully connected to MCP server, got {len(tools)} tools",
                flush=True,
            )
            yield tools

    except Exception as e:
        print(
            f"Warning: Failed to connect to MCP server {config.server_config['url']}: {e}",
            flush=True,
        )
        yield []
