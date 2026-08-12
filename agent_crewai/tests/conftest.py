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
import sys
from unittest import mock

import pytest


@pytest.fixture
def tests_path():
    path = os.path.split(os.path.abspath(__file__))[0]
    return path


@pytest.fixture
def root_path(tests_path):
    path = os.path.split(tests_path)[0]
    return path


@pytest.fixture(autouse=True)
def custom_model_environment(root_path):
    sys.path.append(os.path.join(root_path, "custom_model"))


@pytest.fixture
def mock_agent_response(
    mock_crewai_output,
    mock_langgraph_output,
    mock_llamaindex_output,
    mock_generic_output,
):
    """
    Fixture to return a mock agent response based on the agent template framework.
    """
    # Return the agent framework
    return mock_crewai_output


@pytest.fixture
def mock_crewai_output():
    return mock.Mock(
        raw="agent result",
        token_usage=mock.Mock(
            completion_tokens=1,
            prompt_tokens=2,
            total_tokens=3,
        ),
    ), None


@pytest.fixture
def mock_langgraph_output():
    from langchain_core.messages import AIMessage

    usage = {
        "completion_tokens": 1,
        "prompt_tokens": 2,
        "total_tokens": 3,
    }
    return (
        [
            {
                "final_agent": {
                    "messages": [
                        AIMessage(content="Intermediate message"),
                        AIMessage(content="agent result"),
                    ]
                }
            },
        ],
        usage,
    )


@pytest.fixture
def mock_generic_output():
    usage = {
        "completion_tokens": 1,
        "prompt_tokens": 2,
        "total_tokens": 3,
    }

    return "agent result", usage


@pytest.fixture
def mock_llamaindex_output():
    usage = {
        "completion_tokens": 1,
        "prompt_tokens": 2,
        "total_tokens": 3,
    }
    return "agent result", usage, None
