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
from typing import Any

import pytest
from helpers import _extract_pipeline_interactions
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from ragas import MultiTurnSample


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

    result = _extract_pipeline_interactions(events)
    # The check is that with different ToolMessage content types there is no exception
    assert isinstance(result, MultiTurnSample)
    assert len(result.user_input) == 3
