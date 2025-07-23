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
import time
import uuid
from typing import Any, Union

from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    CompletionCreateParams,
)
from openai.types.chat.chat_completion import Choice
from ragas import MultiTurnSample


class CustomModelChatResponse(ChatCompletion):
    pipeline_interactions: str | None = None


def create_inputs_from_completion_params(
    completion_create_params: CompletionCreateParams,
) -> Union[dict[str, Any], str]:
    """Load the user prompt from a JSON string or file."""
    input_prompt: Any = next(
        (
            msg
            for msg in completion_create_params["messages"]
            if msg.get("role") == "user"
        ),
        {},
    )
    if len(input_prompt) == 0:
        raise ValueError("No user prompt found in the messages.")
    user_prompt = input_prompt.get("content")

    try:
        inputs = json.loads(user_prompt)
    except json.JSONDecodeError:
        inputs = user_prompt

    return inputs  # type: ignore[no-any-return]


def create_completion_from_response_text(
    response_text: str,
    usage_metrics: dict[str, int],
    model: str,
    pipeline_interactions: MultiTurnSample | None = None,
) -> CustomModelChatResponse:
    """Convert the text of the LLM response into a chat completion response."""
    completion_id = str(uuid.uuid4())
    completion_timestamp = int(time.time())

    choice = Choice(
        index=0,
        message=ChatCompletionMessage(role="assistant", content=response_text),
        finish_reason="stop",
    )
    completion = CustomModelChatResponse(
        id=completion_id,
        object="chat.completion",
        choices=[choice],
        created=completion_timestamp,
        model=model,
        usage=CompletionUsage(**usage_metrics),
        pipeline_interactions=pipeline_interactions.model_dump_json()
        if pipeline_interactions
        else None,
    )
    return completion


def to_custom_model_response(
    agent_result: str,
    usage_metrics: dict[str, int],
    model: str,
) -> CustomModelChatResponse:
    """Convert the agent output to a custom model response."""
    response = create_completion_from_response_text(
        response_text=agent_result,
        usage_metrics=usage_metrics,
        model=model,
        pipeline_interactions=None,
    )
    return response
