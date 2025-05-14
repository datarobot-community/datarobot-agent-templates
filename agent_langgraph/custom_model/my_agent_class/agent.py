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
import functools
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union, cast

from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledGraph, CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def deployment_response_langgraph(func: FuncT) -> FuncT:
    @functools.wraps(func)
    def wrapper_response_langgraph(
        *args: Any, **kwargs: Any
    ) -> Tuple[str, Dict[str, int]]:
        value: List[Any] = func(*args, **kwargs)

        usage_metrics: Dict[str, int] = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        response = value[-1]
        node_name = next(iter(response))
        output = str(response[node_name]["messages"][-1].content)
        return output, usage_metrics

    return cast(FuncT, wrapper_response_langgraph)


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
    def llm_with_datarobot_llm_gateway(self) -> ChatLiteLLM:
        os.environ["DATAROBOT_API_KEY"] = self.api_key
        os.environ["DATAROBOT_API_BASE"] = self.api_base
        return ChatLiteLLM(
            model="datarobot/azure/gpt-4",
            api_base=self.api_base,
            api_key=self.api_key,
            model_kwargs={
                "clientId": "custom-model",
            },
        )

    @property
    def llm_with_datarobot_deployment(self) -> ChatLiteLLM:
        deployment_url = (
            f"{self.api_base}/api/v2/deployments/{os.environ.get('LLM_DEPLOYMENT_ID')}/"
        )
        os.environ["DATAROBOT_API_KEY"] = self.api_key
        os.environ["DATAROBOT_API_BASE"] = deployment_url
        return ChatLiteLLM(
            model="datarobot/azure/gpt-4",
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

    @deployment_response_langgraph
    def run(self, inputs: Dict[str, str]) -> list[Any]:
        # This crew uses one input which is a dictionary with the topic
        # Example: {"topic": "Artificial Intelligence"}
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

        return events
