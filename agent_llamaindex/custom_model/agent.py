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
import asyncio
import os
import re
from datetime import datetime
from typing import Any, Optional, Sequence, Tuple, Union

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
from llama_index.core.workflow import Context, Event
from llama_index.llms.litellm import LiteLLM
from openai.types.chat import CompletionCreateParams


class DataRobotLiteLLM(LiteLLM):  # type: ignore[misc]
    """DataRobotLiteLLM is a small LiteLLM wrapper class that makes all LiteLLM endpoints compatible with the
    LlamaIndex library."""

    @property
    def metadata(self) -> LLMMetadata:
        """Returns the metadata for the LLM.

        This is required to enable the is_chat_model and is_function_calling_model, which are
        mandatory for LlamaIndex agents. By default, LlamaIndex assumes these are false unless each individual
        model config in LiteLLM explicitly sets them to true. To use custom LLM endpoints with LlamaIndex agents,
        you must override this method to return the appropriate metadata.
        """
        return LLMMetadata(
            context_window=128000,
            num_output=self.max_tokens or -1,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name=self.model,
        )


class MyAgent:
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
        """Initializes the MyAgent class with API key, base URL, model, and verbosity settings.

        Args:
            api_key: Optional[str]: API key for authentication with DataRobot services.
                Defaults to None, in which case it will use the DATAROBOT_API_TOKEN environment variable.
            api_base: Optional[str]: Base URL for the DataRobot API.
                Defaults to None, in which case it will use the DATAROBOT_ENDPOINT environment variable.
            model: Optional[str]: The LLM model to use.
                Defaults to None.
            verbose: Optional[Union[bool, str]]: Whether to enable verbose logging.
                Accepts boolean or string values ("true"/"false"). Defaults to True.
            timeout: Optional[int]: How long to wait for the agent to respond.
                Defaults to 90 seconds.
            **kwargs: Any: Additional keyword arguments passed to the agent.
                Contains any parameters received in the CompletionCreateParams.

        Returns:
            None
        """
        self.api_key = api_key or os.environ.get("DATAROBOT_API_TOKEN")
        self.api_base = api_base or os.environ.get("DATAROBOT_ENDPOINT")
        self.model = model
        self.timeout = timeout
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    def run(
        self, completion_create_params: CompletionCreateParams
    ) -> Tuple[str, dict[str, int], Sequence[Event] | None]:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Args:
            completion_create_params: The completion request parameters including input topic and settings.
        Returns:
            tuple[str, dict[str, int], Sequence[Event] | None]: A tuple containing the agent
                response, usage_statistics and a list of messages (events).
        """
        # Retrieve the starting user prompt from the CompletionCreateParams
        user_messages = [
            msg
            for msg in completion_create_params["messages"]
            # You can use other roles as needed (e.g. "system", "assistant")
            if msg.get("role") == "user"
        ]
        user_prompt: Any = user_messages[0] if user_messages else {}
        user_prompt_content = user_prompt.get("content", {})

        # Print commands may need flush=True to ensure they are displayed in real-time.
        print("Running agent with user prompt:", user_prompt_content, flush=True)

        input_message = (
            f"Your task is to write a detailed report on a topic. "
            f"The topic is '{user_prompt_content}'. Make sure you find any interesting and relevant"
            f"information given the current year is {str(datetime.now().year)}."
        )

        result, events = asyncio.run(
            self.run_llamaindex_agentic_workflow(input_message)
        )

        usage_metrics: dict[str, int] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }

        # The `events` variable is used to compute agentic metrics and guardrails
        # If you are not interested in these metrics, you can also return None instead.
        return str(result["report_content"]), usage_metrics, events

    async def run_llamaindex_agentic_workflow(self, user_prompt: str) -> Any:
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
        events = []
        async for event in handler.stream_events():
            events.append(event)
            if (
                hasattr(event, "current_agent_name")
                and event.current_agent_name != current_agent
            ):
                current_agent = event.current_agent_name
                print(f"\n{'=' * 50}", flush=True)
                print(f"🤖 Agent: {current_agent}", flush=True)
                print(f"{'=' * 50}\n", flush=True)
            if isinstance(event, AgentStream):
                if event.delta:
                    print(event.delta, end="", flush=True)
            elif isinstance(event, AgentInput):
                print("📥 Input:", event.input, flush=True)
            elif isinstance(event, AgentOutput):
                if event.response.content:
                    print("📤 Output:", event.response.content, flush=True)
                if event.tool_calls:
                    print(
                        "🛠️  Planning to use tools:",
                        [call.tool_name for call in event.tool_calls],
                        flush=True,
                    )
            elif isinstance(event, ToolCallResult):
                print(f"🔧 Tool Result ({event.tool_name}):", flush=True)
                print(f"  Arguments: {event.tool_kwargs}", flush=True)
                print(f"  Output: {event.tool_output}", flush=True)
            elif isinstance(event, ToolCall):
                print(f"🔨 Calling Tool: {event.tool_name}", flush=True)
                print(f"  With arguments: {event.tool_kwargs}", flush=True)

        return await handler.ctx.get("state"), events  # type: ignore[union-attr]

    @property
    def llm(self) -> DataRobotLiteLLM:
        """Returns a LlamaIndex LiteLLM compatible LLM instance configured to use DataRobot's LLM Gateway or a specific deployment."""
        if os.environ.get("LLM_DATAROBOT_DEPLOYMENT_ID"):
            return self.llm_with_datarobot_deployment
        else:
            return self.llm_with_datarobot_llm_gateway

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
    def api_base_litellm(self) -> str:
        """Returns a modified version of the API base URL suitable for LiteLLM.

        Strips 'api/v2/' or 'api/v2' from the end of the URL if present.

        Returns:
            str: The modified API base URL.
        """
        if self.api_base:
            return re.sub(r"api/v2/?$", "", self.api_base)
        return "https://api.datarobot.com"

    @property
    def llm_with_datarobot_llm_gateway(self) -> DataRobotLiteLLM:
        """Returns a LlamaIndex LiteLLM compatible LLM instance configured to use DataRobot's LLM Gateway.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """

        # NOTE: LlamaIndex tool encodings are sensitive the the LLM model used and may need to be re-written
        # to work with different models. This example assumes the model is a GPT compatible model.
        return DataRobotLiteLLM(
            model="datarobot/azure/gpt-4o-mini",
            api_base=self.api_base_litellm,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    @property
    def llm_with_datarobot_deployment(self) -> DataRobotLiteLLM:
        """Returns a LlamaIndex LiteLLM compatible LLM instance configured to use DataRobot's LLM Deployments.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        deployment_url = f"{self.api_base}/deployments/{os.environ.get('LLM_DATAROBOT_DEPLOYMENT_ID')}/"

        # NOTE: LlamaIndex tool encodings are sensitive the the LLM model used and may need to be re-written
        # to work with different models. This example assumes the model is a GPT compatible model.
        return DataRobotLiteLLM(
            model="openai/gpt-4o-mini",
            api_base=deployment_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )
