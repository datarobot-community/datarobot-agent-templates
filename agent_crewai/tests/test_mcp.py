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

import os
from unittest.mock import MagicMock, patch

from custom_model.mcp_client import MCPConfig, mcp_tools_context


class TestMCPConfig:
    """Test MCP configuration management."""

    def test_mcp_config_without_configuration(self):
        """Test MCP config when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            config = MCPConfig()
            assert config.external_mcp_url is None
            assert config.mcp_deployment_id is None
            assert config.server_config is None

    def test_mcp_config_with_external_url(self):
        """Test MCP config with external URL."""
        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            config = MCPConfig()
            assert config.external_mcp_url == test_url
            assert config.server_config is not None
            assert config.server_config["url"] == test_url
            assert config.server_config["transport"] == "streamable-http"
            assert "headers" not in config.server_config

    def test_mcp_config_with_datarobot_deployment_id(self):
        """Test MCP config with DataRobot deployment ID."""
        deployment_id = "abc123def456789012345678"
        api_base = "https://app.datarobot.com/api/v2"
        api_key = "test-api-key"

        with patch.dict(
            os.environ,
            {
                "MCP_DEPLOYMENT_ID": deployment_id,
                "DATAROBOT_ENDPOINT": api_base,
                "DATAROBOT_API_TOKEN": api_key,
            },
            clear=True,
        ):
            config = MCPConfig()
            assert config.mcp_deployment_id == deployment_id
            assert config.server_config is not None
            assert (
                config.server_config["url"]
                == f"{api_base}/deployments/{deployment_id}/directAccess/mcp"
            )
            assert config.server_config["transport"] == "streamable-http"
            assert (
                config.server_config["headers"]["Authorization"] == f"Bearer {api_key}"
            )

    def test_mcp_config_with_datarobot_deployment_id_and_bearer_token(self):
        """Test MCP config with DataRobot deployment ID and Bearer token already formatted."""
        deployment_id = "abc123def456789012345678"
        api_base = "https://app.datarobot.com/api/v2"
        api_key = "Bearer test-api-key"

        with patch.dict(
            os.environ,
            {
                "MCP_DEPLOYMENT_ID": deployment_id,
                "DATAROBOT_ENDPOINT": api_base,
                "DATAROBOT_API_TOKEN": api_key,
            },
            clear=True,
        ):
            config = MCPConfig()
            assert config.server_config["headers"]["Authorization"] == api_key

    def test_mcp_config_with_datarobot_deployment_id_no_api_key(self):
        """Test MCP config with DataRobot deployment ID but no API key."""
        deployment_id = "abc123def456789012345678"

        with patch.dict(os.environ, {"MCP_DEPLOYMENT_ID": deployment_id}, clear=True):
            config = MCPConfig()
            assert config.server_config is None

    def test_mcp_config_with_datarobot_deployment_id_no_deployment_id(self):
        """Test MCP config with API key but no deployment ID."""
        api_key = "test-api-key"

        with patch.dict(os.environ, {"DATAROBOT_API_TOKEN": api_key}, clear=True):
            config = MCPConfig()
            assert config.server_config is None

    def test_mcp_config_url_construction_with_trailing_slash(self):
        """Test URL construction when api_base has trailing slash."""
        deployment_id = "abc123def456789012345678"
        api_base = "https://app.datarobot.com/api/v2/"
        api_key = "test-api-key"

        with patch.dict(
            os.environ,
            {
                "MCP_DEPLOYMENT_ID": deployment_id,
                "DATAROBOT_ENDPOINT": api_base,
                "DATAROBOT_API_TOKEN": api_key,
            },
            clear=True,
        ):
            config = MCPConfig()
            expected_url = "https://app.datarobot.com/api/v2/deployments/abc123def456789012345678/directAccess/mcp"
            assert config.server_config["url"] == expected_url

    def test_mcp_config_priority_external_over_deployment(self):
        """Test that EXTERNAL_MCP_URL takes priority over MCP_DEPLOYMENT_ID."""
        external_url = "https://external-mcp.com/mcp"
        deployment_id = "abc123def456789012345678"
        api_key = "test-api-key"

        with patch.dict(
            os.environ,
            {
                "EXTERNAL_MCP_URL": external_url,
                "MCP_DEPLOYMENT_ID": deployment_id,
                "DATAROBOT_API_TOKEN": api_key,
            },
            clear=True,
        ):
            config = MCPConfig()
            assert config.server_config["url"] == external_url
            assert "headers" not in config.server_config


class TestMCPToolsContext:
    """Test MCP tools context manager."""

    def test_mcp_tools_context_no_configuration(self):
        """Test context manager when no MCP server is configured."""
        with patch.dict(os.environ, {}, clear=True):
            with mcp_tools_context() as tools:
                assert tools == []

    @patch("custom_model.mcp_client.MCPServerAdapter")
    def test_mcp_tools_context_with_external_url(self, mock_adapter):
        """Test context manager with external MCP URL."""
        mock_tools = [MagicMock(), MagicMock()]
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.__enter__.return_value = mock_tools
        mock_adapter_instance.__exit__.return_value = None
        mock_adapter.return_value = mock_adapter_instance

        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            with mcp_tools_context() as tools:
                assert tools == mock_tools
                mock_adapter.assert_called_once()
                # Check that the server config was passed correctly
                call_args = mock_adapter.call_args[0][0]
                assert call_args["url"] == test_url
                assert call_args["transport"] == "streamable-http"

    @patch("custom_model.mcp_client.MCPServerAdapter")
    def test_mcp_tools_context_with_datarobot_deployment(self, mock_adapter):
        """Test context manager with DataRobot deployment ID."""
        mock_tools = [MagicMock()]
        mock_adapter_instance = MagicMock()
        mock_adapter_instance.__enter__.return_value = mock_tools
        mock_adapter_instance.__exit__.return_value = None
        mock_adapter.return_value = mock_adapter_instance

        deployment_id = "abc123def456789012345678"
        api_base = "https://app.datarobot.com/api/v2"
        api_key = "test-api-key"

        with patch.dict(
            os.environ,
            {
                "MCP_DEPLOYMENT_ID": deployment_id,
                "DATAROBOT_ENDPOINT": api_base,
                "DATAROBOT_API_TOKEN": api_key,
            },
            clear=True,
        ):
            with mcp_tools_context() as tools:
                assert tools == mock_tools
                mock_adapter.assert_called_once()
                # Check that the server config was passed correctly
                call_args = mock_adapter.call_args[0][0]
                expected_url = (
                    f"{api_base}/deployments/{deployment_id}/directAccess/mcp"
                )
                assert call_args["url"] == expected_url
                assert call_args["transport"] == "streamable-http"
                assert call_args["headers"]["Authorization"] == f"Bearer {api_key}"

    @patch("custom_model.mcp_client.MCPServerAdapter")
    def test_mcp_tools_context_connection_error(self, mock_adapter):
        """Test context manager handles connection errors gracefully."""
        mock_adapter.side_effect = Exception("Connection failed")

        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            with mcp_tools_context() as tools:
                assert tools == []

    def test_mcp_tools_context_with_parameters(self):
        """Test context manager with explicit api_base and api_key parameters."""
        deployment_id = "abc123def456789012345678"

        with patch.dict(os.environ, {"MCP_DEPLOYMENT_ID": deployment_id}, clear=True):
            with mcp_tools_context(
                api_base="https://custom.datarobot.com/api/v2", api_key="custom-key"
            ):
                # Should use the provided parameters instead of environment variables
                pass  # The test passes if no exception is raised
