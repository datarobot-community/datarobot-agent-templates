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

from langchain_core.messages import ToolMessage
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    CompletionCreateParams,
)
from openai.types.chat.chat_completion import Choice
from ragas import MultiTurnSample
from ragas.integrations.langgraph import convert_to_ragas_messages


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


def _extract_pipeline_interactions(events: list[dict[str, Any]]) -> MultiTurnSample:
    """Extract the pipeline interactions from the events."""
    messages = []
    for e in events:
        for k, v in e.items():
            messages.extend(v["messages"])

    # Drop the ToolMessages since they may not be compatible with Ragas ToolMessage
    # that is needed for the MultiTurnSample.
    messages = [m for m in messages if not isinstance(m, ToolMessage)]

    ragas_trace = convert_to_ragas_messages(messages)
    pipeline_interactions = MultiTurnSample(user_input=ragas_trace)
    return pipeline_interactions


def to_custom_model_response(
    events: list[dict[str, Any]],
    usage_metrics: dict[str, int],
    model: str,
) -> CustomModelChatResponse:
    """Convert the Langgraph agent output to a custom model response."""
    last_event = events[-1]
    node_name = next(iter(last_event))
    output = str(last_event[node_name]["messages"][-1].content)

    # The `pipeline_interactions` parameter is used to compute agentic metrics
    # (e.g. Task Adherence, Agent Goal Accuracy, Agent Goal Accuracy with Reference,
    # Tool Call Accuracy).
    # If you are not interested in these metrics, you can also pass None instead.
    # This will reduce the size of the response significantly.
    response = create_completion_from_response_text(
        response_text=output,
        usage_metrics=usage_metrics,
        model=model,
        pipeline_interactions=_extract_pipeline_interactions(events),
    )
    return response
