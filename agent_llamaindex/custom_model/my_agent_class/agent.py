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
import asyncio
from typing import Any, Dict, Tuple, Union

from llama_index.core.agent.workflow import (
    AgentInput,
    AgentOutput,
    AgentStream,
    AgentWorkflow,
    FunctionAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.base.llms.types import LLMMetadata
from llama_index.core.workflow import Context
from llama_index.llms.litellm import LiteLLM


class DataRobotLiteLLM(LiteLLM):  # type: ignore[misc]
    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=128000,
            num_output=self.max_tokens or -1,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name=self.model,
        )


class MyAgent:
    def __init__(
        self, api_key: str, api_base: str, verbose: Union[bool, str], **kwargs: Any
    ):
        self.api_key = api_key
        self.api_base = api_base
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    @property
    def llm(self) -> DataRobotLiteLLM:
        return DataRobotLiteLLM(
            model="datarobot/bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
            additional_kwargs={"clientId": "custom-model"},
            api_base=self.api_base,
            api_key=self.api_key,
        )

    @staticmethod
    async def record_notes(ctx: Context, notes: str, notes_title: str) -> str:
        """Useful for recording notes on a given topic. Your input should be notes with a
        title to save the notes under."""
        current_state = await ctx.get("state")
        if "research_notes" not in current_state:
            current_state["research_notes"] = {}
        current_state["research_notes"][notes_title] = notes
        await ctx.set("state", current_state)
        return "Notes recorded."

    @staticmethod
    async def write_report(ctx: Context, report_content: str) -> str:
        """Useful for writing a report on a given topic. Your input should be a markdown formatted report."""
        current_state = await ctx.get("state")
        current_state["report_content"] = report_content
        await ctx.set("state", current_state)
        return "Report written."

    @staticmethod
    async def review_report(ctx: Context, review: str) -> str:
        """Useful for reviewing a report and providing feedback. Your input should be a review of the report."""
        current_state = await ctx.get("state")
        current_state["review"] = review
        await ctx.set("state", current_state)
        return "Report reviewed."

    @property
    def research_agent(self) -> FunctionAgent:
        return FunctionAgent(
            name="ResearchAgent",
            description="Useful for finding information on a given topic and recording notes on the topic.",
            system_prompt=(
                "You are the ResearchAgent that can find information on a given topic and record notes on the topic. "
                "Once notes are recorded and you are satisfied, you should hand off control to the "
                "WriteAgent to write a report on the topic. You should have at least some notes on a topic "
                "before handing off control to the WriteAgent."
            ),
            llm=self.llm,
            tools=[self.record_notes],
            can_handoff_to=["WriteAgent"],
        )

    @property
    def write_agent(self) -> FunctionAgent:
        return FunctionAgent(
            name="WriteAgent",
            description="Useful for writing a report on a given topic.",
            system_prompt=(
                "You are the WriteAgent that can write a report on a given topic. "
                "Your report should be in a markdown format. The content should be grounded in the research notes. "
                "Once the report is written, you should get feedback at least once from the ReviewAgent."
            ),
            llm=self.llm,
            tools=[self.write_report],
            can_handoff_to=["ReviewAgent", "ResearchAgent"],
        )

    @property
    def review_agent(self) -> FunctionAgent:
        return FunctionAgent(
            name="ReviewAgent",
            description="Useful for reviewing a report and providing feedback.",
            system_prompt=(
                "You are the ReviewAgent that can review the write report and provide feedback. "
                "Your review should either approve the current report or request changes for the "
                "WriteAgent to implement.  If you have feedback that requires changes, you should hand "
                "off control to the WriteAgent to implement the changes after submitting the review."
            ),
            llm=self.llm,
            tools=[self.review_report],
            can_handoff_to=["WriteAgent"],
        )

    async def run_async(self, user_prompt: str) -> Any:
        agent_workflow = AgentWorkflow(
            agents=[self.research_agent, self.write_agent, self.review_agent],
            root_agent=self.research_agent.name,
            initial_state={
                "research_notes": {},
                "report_content": "Not written yet.",
                "review": "Review required.",
            },
        )

        handler = agent_workflow.run(user_msg=user_prompt)

        current_agent = None
        async for event in handler.stream_events():
            if (
                hasattr(event, "current_agent_name")
                and event.current_agent_name != current_agent
            ):
                current_agent = event.current_agent_name
                print(f"\n{'=' * 50}")
                print(f"🤖 Agent: {current_agent}")
                print(f"{'=' * 50}\n")
            if isinstance(event, AgentStream):
                if event.delta:
                    print(event.delta, end="", flush=True)
            elif isinstance(event, AgentInput):
                print("📥 Input:", event.input)
            elif isinstance(event, AgentOutput):
                if event.response.content:
                    print("📤 Output:", event.response.content)
                if event.tool_calls:
                    print(
                        "🛠️  Planning to use tools:",
                        [call.tool_name for call in event.tool_calls],
                    )
            elif isinstance(event, ToolCallResult):
                print(f"🔧 Tool Result ({event.tool_name}):")
                print(f"  Arguments: {event.tool_kwargs}")
                print(f"  Output: {event.tool_output}")
            elif isinstance(event, ToolCall):
                print(f"🔨 Calling Tool: {event.tool_name}")
                print(f"  With arguments: {event.tool_kwargs}")

        return await handler.ctx.get("state")  # type: ignore[union-attr]

    def run(self, inputs: Dict[str, str]) -> Tuple[str, Dict[str, int]]:
        user_prompt = (
            f"Write me a report on the {inputs['topic']}. "
            f"Briefly describe the history of {inputs['topic']}, important developments, "
            f"and the current state in the 21st century."
        )
        result = asyncio.run(self.run_async(user_prompt))

        usage_metrics: Dict[str, int] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        return str(result["report_content"]), usage_metrics
