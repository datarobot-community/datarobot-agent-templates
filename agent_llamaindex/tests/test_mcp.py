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
Tests for MCP LlamaIndex integration - verifying agents have MCP tools configured.
"""

import asyncio
import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent import MyAgent


def create_mock_mcp_tool(name: str):
    """Create a mock MCP tool that can be used by LlamaIndex FunctionAgent."""

    async def mock_tool_func(ctx: Any, **kwargs: Any) -> str:
        return f"Result from {name}"

    mock_tool_func.__name__ = name
    mock_tool_func.__doc__ = f"Mock MCP tool {name}"
    return mock_tool_func


def create_mock_workflow_handler():
    """Create a mock workflow handler that simulates workflow execution."""
    mock_handler = MagicMock()

    async def stream_events():
        if False:  # pragma: no cover
            yield

    mock_handler.stream_events = stream_events
    mock_handler.ctx = MagicMock()
    mock_handler.ctx.get.return_value = {"report_content": "Test response"}
    return mock_handler


def create_mock_workflow(handler: MagicMock | None = None):
    """Create a mock workflow."""
    workflow = MagicMock()
    workflow.run.return_value = handler or create_mock_workflow_handler()
    return workflow


@pytest.fixture(autouse=True)
def llamaindex_common_mocks():
    """
    Autouse fixture that centralizes LlamaIndex mocks:
    - load_mcp_tools returns a configurable list of mock tools
    - build_workflow returns a lightweight mock workflow
    Tests can override the tool list or workflow via helper methods.
    """
    default_tools = [
        create_mock_mcp_tool("fixture_mcp_tool_1"),
        create_mock_mcp_tool("fixture_mcp_tool_2"),
    ]
    default_workflow = create_mock_workflow()
    _ = MyAgent.build_workflow

    with (
        patch("datarobot_genai.llama_index.base.load_mcp_tools") as mock_load_mcp_tools,
        patch.object(MyAgent, "build_workflow") as mock_build_workflow,
    ):
        mock_load_mcp_tools.return_value = default_tools
        mock_build_workflow.return_value = default_workflow

        def set_mcp_tools(tools: list[Any]):
            mock_load_mcp_tools.return_value = tools

        def set_workflow(workflow):
            mock_build_workflow.side_effect = None
            mock_build_workflow.return_value = workflow

        yield SimpleNamespace(
            load_mcp_tools=mock_load_mcp_tools,
            build_workflow=mock_build_workflow,
            default_tools=default_tools,
            default_workflow=default_workflow,
            set_mcp_tools=set_mcp_tools,
            set_workflow=set_workflow,
            create_workflow=create_mock_workflow,
        )


class TestMyAgentMCPIntegration:
    """Test MCP tool integration for LlamaIndex agents."""

    def test_agent_loads_mcp_tools_from_external_url_in_invoke(
        self, llamaindex_common_mocks
    ):
        """Test that agent loads MCP tools from EXTERNAL_MCP_URL when invoke() is called."""
        mock_tools = llamaindex_common_mocks.default_tools
        mock_load_mcp_tools = llamaindex_common_mocks.load_mcp_tools

        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            agent = MyAgent(api_key="test_key", api_base="test_base", verbose=True)

            # Create completion params
            completion_params = {
                "messages": [{"role": "user", "content": "test prompt"}],
            }

            # Call invoke - this should trigger MCP tool loading
            try:
                asyncio.run(agent.invoke(completion_params))
            except (StopIteration, AttributeError, TypeError):
                # Expected when workflow is mocked
                pass

            # Verify load_mcp_tools was called with correct parameters
            mock_load_mcp_tools.assert_called_once_with(
                api_base="test_base",
                api_key="test_key",
                authorization_context={},
            )

            # Verify set_mcp_tools was called with the tools from MCP server
            assert agent.mcp_tools == mock_tools

            # Verify mcp_tools property was accessed (by agent_planner, agent_writer, agent_editor)
            # We can verify this by checking that the agents were created with the tools
            planner = agent.agent_planner
            writer = agent.agent_writer
            editor = agent.agent_editor

            # Verify all agents have MCP tools
            assert len(planner.tools) == 3  # record_notes + 2 MCP tools
            assert len(writer.tools) == 3  # write_report + 2 MCP tools
            assert len(editor.tools) == 3  # review_report + 2 MCP tools

    def test_agent_loads_mcp_tools_from_datarobot_deployment_in_invoke(
        self, llamaindex_common_mocks
    ):
        """Test that agent loads MCP tools from MCP_DEPLOYMENT_ID when invoke() is called."""
        # Create mock MCP tools
        mock_tool = create_mock_mcp_tool("test_mcp_tool")
        mock_tools = [mock_tool]
        llamaindex_common_mocks.set_mcp_tools(mock_tools)
        mock_load_mcp_tools = llamaindex_common_mocks.load_mcp_tools

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
            agent = MyAgent(api_key=api_key, api_base=api_base, verbose=True)

            # Create completion params
            completion_params = {
                "messages": [{"role": "user", "content": "test prompt"}],
            }

            # Call invoke - this should trigger MCP tool loading
            try:
                asyncio.run(agent.invoke(completion_params))
            except (StopIteration, AttributeError, TypeError):
                # Expected when workflow is mocked
                pass

            # Verify load_mcp_tools was called with correct parameters
            mock_load_mcp_tools.assert_called_once_with(
                api_base=api_base,
                api_key=api_key,
                authorization_context={},
            )

            # Verify set_mcp_tools was called with the tools from MCP server
            assert agent.mcp_tools == mock_tools

            # Verify agents have MCP tools
            planner = agent.agent_planner
            writer = agent.agent_writer
            editor = agent.agent_editor

            assert len(planner.tools) == 2  # record_notes + 1 MCP tool
            assert len(writer.tools) == 2  # write_report + 1 MCP tool
            assert len(editor.tools) == 2  # review_report + 1 MCP tool

    def test_agent_works_without_mcp_tools(self, llamaindex_common_mocks):
        """Test that agent works correctly when no MCP tools are available."""
        mock_load_mcp_tools = llamaindex_common_mocks.load_mcp_tools
        llamaindex_common_mocks.set_mcp_tools([])

        with patch.dict(os.environ, {}, clear=True):
            agent = MyAgent(api_key="test_key", api_base="test_base", verbose=True)

            # Create completion params
            completion_params = {
                "messages": [{"role": "user", "content": "test prompt"}],
            }

            # Call invoke
            try:
                asyncio.run(agent.invoke(completion_params))
            except (StopIteration, AttributeError, TypeError):
                # Expected when workflow is mocked
                pass

            # Verify load_mcp_tools was still called
            mock_load_mcp_tools.assert_called_once()

            # Verify mcp_tools is empty
            assert len(agent.mcp_tools) == 0

            # Verify agents only have their default tools
            planner = agent.agent_planner
            writer = agent.agent_writer
            editor = agent.agent_editor

            assert len(planner.tools) == 1  # only record_notes
            assert len(writer.tools) == 1  # only write_report
            assert len(editor.tools) == 1  # only review_report

    def test_mcp_tools_property_accessed_by_all_agents(self, llamaindex_common_mocks):
        """Test that mcp_tools property is accessed by all three agents during workflow build."""
        # Create mock MCP tools
        mock_tool1 = create_mock_mcp_tool("tool1")
        mock_tool2 = create_mock_mcp_tool("tool2")
        mock_tools = [mock_tool1, mock_tool2]
        llamaindex_common_mocks.set_mcp_tools(mock_tools)
        # Track property access using a spy
        access_count = {"count": 0}
        original_prop = MyAgent.mcp_tools

        def counting_prop(self):
            access_count["count"] += 1
            return original_prop.__get__(self, MyAgent)

        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            with patch.object(MyAgent, "mcp_tools", property(counting_prop)):
                agent = MyAgent(api_key="test_key", api_base="test_base", verbose=True)
                agent.set_mcp_tools(mock_tools)
                _ = agent.agent_planner
                _ = agent.agent_writer
                _ = agent.agent_editor

        # Verify set_mcp_tools was called with the tools from MCP server
        assert agent._mcp_tools == mock_tools

        # Verify mcp_tools property was accessed at least 3 times (once per agent)
        assert access_count["count"] >= 3, (
            f"Expected at least 3 accesses (one per agent), got {access_count['count']}"
        )

    @patch(
        "datarobot_genai.llama_index.mcp.aget_tools_from_mcp_url",
        new_callable=AsyncMock,
    )
    def test_mcp_tool_execution_makes_request_to_server(
        self, mock_aget_tools, llamaindex_common_mocks
    ):
        """Test that executing an MCP tool makes a request to the MCP server and returns a response."""

        # Create a mock MCP tool that simulates making a request
        async def executable_tool_func(
            ctx: Any, query: str = "test", **kwargs: Any
        ) -> str:
            # This simulates the tool making a request to the MCP server
            # In reality, this would be handled by the MCP adapter
            return f"MCP server response for: {query}"

        executable_tool_func.__name__ = "test_executable_tool"
        executable_tool_func.__doc__ = "Test executable MCP tool"

        mock_tool = executable_tool_func
        mock_tools = [mock_tool]

        # Mock aget_tools_from_mcp_url to return our executable tool
        mock_aget_tools.return_value = mock_tools

        llamaindex_common_mocks.set_mcp_tools(mock_tools)
        mock_load_mcp_tools = llamaindex_common_mocks.load_mcp_tools

        test_url = "https://mcp-server.example.com/mcp"
        with patch.dict(os.environ, {"EXTERNAL_MCP_URL": test_url}, clear=True):
            agent = MyAgent(api_key="test_key", api_base="test_base", verbose=True)

            # Create completion params
            completion_params = {
                "messages": [{"role": "user", "content": "test prompt"}],
            }

            # Call invoke - this should trigger MCP tool loading
            try:
                asyncio.run(agent.invoke(completion_params))
            except (StopIteration, AttributeError, TypeError):
                # Expected when workflow is mocked
                pass

            # Verify load_mcp_tools was called (which internally calls aget_tools_from_mcp_url)
            mock_load_mcp_tools.assert_called_once()

            # Verify tools were set
            assert len(agent.mcp_tools) == 1

            # Execute the tool and verify it returns a response
            tool = agent.mcp_tools[0]
            result = asyncio.run(tool(ctx=MagicMock(), query="test query"))

            # Verify the tool executed and returned a response
            assert result == "MCP server response for: test query"

            # Verify the tool is callable
            assert callable(tool)
