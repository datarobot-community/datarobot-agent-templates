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
def mock_agent_response():
    """
    Fixture to return a mock agent response based on the agent template framework.
    """
    return (
        "agent result",
        [],
        {
            "completion_tokens": 1,
            "prompt_tokens": 2,
            "total_tokens": 3,
        },
    )
