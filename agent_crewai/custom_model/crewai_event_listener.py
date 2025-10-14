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
from typing import Any, Union

try:
    from crewai.events.base_event_listener import BaseEventListener
    from crewai.events.event_bus import CrewAIEventsBus
    from crewai.events.event_types import (
        AgentExecutionCompletedEvent,
        AgentExecutionStartedEvent,
        CrewKickoffStartedEvent,
        ToolUsageFinishedEvent,
        ToolUsageStartedEvent,
    )
# Handle legacy crewai package structure
except ImportError:
    from crewai.utilities.events import (
        AgentExecutionCompletedEvent,
        AgentExecutionStartedEvent,
        CrewAIEventsBus,
        CrewKickoffStartedEvent,
        ToolUsageFinishedEvent,
        ToolUsageStartedEvent,
    )
    from crewai.utilities.events.base_event_listener import BaseEventListener

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
