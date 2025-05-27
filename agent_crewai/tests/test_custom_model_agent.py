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
from unittest.mock import ANY, Mock, patch

import pytest

from custom_model.agent import MyAgent


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

    @patch("custom_model.agent.LLM")
    def test_llm_property(self, mock_llm, agent):
        # Test that LLM is created with correct parameters
        agent.llm_with_datarobot_llm_gateway
        mock_llm.assert_called_once_with(
            model="datarobot/vertex_ai/gemini-1.5-flash-002",
            clientId="custom-model",
            api_base="test_base",
            api_key="test_key",
        )

    @patch("custom_model.agent.Agent")
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

    @patch("custom_model.agent.Agent")
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

    @patch("custom_model.agent.Agent")
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

    @patch("custom_model.agent.Task")
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

    @patch("custom_model.agent.Task")
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

    @patch("custom_model.agent.Task")
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
            inputs = {"topic": "Artificial Intelligence"}
            result = agent.run(inputs)

            # Verify crew() was called
            agent.crew.assert_called_once()

            # Verify kickoff was called with the right inputs
            mock_crew.kickoff.assert_called_once_with(inputs=inputs)

            assert result == mock_result
