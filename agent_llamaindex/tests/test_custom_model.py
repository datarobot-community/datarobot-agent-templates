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
from unittest.mock import ANY, MagicMock, patch


class TestCustomModel:
    def test_load_model(self):
        from custom import load_model

        result = load_model("")
        assert result == "success"

    @patch("custom.MyAgent")
    @patch.dict(os.environ, {"LLM_DATAROBOT_DEPLOYMENT_ID": "TEST_VALUE"}, clear=True)
    def test_chat(self, mock_agent, mock_agent_response):
        from custom import chat

        # Setup mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.invoke.return_value = mock_agent_response
        mock_agent.return_value = mock_agent_instance

        completion_create_params = {
            "model": "test-model",
            "messages": [{"role": "user", "content": '{"topic": "test"}'}],
            "environment_var": True,
        }

        response = chat(completion_create_params, model="test-model")

        # Assert results
        actual = json.loads(response.model_dump_json())
        expected = {
            "id": ANY,
            "choices": [
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "logprobs": None,
                    "message": {
                        "content": "agent result",
                        "refusal": None,
                        "role": "assistant",
                        "annotations": None,
                        "audio": None,
                        "function_call": None,
                        "tool_calls": None,
                    },
                }
            ],
            "created": ANY,
            "model": "test-model",
            "object": "chat.completion",
            "service_tier": None,
            "system_fingerprint": None,
            "usage": {
                "completion_tokens": 1,
                "prompt_tokens": 2,
                "total_tokens": 3,
                "completion_tokens_details": None,
                "prompt_tokens_details": None,
            },
            "pipeline_interactions": ANY,
        }
        assert actual == expected

        # Verify mocks were called correctly
        mock_agent.assert_called_once_with(**completion_create_params)
        mock_agent_instance.invoke.assert_called_once_with(
            completion_create_params={
                "model": "test-model",
                "messages": [{"role": "user", "content": '{"topic": "test"}'}],
                "environment_var": True,
            }
        )
