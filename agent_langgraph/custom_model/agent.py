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
import re
from datetime import datetime
from typing import Any, Generator, Optional, Union
from urllib.parse import urljoin, urlparse

from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from openai.types.chat import CompletionCreateParams
from ragas import MultiTurnSample
from ragas.integrations.langgraph import convert_to_ragas_messages


class MyAgent:
    """MyAgent is a custom agent that uses Langgraph to plan, write, and edit content.
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
        self.api_base = (
            api_base
            or os.environ.get("DATAROBOT_ENDPOINT")
            or "https://api.datarobot.com"
        )
        self.model = model
        self.timeout = timeout
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    def invoke(
        self, completion_create_params: CompletionCreateParams
    ) -> Union[
        Generator[tuple[str, Any | None, dict[str, int]], None, None],
        tuple[str, Any | None, dict[str, int]],
    ]:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Args:
            completion_create_params: The completion request parameters including input topic and settings.
        Returns:
            Union[
                Generator[tuple[str, Any | None, dict[str, int]], None, None],
                tuple[str, Any | None, dict[str, int]],
            ]: For streaming requests, returns a generator yielding tuples of (response_text, pipeline_interactions, usage_metrics).
               For non-streaming requests, returns a single tuple of (response_text, pipeline_interactions, usage_metrics).
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

        # Construct the input message for the langgraph graph.
        input_message = Command(
            update={
                "messages": (
                    "user",
                    f"The topic is '{user_prompt_content}'. Make sure you find any interesting and relevant "
                    f"information given the current year is {str(datetime.now().year)}.",
                ),
            },
            goto="writer_node",
        )

        # Create and invoke the Langgraph Agentic Workflow with the inputs
        langgraph_workflow = StateGraph(MessagesState)
        langgraph_workflow.add_node("planner_node", self.task_plan)
        langgraph_workflow.add_node("writer_node", self.task_write)
        langgraph_workflow.add_node("editor_node", self.task_edit)
        langgraph_workflow.add_edge(START, "planner_node")
        langgraph_execution_graph = langgraph_workflow.compile()

        graph_stream = langgraph_execution_graph.stream(
            input=input_message,
            config={
                "recursion_limit": 150
            },  # Maximum number of steps to take in the graph
            debug=True,
        )

        usage_metrics: dict[str, int] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }

        # The following code demonstrate both a synchronous and streaming response.
        # You can choose one or the other based on your use case, they function the same.
        # The main difference is returning a generator for streaming or a final response for sync.
        if completion_create_params.get("stream"):
            # Streaming response: yield each message as it is generated
            def stream_generator() -> Generator[
                tuple[str, Any | None, dict[str, int]], None, None
            ]:
                # For each event in the graph stream, yield the latest message content
                # along with updated usage metrics.
                events = []
                for event in graph_stream:
                    events.append(event)
                    current_node = next(iter(event))
                    yield (
                        str(event[current_node]["messages"][-1].content),
                        None,
                        usage_metrics,
                    )
                    current_usage = event[current_node].get("usage", {})
                    if current_usage:
                        usage_metrics["total_tokens"] += current_usage.get(
                            "total_tokens", 0
                        )
                        usage_metrics["prompt_tokens"] += current_usage.get(
                            "prompt_tokens", 0
                        )
                        usage_metrics["completion_tokens"] += current_usage.get(
                            "completion_tokens", 0
                        )

                # Create a list of events from the event listener
                pipeline_interactions = self.create_pipeline_interactions_from_events(
                    events
                )

                # yield the final response indicating completion
                yield "", pipeline_interactions, usage_metrics

            return stream_generator()
        else:
            # Synchronous response: collect all events and return the final message
            events = [event for event in graph_stream]
            pipeline_interactions = self.create_pipeline_interactions_from_events(
                events
            )

            # Extract the final event from the graph stream as the synchronous response
            last_event = events[-1]
            node_name = next(iter(last_event))
            response_text = str(last_event[node_name]["messages"][-1].content)
            current_usage = last_event[node_name].get("usage", {})
            if current_usage:
                usage_metrics["total_tokens"] += current_usage.get("total_tokens", 0)
                usage_metrics["prompt_tokens"] += current_usage.get("prompt_tokens", 0)
                usage_metrics["completion_tokens"] += current_usage.get(
                    "completion_tokens", 0
                )

            return response_text, pipeline_interactions, usage_metrics

    @property
    def llm(self) -> ChatLiteLLM:
        """Returns a ChatLiteLLM instance configured to use DataRobot's LLM Gateway or a specific deployment.

        For help configuring different LLM backends see:
        https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/developing-agents-llm-providers.md
        """
        api_base = urlparse(self.api_base)
        if os.environ.get("LLM_DATAROBOT_DEPLOYMENT_ID"):
            path = api_base.path
            if "/api/v2/deployments" not in path and "api/v2/genai" not in path:
                # Ensure the API base ends with /api/v2/ for deployments
                if not path.endswith("/api/v2/") and not path.endswith("/api/v2"):
                    path = urljoin(path + "/", "api/v2/")
                if not path.endswith("/"):
                    path += "/"
                api_base = api_base._replace(path=path)
                deployment_url = urljoin(
                    api_base.geturl(),
                    f"deployments/{os.environ.get('LLM_DATAROBOT_DEPLOYMENT_ID')}/",
                )
            else:
                # If user specifies a likely deployment URL then leave it alone
                deployment_url = api_base.geturl()
            return ChatLiteLLM(
                model="datarobot/azure/gpt-4o-mini",
                api_base=deployment_url,
                api_key=self.api_key,
                timeout=self.timeout,
            )
        else:
            # Ensure the API base does not end with /api/v2/ for LLM Gateway
            path = api_base.path
            if path.endswith("api/v2/") or path.endswith("api/v2"):
                path = re.sub(r"/api/v2/?$", "/", path)
            api_base = api_base._replace(path=path)
            return ChatLiteLLM(
                model="datarobot/azure/gpt-4o-mini",
                api_base=api_base.geturl(),
                api_key=self.api_key,
                timeout=self.timeout,
            )

    @property
    def agent_planner(self) -> Any:
        return create_react_agent(
            self.llm,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content planner. You are working with a content writer and editor colleague.\n"
                "You're working on planning a blog article about the topic. You collect information that helps the "
                "audience learn something and make informed decisions. Your work is the basis for the Content Writer "
                "to write an article on this topic."
                "\n"
                "1. Prioritize the latest trends, key players, and noteworthy news on the topic.\n"
                "2. Identify the target audience, considering their interests and pain points.\n"
                "3. Develop a detailed content outline including an introduction, key points, and a call to action.\n"
                "4. Include SEO keywords and relevant data or sources."
                "\n"
                "Plan engaging and factually accurate content on the topic. You must create a comprehensive content "
                "plan document with an outline, audience analysis, SEO keywords, and resources.",
            ),
        )

    @property
    def agent_writer(self) -> Any:
        return create_react_agent(
            self.llm,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content writer. You are working with a planner and editor colleague.\n"
                "You're working on writing a new opinion piece about the topic. You base your writing on the work "
                "of the Content Planner, who provides an outline and relevant context about the topic. You follow "
                "the main objectives and direction of the outline, as provided by the Content Planner. You also "
                "provide objective and impartial insights and back them up with information provided by the Content "
                "Planner. You acknowledge in your opinion piece when your statements are opinions as opposed to "
                "objective statements.\n"
                "1. Use the content plan to craft a compelling blog post.\n"
                "2. Incorporate SEO keywords naturally.\n"
                "3. Sections/Subtitles are properly named in an engaging manner.\n"
                "4. Ensure the post is structured with an engaging introduction, insightful body, and a summarizing "
                "conclusion.\n"
                "5. Proofread for grammatical errors and alignment with the brand's voice.\n"
                "Write insightful and factually accurate opinion piece about the topic. You must create a "
                "well-written blog post in markdown format, ready for publication, each section should have 2 or 3 "
                "paragraphs.",
            ),
        )

    @property
    def agent_editor(self) -> Any:
        return create_react_agent(
            self.llm,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content editor. You are working with a planner and writer colleague.\n"
                "You are an editor who receives a blog post from the Content Writer. Your goal is to review the "
                "blog post to ensure that it follows journalistic best practices, provides balanced viewpoints when "
                "providing opinions or assertions, and also avoids major controversial topics or opinions when "
                "possible.\n"
                "Proofread the given blog post for grammatical errors and alignment with the brand's voice.\n"
                "You must create a well-written blog post in markdown format, ready for publication, each section "
                "should have 2 or 3 paragraphs.\n"
                "You should return ONLY the full corrected blog post in markdown format, "
                "do not include any commentary or explanations.",
            ),
        )

    def task_plan(self, state: MessagesState) -> Command[Any]:
        result = self.agent_planner.invoke(state)
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="planner_node"
        )
        return Command(
            update={
                # share internal message history with other agents
                "messages": result["messages"],
            },
            goto="writer_node",
        )

    def task_write(self, state: MessagesState) -> Command[Any]:
        result = self.agent_writer.invoke(state)
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="writer_node"
        )
        return Command(
            update={
                # share internal message history with other agents
                "messages": result["messages"],
            },
            goto="editor_node",
        )

    def task_edit(self, state: MessagesState) -> Command[Any]:
        result = self.agent_planner.invoke(state)
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="editor_node"
        )
        return Command(
            update={
                # share internal message history with other agents
                "messages": result["messages"],
            },
            goto=END,
        )

    @staticmethod
    def make_system_prompt(suffix: str) -> str:
        return (
            "You are a helpful AI assistant, collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK, another assistant with different tools "
            " will help where you left off. Execute what you can to make progress."
            f"\n{suffix}"
        )

    @staticmethod
    def create_pipeline_interactions_from_events(
        events: list[dict[str, Any]],
    ) -> MultiTurnSample | None:
        """Convert a list of events into a MultiTurnSample.

        Creates the pipeline interactions for moderations and evaluation
        (e.g. Task Adherence, Agent Goal Accuracy, Tool Call Accuracy)
        """
        if not events:
            return None

        messages = []
        for e in events:
            for k, v in e.items():
                messages.extend(v["messages"])

        # Drop the ToolMessages since they may not be compatible with Ragas ToolMessage
        # that is needed for the MultiTurnSample.
        messages = [m for m in messages if not isinstance(m, ToolMessage)]

        ragas_trace = convert_to_ragas_messages(messages)
        return MultiTurnSample(user_input=ragas_trace)
