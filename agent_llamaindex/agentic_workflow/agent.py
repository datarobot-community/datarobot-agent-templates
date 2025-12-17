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
# mypy: disable-error-code=attr-defined
from datetime import datetime
from typing import Any, Optional, Union

# isort: off
from config import Config

# isort: on
from datarobot_genai.core.agents import extract_user_prompt_content
from datarobot_genai.llama_index import (
    DataRobotLiteLLM,
)
from datarobot_genai.llama_index.base import LlamaIndexAgent
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    FunctionAgent,
)
from llama_index.core.workflow import Context


class MyAgent(LlamaIndexAgent):
    """MyAgent is a custom agent that uses LlamaIndex to plan, write, and edit content.
    It utilizes DataRobot's LLM Gateway or a specific deployment for language model interactions.
    This example illustrates 3 agents that handle content creation tasks, including planning, writing,
    and editing blog posts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        verbose: Optional[Union[bool, str]] = True,
        timeout: Optional[int] = 90,
        **kwargs: Any,
    ):
        super().__init__(
            api_key=api_key,
            api_base=api_base,
            model=model,
            verbose=verbose,
            timeout=timeout,
            **kwargs,
        )
        self.config = Config()
        self.default_model = self.config.llm_default_model

    def make_input_message(self, completion_create_params: Any) -> str:
        user_prompt_content = extract_user_prompt_content(completion_create_params)
        return (
            f"Your task is to write a concise report on a topic. "
            f"The topic is '{user_prompt_content}'. Make sure you find any interesting and relevant "
            f"information given the current year is {str(datetime.now().year)}. "
            f"Keep the final report under 500 words and don't overthink - this is a simple example task."
        )

    def build_workflow(self) -> AgentWorkflow:
        return AgentWorkflow(
            agents=[self.agent_planner, self.agent_writer],
            root_agent=self.agent_planner.name,
            initial_state={
                "planner_notes": {},
                "report_content": "Not written yet.",
            },
        )

    def extract_response_text(self, result_state: Any, events: list[Any]) -> str:
        return str(result_state["report_content"])

    def llm(
        self,
        preferred_model: str | None = None,
        auto_model_override: bool = True,
    ) -> DataRobotLiteLLM:
        api_base = self.litellm_api_base(self.config.llm_deployment_id)
        model = preferred_model
        if preferred_model is None:
            model = self.default_model
        if auto_model_override and not self.config.use_datarobot_llm_gateway:
            model = self.default_model
        if self.verbose:
            print(f"Using model: {model}")
        return DataRobotLiteLLM(
            model=model,
            api_base=api_base,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    @property
    def agent_planner(self) -> FunctionAgent:
        return FunctionAgent(
            name="PlannerAgent",
            description="Useful for planning content on a given topic and recording notes for the plan.",
            system_prompt=(
                "You are the PlannerAgent that can find information on a given topic and record notes on the topic. "
                "Once notes are recorded and you are satisfied, you should hand off control to the "
                "WriterAgent to write a report on the topic. You should have at least some notes on a topic "
                "before handing off control to the WriterAgent. Keep your notes brief and focused - don't overthink it. "
                "This is a simple example task."
            ),
            llm=self.llm(preferred_model="datarobot/azure/gpt-5-mini-2025-08-07"),
            tools=[self.planner_notes_tool, *self.mcp_tools],
            can_handoff_to=["WriterAgent"],
        )

    @property
    def agent_writer(self) -> FunctionAgent:
        return FunctionAgent(
            name="WriterAgent",
            description="Useful for writing a report on a given topic.",
            system_prompt=(
                "You are the WriteAgent that can write a report on a given topic. "
                "Your report should be in a markdown format. The content should be grounded in the planner notes. "
                "IMPORTANT: Keep your report concise and under 500 words total. Don't overthink - this is a simple example task."
            ),
            llm=self.llm(preferred_model="datarobot/azure/gpt-5-mini-2025-08-07"),
            tools=[self.writer_report_tool, *self.mcp_tools],
            # Writer is terminal in this simple flow; no handoff
        )

    @staticmethod
    async def planner_notes_tool(ctx: Context, notes: str, notes_title: str) -> str:
        current_state = await ctx.get("state")
        if "planner_notes" not in current_state:
            current_state["planner_notes"] = {}
        current_state["planner_notes"][notes_title] = notes
        await ctx.set("state", current_state)
        return "Notes recorded."

    @staticmethod
    async def writer_report_tool(ctx: Context, report_content: str) -> str:
        current_state = await ctx.get("state")
        current_state["report_content"] = report_content
        await ctx.set("state", current_state)
        return "Report written."
