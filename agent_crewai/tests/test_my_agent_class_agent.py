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
from unittest.mock import ANY, Mock, patch

import pytest

from custom_model.my_agent_class.agent import MyAgent


class TestMyAgentCrewAI:
    @pytest.fixture
    def agent(self):
        return MyAgent(api_key="test_key", api_base="test_base", verbose=True)

    def test_init_with_string_verbose_true(self):
        # Test initialization with verbose as string "true"
        agent = MyAgent(api_key="test_key", api_base="test_base", verbose="true")
        assert agent.api_key == "test_key"
        assert agent.api_base == "test_base"
        assert agent.verbose is True

    def test_init_with_string_verbose_false(self):
        # Test initialization with verbose as string "false"
        agent = MyAgent(api_key="test_key", api_base="test_base", verbose="false")
        assert agent.api_key == "test_key"
        assert agent.api_base == "test_base"
        assert agent.verbose is False

    def test_init_with_bool_verbose(self):
        # Test initialization with verbose as boolean
        agent = MyAgent(api_key="test_key", api_base="test_base", verbose=True)
        assert agent.api_key == "test_key"
        assert agent.api_base == "test_base"
        assert agent.verbose is True

    def test_init_with_extra_kwargs(self):
        # Test initialization with extra kwargs
        agent = MyAgent(
            api_key="test_key",
            api_base="test_base",
            verbose=True,
            extra_param="extra_value",
        )
        assert agent.api_key == "test_key"
        assert agent.api_base == "test_base"
        assert agent.verbose is True

    @patch("custom_model.my_agent_class.agent.LLM")
    def test_llm_property(self, mock_llm, agent):
        # Test that LLM is created with correct parameters
        agent.llm_with_datarobot_llm_gateway
        mock_llm.assert_called_once_with(
            model="datarobot/azure/gpt-4",
            clientId="custom-model",
            api_base="test_base",
            api_key="test_key",
        )

    @patch("custom_model.my_agent_class.agent.Agent")
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

    @patch("custom_model.my_agent_class.agent.Agent")
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

    @patch("custom_model.my_agent_class.agent.Agent")
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

    @patch("custom_model.my_agent_class.agent.Task")
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

    @patch("custom_model.my_agent_class.agent.Task")
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

    @patch("custom_model.my_agent_class.agent.Task")
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

            # Verify the returned result
            assert result == (
                "success",
                {"completion_tokens": 10, "prompt_tokens": 5, "total_tokens": 15},
            )
