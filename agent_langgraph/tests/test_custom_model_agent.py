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
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from agent import MyAgent
from helpers import (
    CustomModelChatResponse,
    CustomModelStreamingResponse,
    to_custom_model_chat_response,
    to_custom_model_streaming_response,
)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from ragas import MultiTurnSample


class TestMyAgentLanggraph:
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
        assert agent.api_base == "https://api.datarobot.com"  # Default value
        assert agent.model is None
        assert agent.verbose is True

        # Verify that the extra parameters don't create attributes
        with pytest.raises(AttributeError):
            _ = agent.extra_param1

    @pytest.mark.parametrize(
        "api_base,expected_result",
        [
            ("https://example.com", "https://example.com"),
            ("https://example.com/", "https://example.com/"),
            ("https://example.com/api/v2", "https://example.com/"),
            ("https://example.com/api/v2/", "https://example.com/"),
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
    @patch("agent.ChatLiteLLM")
    def test_llm_gateway_with_api_base(self, mock_llm, api_base, expected_result):
        """Test api_base_litellm property with various URL formats."""
        with patch.dict(os.environ, {}, clear=True):
            agent = MyAgent(api_base=api_base)
            _ = agent.llm
            mock_llm.assert_called_once_with(
                model="datarobot/azure/gpt-4o-mini",
                api_base=expected_result,
                api_key=None,
                timeout=90,
            )

    @pytest.mark.parametrize(
        "api_base,expected_result",
        [
            ("https://example.com", "https://example.com/api/v2/deployments/test-id/"),
            ("https://example.com/", "https://example.com/api/v2/deployments/test-id/"),
            (
                "https://example.com/api/v2/",
                "https://example.com/api/v2/deployments/test-id/",
            ),
            (
                "https://example.com/api/v2",
                "https://example.com/api/v2/deployments/test-id/",
            ),
            (
                "https://example.com/other-path",
                "https://example.com/other-path/api/v2/deployments/test-id/",
            ),
            (
                "https://custom.example.com:8080/path/to",
                "https://custom.example.com:8080/path/to/api/v2/deployments/test-id/",
            ),
            (
                "https://custom.example.com:8080/path/to/api/v2/",
                "https://custom.example.com:8080/path/to/api/v2/deployments/test-id/",
            ),
            (
                "https://example.com/api/v2/deployments/",
                "https://example.com/api/v2/deployments/",
            ),
            (
                "https://example.com/api/v2/deployments",
                "https://example.com/api/v2/deployments",
            ),
            (
                "https://example.com/api/v2/genai/llmgw/chat/completions",
                "https://example.com/api/v2/genai/llmgw/chat/completions",
            ),
            (
                "https://example.com/api/v2/genai/llmgw/chat/completions/",
                "https://example.com/api/v2/genai/llmgw/chat/completions/",
            ),
            (None, "https://api.datarobot.com/api/v2/deployments/test-id/"),
        ],
    )
    @patch("agent.ChatLiteLLM")
    def test_llm_deployment_with_api_base(self, mock_llm, api_base, expected_result):
        """Test api_base_litellm property with various URL formats."""
        with patch.dict(
            os.environ, {"LLM_DATAROBOT_DEPLOYMENT_ID": "test-id"}, clear=True
        ):
            agent = MyAgent(api_base=api_base)
            _ = agent.llm
            mock_llm.assert_called_once_with(
                model="datarobot/azure/gpt-4o-mini",
                api_base=expected_result,
                api_key=None,
                timeout=90,
            )

    @patch("agent.StateGraph")
    def test_langgraph_non_streaming(self, mock_state_graph, agent):
        def mock_stream_generator():
            yield {
                "final_agent": {
                    "messages": [
                        HumanMessage(content="Hi, tell me about Paris."),
                        AIMessage(
                            content="Here is the information you requested about Paris....."
                        ),
                    ]
                }
            }

        mock_graph_stream = Mock()
        mock_graph_stream.stream.return_value = mock_stream_generator()
        mock_state_graph.return_value = Mock(
            compile=MagicMock(return_value=mock_graph_stream)
        )

        completion_create_params = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": '{"topic": "Artificial Intelligence"}'}
            ],
            "environment_var": True,
        }

        response_text, pipeline_interactions, usage_metrics = agent.invoke(
            completion_create_params
        )
        response = to_custom_model_chat_response(
            response_text, pipeline_interactions, usage_metrics, model="test-model"
        )
        assert isinstance(response, CustomModelChatResponse)
        assert (
            response.choices[0].message.content
            == "Here is the information you requested about Paris....."
        )
        assert response.pipeline_interactions is not None
        assert response.usage.completion_tokens == 0
        assert response.usage.prompt_tokens == 0
        assert response.usage.total_tokens == 0

    @patch("agent.StateGraph")
    def test_langgraph_streaming(self, mock_state_graph, agent):
        def mock_stream_generator():
            yield {
                "first_agent": {
                    "messages": [
                        HumanMessage(content="Hi, tell me about Paris."),
                        AIMessage(
                            content="Here is the information you requested about Paris....."
                        ),
                    ]
                }
            }
            yield {
                "final_agent": {
                    "messages": [
                        HumanMessage(content="Hi, tell me about Paris."),
                        AIMessage(content="Paris is the capital city of France."),
                    ]
                }
            }

        mock_graph_stream = Mock()
        mock_graph_stream.stream.return_value = mock_stream_generator()
        mock_state_graph.return_value = Mock(
            compile=MagicMock(return_value=mock_graph_stream)
        )

        completion_create_params = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": '{"topic": "Artificial Intelligence"}'}
            ],
            "environment_var": True,
            "stream": True,
        }
        streaming_response_iterator = agent.invoke(completion_create_params)
        streaming_response = to_custom_model_streaming_response(
            streaming_response_iterator, model="test-model"
        )
        for idx, response in enumerate(streaming_response):
            assert isinstance(response, CustomModelStreamingResponse)
            if idx == 0:
                assert (
                    response.choices[0].delta.content
                    == "Here is the information you requested about Paris....."
                )
                assert response.choices[0].finish_reason is None
                assert response.pipeline_interactions is None
            elif idx == 1:
                assert (
                    response.choices[0].delta.content
                    == "Paris is the capital city of France."
                )
                assert response.choices[0].finish_reason is None
                assert response.pipeline_interactions is None
            else:
                assert response.choices[0].delta.content is None
                assert response.choices[0].finish_reason == "stop"
                assert response.pipeline_interactions is not None


@pytest.fixture
def events() -> list[dict[str, Any]]:
    return [
        {
            "final_agent": {
                "messages": [
                    HumanMessage(content="Hi, tell me about Paris."),
                    AIMessage(
                        content="",
                        additional_kwars={
                            "tool_calls": [
                                {
                                    "id": "call_9Luzq73eFGikbDUnAazwnPep",
                                    "function": {
                                        "name": "wikipedia",
                                        "arguments": '{"city": "Paris"}',
                                        "type": "function",
                                    },
                                },
                                {
                                    "id": "call_PvSdV1HLzTd6RnoiwM7lLy5u",
                                    "function": {
                                        "name": "weather",
                                        "arguments": '{"city": "Paris"}',
                                        "type": "function",
                                    },
                                },
                                {
                                    "id": "call_mknvGBUMnAY4OzUTZA9yTe4I",
                                    "function": {
                                        "name": "events",
                                        "arguments": '{"city": "Paris"}',
                                        "type": "function",
                                    },
                                },
                            ]
                        },
                    ),
                    ToolMessage(
                        content="stuff about paris",
                        tool_call_id="call_9Luzq73eFGikbDUnAazwnPep",
                    ),
                    ToolMessage(
                        content=[{"temp": 15, "wind": 2, "direction": 215}],
                        tool_call_id="call_PvSdV1HLzTd6RnoiwM7lLy5u",
                    ),
                    ToolMessage(
                        content=["a", "b", "c"],
                        tool_call_id="call_mknvGBUMnAY4OzUTZA9yTe4I",
                    ),
                    AIMessage(
                        content="Here is the information you requested about Paris....."
                    ),
                ]
            }
        }
    ]


def test_extract_pipeline_interactions(events: list[dict[str, Any]]) -> None:
    """Test that the pipeline interactions are extracted correctly."""

    result = MyAgent.create_pipeline_interactions_from_events(events)
    # The check is that with different ToolMessage content types there is no exception
    assert isinstance(result, MultiTurnSample)
    assert len(result.user_input) == 3
