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
import logging
import time
import uuid
from typing import Any, Union

from crewai import CrewOutput
from crewai.utilities.events import (
    AgentExecutionCompletedEvent,
    AgentExecutionStartedEvent,
    CrewAIEventsBus,
    CrewKickoffStartedEvent,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)
from crewai.utilities.events.base_event_listener import BaseEventListener
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    CompletionCreateParams,
)
from openai.types.chat.chat_completion import Choice
from ragas import MultiTurnSample
from ragas.messages import AIMessage, HumanMessage, ToolCall, ToolMessage


class CrewAIEventListener(BaseEventListener):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[Union[HumanMessage, AIMessage, ToolMessage]] = []

    def setup_listeners(self, crewai_event_bus: CrewAIEventsBus) -> None:
        @crewai_event_bus.on(CrewKickoffStartedEvent)  # type: ignore[misc]
        def on_crew_execution_started(_: Any, event: CrewKickoffStartedEvent) -> None:
            self.messages.append(
                HumanMessage(content=f"Working on input '{json.dumps(event.inputs)}'")
            )

        @crewai_event_bus.on(AgentExecutionStartedEvent)  # type: ignore[misc]
        def on_agent_execution_started(
            _: Any, event: AgentExecutionStartedEvent
        ) -> None:
            self.messages.append(AIMessage(content=event.task_prompt, tool_calls=[]))

        @crewai_event_bus.on(AgentExecutionCompletedEvent)  # type: ignore[misc]
        def on_agent_execution_completed(
            _: Any, event: AgentExecutionCompletedEvent
        ) -> None:
            self.messages.append(AIMessage(content=event.output, tool_calls=[]))

        @crewai_event_bus.on(ToolUsageStartedEvent)  # type: ignore[misc]
        def on_tool_usage_started(_: Any, event: ToolUsageStartedEvent) -> None:
            # Its a tool call - add tool call to last AIMessage
            if len(self.messages) == 0:
                logging.warning("Direct tool usage without agent invocation")
                return
            last_message = self.messages[-1]
            if not isinstance(last_message, AIMessage):
                logging.warning(
                    "Tool call must be preceded by an AIMessage somewhere in the conversation."
                )
                return
            tool_call = ToolCall(name=event.tool_name, args=json.loads(event.tool_args))
            last_message.tool_calls.append(tool_call)

        @crewai_event_bus.on(ToolUsageFinishedEvent)  # type: ignore[misc]
        def on_tool_usage_finished(_: Any, event: ToolUsageFinishedEvent) -> None:
            if len(self.messages) == 0:
                logging.warning("Direct tool usage without agent invocation")
                return
            last_message = self.messages[-1]
            if not isinstance(last_message, AIMessage):
                logging.warning(
                    "Tool call must be preceded by an AIMessage somewhere in the conversation."
                )
                return
            if not last_message.tool_calls:
                logging.warning("No previous tool calls found")
                return
            self.messages.append(ToolMessage(content=event.output))


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
    crew_output: CrewOutput,
    events: list[Union[HumanMessage, AIMessage, ToolMessage]] | None,
    model: str,
) -> CustomModelChatResponse:
    """Convert the CrewAI agent output to a custom model response."""
    usage_metrics: dict[str, int] = {
        "completion_tokens": crew_output.token_usage.completion_tokens,
        "prompt_tokens": crew_output.token_usage.prompt_tokens,
        "total_tokens": crew_output.token_usage.total_tokens,
    }

    pipeline_interactions = None
    if events is not None:
        pipeline_interactions = MultiTurnSample(user_input=events)
    response = create_completion_from_response_text(
        response_text=str(crew_output.raw),
        usage_metrics=usage_metrics,
        model=model,
        pipeline_interactions=pipeline_interactions,
    )
    return response
