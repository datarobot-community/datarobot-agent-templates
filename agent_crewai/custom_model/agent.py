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
from typing import Any, Optional, Union

from crewai import LLM, Agent, Crew, CrewOutput, Task
from helpers import CrewAIEventListener, create_inputs_from_completion_params
from openai.types.chat import CompletionCreateParams
from ragas.messages import AIMessage


class MyAgent:
    """MyAgent is a custom agent that uses CrewAI to plan, write, and edit content.
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
        self.event_listener = CrewAIEventListener()

    def run(
        self, completion_create_params: CompletionCreateParams
    ) -> tuple[CrewOutput, list[Any]]:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Args:
            completion_create_params: The completion request parameters including input topic and settings.
        Returns:
            tuple[CrewOutput, list[Any]]: The crew output and list of events for agentic metrics.
        """
        # Example helper for extracting inputs as a json from the completion_create_params["messages"]
        # field with the 'user' role: (e.g. {"topic": "Artificial Intelligence"})
        inputs = create_inputs_from_completion_params(completion_create_params)

        # If inputs are a string, convert to a dictionary with 'topic' key for this example.
        if isinstance(inputs, str):
            inputs = {"topic": inputs}

        # Print commands may need flush=True to ensure they are displayed in real-time.
        print("Running agent with inputs:", inputs, flush=True)

        # Run the crew with the inputs
        crew_output = self.run_crew_agentic_workflow().kickoff(inputs=inputs)

        # Extract the response text from the crew output
        response_text = str(crew_output.raw)

        # Create a list of events from the event listener
        events = self.event_listener.messages
        if len(events) > 0:
            last_message = events[-1].content
            if last_message != response_text:
                events.append(AIMessage(content=response_text))
        else:
            events = None

        # The `events` variable is used to compute agentic metrics and guardrails
        # If you are not interested in these metrics, you can also return None instead.
        return crew_output, events

    def run_crew_agentic_workflow(self) -> Crew:
        """Creates and returns a Crew instance with defined agents and tasks."""
        return Crew(
            agents=[self.agent_planner, self.agent_writer, self.agent_editor],
            tasks=[self.task_plan, self.task_write, self.task_edit],
            verbose=self.verbose,
        )

    @property
    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use DataRobot's LLM Gateway or a specific deployment.

        For help configuring different LLM backends see:
        https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/developing-agents-llm-providers.md
        """
        if os.environ.get("LLM_DATAROBOT_DEPLOYMENT_ID"):
            return self.llm_with_datarobot_deployment
        else:
            return self.llm_with_datarobot_llm_gateway

    @property
    def agent_planner(self) -> Agent:
        return Agent(
            role="Content Planner",
            goal="Plan engaging and factually accurate content on {topic}",
            backstory="You're working on planning a blog article about the topic: {topic}. You collect "
            "information that helps the audience learn something and make informed decisions. Your work is "
            "the basis for the Content Writer to write an article on this topic.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm,
        )

    @property
    def agent_writer(self) -> Agent:
        return Agent(
            role="Content Writer",
            goal="Write insightful and factually accurate opinion piece about the topic: {topic}",
            backstory="You're working on writing a new opinion piece about the topic: {topic}. You base your writing "
            "on the work of the Content Planner, who provides an outline and relevant context about the topic. "
            "You follow the main objectives and direction of the outline, as provided by the Content Planner. "
            "You also provide objective and impartial insights and back them up with information provided by the "
            "Content Planner. You acknowledge in your opinion piece when your statements are opinions as opposed "
            "to objective statements.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm,
        )

    @property
    def agent_editor(self) -> Agent:
        return Agent(
            role="Editor",
            goal="Edit a given blog post to align with the writing style of the organization.",
            backstory="You are an editor who receives a blog post from the Content Writer. Your goal is to review "
            "the blog post to ensure that it follows journalistic best practices, provides balanced viewpoints "
            "when providing opinions or assertions, and also avoids major controversial topics or opinions when "
            "possible.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm,
        )

    @property
    def task_plan(self) -> Task:
        return Task(
            description=(
                "1. Prioritize the latest trends, key players, and noteworthy news on {topic}.\n"
                "2. Identify the target audience, considering their interests and pain points.\n"
                "3. Develop a detailed content outline including an introduction, key points, and a call to action.\n"
                "4. Include SEO keywords and relevant data or sources."
            ),
            expected_output="A comprehensive content plan document with an outline, audience analysis, SEO keywords, "
            "and resources.",
            agent=self.agent_planner,
        )

    @property
    def task_write(self) -> Task:
        return Task(
            description=(
                "1. Use the content plan to craft a compelling blog post on {topic}.\n"
                "2. Incorporate SEO keywords naturally.\n"
                "3. Sections/Subtitles are properly named in an engaging manner.\n"
                "4. Ensure the post is structured with an engaging introduction, insightful body, and a summarizing "
                "conclusion.\n"
                "5. Proofread for grammatical errors and alignment with the brand's voice.\n"
            ),
            expected_output="A well-written blog post in markdown format, ready for publication, each section should "
            "have 2 or 3 paragraphs.",
            agent=self.agent_writer,
        )

    @property
    def task_edit(self) -> Task:
        return Task(
            description=(
                "Proofread the given blog post for grammatical errors and alignment with the brand's voice."
            ),
            expected_output="A well-written blog post in markdown format, ready for publication, each section should "
            "have 2 or 3 paragraphs.",
            agent=self.agent_editor,
        )

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
    def llm_with_datarobot_llm_gateway(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use DataRobot's LLM Gateway.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        return LLM(
            model="datarobot/azure/gpt-4o-mini",
            api_base=self.api_base_litellm,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    @property
    def llm_with_datarobot_deployment(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use DataRobot's LLM Deployments.

        This property can serve as a primary LLM backend for the agents. You can optionally
        have multiple LLMs configured, such as one for DataRobot's LLM Gateway
        and another for a specific DataRobot deployment, or even multiple deployments or
        third-party LLMs.
        """
        deployment_url = f"{self.api_base}/deployments/{os.environ.get('LLM_DATAROBOT_DEPLOYMENT_ID')}/"
        return LLM(
            model="openai/gpt-4o-mini",
            api_base=deployment_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )
