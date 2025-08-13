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

import requests
from helpers import create_inputs_from_completion_params
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledGraph, CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from openai.types.chat import CompletionCreateParams
from langchain.tools import BaseTool


class ApiQueryTool(BaseTool):
    name = "api_query_tool"
    description = (
        "A tool that sends a query string to an API endpoint with a pre-configured token in the headers, "
        "and returns a list of items from the JSON response body."
    )

    def __init__(self, api_url: str, token: str):
        super().__init__()
        self.api_url = api_url
        self.token = token

    def _run(self, query: str) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"query": query}
        response = requests.get(self.api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Assumes the list is under the 'body' key in the response
        return data.get("body", [])

    async def _arun(self, query: str) -> Any:
        # For async support, you could use httpx or aiohttp
        raise NotImplementedError("Async not implemented for ApiQueryTool.")


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
        nim_deployment_id: Optional[str] = None,
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
        # Deployment ID for NIM container on datarobot
        self.nim_deployment_id = nim_deployment_id
        # SSO Token for local tool authentication
        self.sso_token = kwargs.get("extra_body").get("sso_token", None)
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    @property
    def nim_deployment(self) -> ChatOpenAI:
        """Returns a ChatOpenAI instance configured to use DataRobot's LLM Deployments.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        return ChatOpenAI(
            model="meta/llama3-8b-instruct",
            base_url=f"https://app.datarobot.com/api/v2/deployments/{self.nim_deployment_id}",
            api_key=self.api_key,
            timeout=self.timeout,
            default_headers={
                "Authorization": f"Bearer {self.api_key}"
            }
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
    def agent_summarizer(self) -> CompiledGraph:
        # Create an instance of the ApiQueryTool with the token pre-configured
        # You should replace this with your actual API endpoint
        api_tool = ApiQueryTool(api_url="https://your-api-endpoint.com/api/search", token=self.sso_token or "your-token-here")

        return create_react_agent(
            self.nim_deployment,
            tools=[api_tool],
            prompt=self.make_system_prompt(
                "You are a content summarizer. You help gather and summarize information from external APIs."
                "\n"
                "You have access to an API query tool that can search for information using a query string."
                "Use this tool to gather relevant information about the topic by sending queries to the API."
                "The API will return a list of items that you should analyze and summarize."
                "\n"
                "When using the api_query_tool, you only need to provide:"
                "1. query: A search string related to the topic"
                "(The authentication token is already configured)"
                "\n"
                "Your goal is to:"
                "1. Query the API for relevant information about the topic"
                "2. Analyze the returned data"
                "3. Create a comprehensive summary of the findings"
                "4. Highlight key insights and important details"
                "\n"
                "Provide a well-structured summary based on the API responses.",
            ),
        )

    def task_summarize(self, state: MessagesState) -> Command[Any]:
        result = self.agent_summarizer.invoke(state)
        result["messages"][-1] = HumanMessage(
            content=result["messages"][-1].content, name="summarizer_node"
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
        workflow.add_node("summarizer_node", self.task_summarize)
        workflow.add_edge(START, "summarizer_node")
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
