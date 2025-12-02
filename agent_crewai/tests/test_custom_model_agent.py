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
import json
import os
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from agent import MyAgent
from ragas.messages import AIMessage, HumanMessage, ToolCall, ToolMessage


class TestMyAgentCrewAI:
    @pytest.fixture
    def agent(self):
        return MyAgent(api_key="test_key", api_base="test_base", verbose=True)

    def test_init_with_explicit_parameters(self):
        """Test initialization with explicitly provided parameters."""
        # Setup
        api_key = "test-api-key"
        api_base = "https://test-api-base.com"
        model = "test-model"
        verbose = True

        # Execute
        agent = MyAgent(
            api_key=api_key, api_base=api_base, model=model, verbose=verbose
        )

        # Assert
        assert agent.api_key == api_key
        assert agent.api_base == api_base
        assert agent.model == model
        assert agent.verbose is True

    @patch.dict(
        os.environ,
        {
            "DATAROBOT_API_TOKEN": "env-api-key",
            "DATAROBOT_ENDPOINT": "https://env-api-base.com",
        },
    )
    def test_init_with_environment_variables(self):
        """Test initialization using environment variables when no explicit parameters."""
        # Execute
        agent = MyAgent()

        # Assert
        assert agent.api_key == "env-api-key"
        assert agent.api_base == "https://env-api-base.com"
        assert agent.model is None
        assert agent.verbose is True

    @patch.dict(
        os.environ,
        {
            "DATAROBOT_API_TOKEN": "env-api-key",
            "DATAROBOT_ENDPOINT": "https://env-api-base.com",
        },
    )
    def test_init_explicit_params_override_env_vars(self):
        """Test explicit parameters override environment variables."""
        # Setup
        api_key = "explicit-api-key"
        api_base = "https://explicit-api-base.com"

        # Execute
        agent = MyAgent(api_key=api_key, api_base=api_base)

        # Assert
        assert agent.api_key == "explicit-api-key"
        assert agent.api_base == "https://explicit-api-base.com"

    def test_init_with_string_verbose_true(self):
        """Test initialization with string 'true' for verbose parameter."""
        # Setup
        verbose_values = ["true", "TRUE", "True"]

        for verbose in verbose_values:
            # Execute
            agent = MyAgent(verbose=verbose)

            # Assert
            assert agent.verbose is True

    def test_init_with_string_verbose_false(self):
        """Test initialization with string 'false' for verbose parameter."""
        # Setup
        verbose_values = ["false", "FALSE", "False"]

        for verbose in verbose_values:
            # Execute
            agent = MyAgent(verbose=verbose)

            # Assert
            assert agent.verbose is False

    def test_init_with_boolean_verbose(self):
        """Test initialization with boolean values for verbose parameter."""
        # Test with True
        agent = MyAgent(verbose=True)
        assert agent.verbose is True

        # Test with False
        agent = MyAgent(verbose=False)
        assert agent.verbose is False

    @patch.dict(os.environ, {}, clear=True)
    def test_init_with_additional_kwargs(self):
        """Test initialization with additional keyword arguments."""
        # Setup
        additional_kwargs = {"extra_param1": "value1", "extra_param2": 42}

        # Execute
        agent = MyAgent(**additional_kwargs)

        # Assert - Additional kwargs should be accepted but not stored as attributes
        assert agent.api_key is None  # Should fallback to env var or None
        assert agent.api_base is None  # Should fallback to env var or None
        assert agent.model is None
        assert agent.verbose is True

        # Verify that the extra parameters don't create attributes
        with pytest.raises(AttributeError):
            _ = agent.extra_param1

    @pytest.mark.parametrize(
        "api_base,expected_result",
        [
            ("https://example.com/api/v2/", "https://example.com/"),
            ("https://example.com/api/v2", "https://example.com/"),
            ("https://example.com/other-path", "https://example.com/other-path"),
            (
                "https://custom.example.com:8080/path/to/api/v2/",
                "https://custom.example.com:8080/path/to/",
            ),
            (
                "https://example.com/api/v2/deployment/",
                "https://example.com/api/v2/deployment/",
            ),
            (
                "https://example.com/api/v2/deployment",
                "https://example.com/api/v2/deployment",
            ),
            (
                "https://example.com/api/v2/genai/llmgw/chat/completions",
                "https://example.com/api/v2/genai/llmgw/chat/completions",
            ),
            (
                "https://example.com/api/v2/genai/llmgw/chat/completions/",
                "https://example.com/api/v2/genai/llmgw/chat/completions/",
            ),
            (None, "https://api.datarobot.com"),
        ],
    )
    def test_api_base_litellm_variations(self, api_base, expected_result):
        """Test api_base_litellm property with various URL formats."""
        with patch.dict(os.environ, {}, clear=True):
            agent = MyAgent(api_base=api_base)
            result = agent.api_base_litellm
            assert result == expected_result

    @patch("agent.LLM")
    def test_llm_property(self, mock_llm, agent):
        # Test that LLM is created with correct parameters
        agent.llm_with_datarobot_llm_gateway
        mock_llm.assert_called_once_with(
            model="datarobot/azure/gpt-4o-mini",
            api_base="test_base",
            api_key="test_key",
            timeout=90,
        )

    @patch("agent.LLM")
    def test_llm_property_with_no_api_base(self, mock_llm, agent):
        # Test that LLM is created with correct parameters
        with patch.dict(os.environ, {}, clear=True):
            agent = MyAgent(api_key="test_key", verbose=True)
            agent.llm_with_datarobot_llm_gateway
            mock_llm.assert_called_once_with(
                model="datarobot/azure/gpt-4o-mini",
                api_base="https://api.datarobot.com",
                api_key="test_key",
                timeout=90,
            )

    @patch("agent.Agent")
    def test_agent_planner_property(self, mock_agent, agent):
        # Mock the llm property
        mock_llm = Mock()
        with patch.object(
            MyAgent, "llm_with_datarobot_llm_gateway", return_value=mock_llm
        ):
            agent.agent_planner
            mock_agent.assert_called_once_with(
                role="Content Planner",
                goal=ANY,
                backstory=ANY,
                allow_delegation=False,
                verbose=True,
                llm=ANY,
            )

    @patch("agent.Agent")
    def test_agent_writer_property(self, mock_agent, agent):
        # Mock the llm property
        mock_llm = Mock()
        with patch.object(
            MyAgent, "llm_with_datarobot_llm_gateway", return_value=mock_llm
        ):
            agent.agent_writer
            mock_agent.assert_called_once_with(
                role="Content Writer",
                goal=ANY,
                backstory=ANY,
                allow_delegation=False,
                verbose=True,
                llm=ANY,
            )

    @patch("agent.Agent")
    def test_agent_editor_property(self, mock_agent, agent):
        # Mock the llm property
        mock_llm = Mock()
        with patch.object(
            MyAgent, "llm_with_datarobot_llm_gateway", return_value=mock_llm
        ):
            agent.agent_editor
            mock_agent.assert_called_once_with(
                role="Editor",
                goal=ANY,
                backstory=ANY,
                allow_delegation=False,
                verbose=True,
                llm=ANY,
            )

    @patch("agent.Task")
    def test_task_plan_property(self, mock_task, agent):
        # Mock the agent_planner property
        mock_planner = Mock()
        with patch.object(MyAgent, "agent_planner", return_value=mock_planner):
            agent.task_plan
            mock_task.assert_called_once_with(
                description=ANY,
                expected_output=ANY,
                agent=ANY,
            )

    @patch("agent.Task")
    def test_task_write_property(self, mock_task, agent):
        # Mock the agent_planner property
        mock_planner = Mock()
        with patch.object(MyAgent, "agent_writer", return_value=mock_planner):
            agent.task_write
            mock_task.assert_called_once_with(
                description=ANY,
                expected_output=ANY,
                agent=ANY,
            )

    @patch("agent.Task")
    def test_task_edit_property(self, mock_task, agent):
        # Mock the agent_planner property
        mock_planner = Mock()
        with patch.object(MyAgent, "agent_editor", return_value=mock_planner):
            agent.task_edit
            mock_task.assert_called_once_with(
                description=ANY,
                expected_output=ANY,
                agent=ANY,
            )

    def test_run_method(self, agent):
        # Create a mock result with a raw attribute
        mock_result = Mock()
        mock_result.raw = "success"
        mock_result.token_usage = Mock(
            completion_tokens=10,
            prompt_tokens=5,
            total_tokens=15,
        )

        # Create a mock crew with a kickoff method that returns the mock result
        mock_crew = Mock()
        mock_crew.kickoff.return_value = mock_result

        # Patch the crew method to return our mock
        with patch.object(MyAgent, "crew", return_value=mock_crew):
            # Call the run method with test inputs
            completion_create_params = {
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": '{"topic": "Artificial Intelligence"}'}
                ],
                "environment_var": True,
            }
            crew_output, events = agent.run(completion_create_params)

            # Verify crew() was called
            agent.crew.assert_called_once()

            # Verify kickoff was called with the right inputs
            mock_crew.kickoff.assert_called_once_with(
                inputs={"topic": "Artificial Intelligence"}
            )

            assert crew_output == mock_result
            assert not events

    @patch("custom.MyAgent")
    def test_chat(self, mock_agent):
        # This test case covers pipeline interactions in the response.  Test with
        # no pipeline interactions is already part of test_custom_model.py::test_chat
        from custom import chat

        crew_output = Mock(
            raw="agent result",
            token_usage=Mock(
                completion_tokens=1,
                prompt_tokens=2,
                total_tokens=3,
            ),
        )
        events = [
            HumanMessage(content="Hi"),
            AIMessage(
                content="Which language should I use?",
                tool_calls=[
                    ToolCall(name="find_language", args={"input_language": "en"})
                ],
            ),
            ToolMessage(content="Use en"),
            AIMessage(content="How are you today?"),
        ]

        # Setup mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = (crew_output, events)
        mock_agent.return_value = mock_agent_instance

        completion_create_params = {
            "model": "test-model",
            "messages": [{"role": "user", "content": '{"topic": "test"}'}],
            "environment_var": True,
        }

        response = chat(completion_create_params, model="test-model")

        # Assert results - check the pipeline_interactions - other sections of the
        # results are already being checked in test_custom_model.py::test_chat
        completion = json.loads(response.json())
        actual_events = json.loads(completion["pipeline_interactions"])["user_input"]
        for expected_message, actual_message in zip(events, actual_events):
            assert expected_message.content == actual_message["content"]
            assert expected_message.type == actual_message["type"]
