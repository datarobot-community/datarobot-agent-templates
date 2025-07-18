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
from typing import Any, Optional, Union

from helpers import create_inputs_from_completion_params
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledGraph, CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from openai.types.chat import CompletionCreateParams


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
            **kwargs: Any: Additional keyword arguments passed to the agent.
                Contains any parameters received in the CompletionCreateParams.

        Returns:
            None
        """
        self.api_key = api_key or os.environ.get("DATAROBOT_API_TOKEN")
        self.api_base = api_base or os.environ.get("DATAROBOT_ENDPOINT")
        self.model = model
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

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
    def llm_with_datarobot_llm_gateway(self) -> ChatLiteLLM:
        """Returns a ChatLiteLLM instance configured to use DataRobot's LLM Gateway.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        return ChatLiteLLM(
            model="datarobot/azure/gpt-4o-mini",
            api_base=self.api_base_litellm,
            api_key=self.api_key,
        )

    @property
    def llm_with_datarobot_deployment(self) -> ChatLiteLLM:
        """Returns a ChatLiteLLM instance configured to use DataRobot's LLM Deployments.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        deployment_url = f"{self.api_base_litellm}/api/v2/deployments/{os.environ.get('LLM_DEPLOYMENT_ID')}/"
        return ChatLiteLLM(
            model="datarobot/azure/gpt-4o-mini",
            api_base=deployment_url,
            api_key=self.api_key,
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

    @property
    def agent_planner(self) -> CompiledGraph:
        return create_react_agent(
            self.llm_with_datarobot_llm_gateway,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content planner. You are working with an content writer and editor colleague."
                "\n"
                "You're working on planning a blog article "
                "about the topic."
                "You collect information that helps the "
                "audience learn something "
                "and make informed decisions. "
                "Your work is the basis for "
                "the Content Writer to write an article on this topic."
                "\n"
                "1. Prioritize the latest trends, key players, "
                "and noteworthy news on the topic.\n"
                "2. Identify the target audience, considering "
                "their interests and pain points.\n"
                "3. Develop a detailed content outline including "
                "an introduction, key points, and a call to action.\n"
                "4. Include SEO keywords and relevant data or sources."
                "\n"
                "Plan engaging and factually accurate content on the topic."
                "You must create a comprehensive content plan document "
                "with an outline, audience analysis, "
                "SEO keywords, and resources.",
            ),
        )

    @property
    def agent_writer(self) -> CompiledGraph:
        return create_react_agent(
            self.llm_with_datarobot_llm_gateway,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content writer. You are working with an planner and editor colleague."
                "\n"
                "You're working on writing "
                "a new opinion piece about the topic. "
                "You base your writing on the work of "
                "the Content Planner, who provides an outline "
                "and relevant context about the topic. "
                "You follow the main objectives and "
                "direction of the outline, "
                "as provide by the Content Planner. "
                "You also provide objective and impartial insights "
                "and back them up with information "
                "provide by the Content Planner. "
                "You acknowledge in your opinion piece "
                "when your statements are opinions "
                "as opposed to objective statements."
                "\n"
                "1. Use the content plan to craft a compelling "
                "blog post.\n"
                "2. Incorporate SEO keywords naturally.\n"
                "3. Sections/Subtitles are properly named "
                "in an engaging manner.\n"
                "4. Ensure the post is structured with an "
                "engaging introduction, insightful body, "
                "and a summarizing conclusion.\n"
                "5. Proofread for grammatical errors and "
                "alignment with the brand's voice.\n"
                "\n"
                "Write insightful and factually accurate opinion piece "
                "about the topic."
                "You must create a well-written blog post "
                "in markdown format, ready for publication, "
                "each section should have 2 or 3 paragraphs.",
            ),
        )

    @property
    def agent_editor(self) -> CompiledGraph:
        return create_react_agent(
            self.llm_with_datarobot_llm_gateway,
            tools=[],
            prompt=self.make_system_prompt(
                "You are a content editor. You are working with an planner and writer colleague."
                "\n"
                "You are an editor who receives a blog post "
                "from the Content Writer. "
                "Your goal is to review the blog post "
                "to ensure that it follows journalistic best practices,"
                "provides balanced viewpoints "
                "when providing opinions or assertions, "
                "and also avoids major controversial topics "
                "or opinions when possible."
                "\n"
                "Proofread the given blog post for grammatical errors "
                "and alignment with the brand's voice."
                "\n"
                "Edit a given blog post to align with the writing style "
                "of the organization."
                "You must create a well-written blog post in markdown format, "
                "ready for publication, "
                "each section should have 2 or 3 paragraphs.",
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
        result = self.agent_planner.invoke(state)
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

    def graph(self) -> CompiledStateGraph:
        workflow = StateGraph(MessagesState)
        workflow.add_node("planner_node", self.task_plan)
        workflow.add_node("writer_node", self.task_write)
        workflow.add_node("editor_node", self.task_edit)
        workflow.add_edge(START, "planner_node")
        execution_graph = workflow.compile()
        return execution_graph

    def run(
        self, completion_create_params: CompletionCreateParams
    ) -> tuple[list[Any], dict[str, int]]:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Inputs can be extracted from the completion_create_params in several ways. A helper function
        `create_inputs_from_completion_params` is provided to extract the inputs as json or a string
        from the 'user' portion of the input prompt. Alternatively you can extract and use one or
        more inputs or messages from the completion_create_params["messages"] field.

        Args:
            completion_create_params (CompletionCreateParams): The parameters for
                the completion request, which includes the input topic and other settings.
        Returns:
            tuple[list[Any], CrewOutput]: A tuple containing a list of messages (events) and the crew output.

        """
        # Example helper for extracting inputs as a json from the completion_create_params["messages"]
        # field with the 'user' role: (e.g. {"topic": "Artificial Intelligence"})
        inputs = create_inputs_from_completion_params(completion_create_params)

        # If inputs are a string, convert to a dictionary with 'topic' key for this example.
        if isinstance(inputs, str):
            inputs = {"topic": inputs}

        # Print commands may need flush=True to ensure they are displayed in real-time.
        print("Running agent with inputs:", inputs, flush=True)

        # Construct the input message for the langgraph graph.
        input_message = {
            "messages": [
                (
                    "user",
                    f"The topic is '{inputs['topic']}'. Make sure you find any interesting and relevant"
                    f"information given the current year is {str(datetime.now().year)}.",
                )
            ],
        }

        # Graph stream is a generator that will execute the graph
        graph_stream = self.graph().stream(
            input_message,
            # Maximum number of steps to take in the graph
            {"recursion_limit": 150},
            debug=True,
        )

        # Execute the graph and store calls to the agent in events
        events = [event for event in graph_stream]
        usage_metrics: dict[str, int] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        return events, usage_metrics
