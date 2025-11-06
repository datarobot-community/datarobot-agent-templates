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
from typing import Any, List, Optional, Union

from config import Config
from crewai import LLM, Agent, Task
from crewai_event_listener import CrewAIEventListener
from datarobot_genai.crewai.agent import (
    build_llm,
)
from datarobot_genai.crewai.base import CrewAIAgent


class MyAgent(CrewAIAgent):
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
        self.event_listener = CrewAIEventListener()

    def llm(
        self,
        preferred_model: str | None = None,
        auto_model_override: bool = True,
    ) -> LLM:
        """Returns the LLM to use for a given model.

        If a `preferred_model` is provided, it will be used. Otherwise, the default model will be used.
        If auto_model_override is True, it will try and use the model specified in the request
        but automatically back out to the default model if the LLM Gateway is not configured

        Args:
            preferred_model: Optional[str]: The model to use. If none, it defaults to config.llm_default_model.
            auto_model_override: Optional[bool]: If True, it will try and use the model
                specified in the request but automatically back out if the LLM Gateway is
                not available.

        Returns:
            LLM: The model to use.
        """
        model = preferred_model or self.default_model
        if auto_model_override and not self.config.use_datarobot_llm_gateway:
            model = self.default_model
        if self.verbose:
            print(f"Using model: {model}")
        return build_llm(
            api_base=self.api_base,
            api_key=self.api_key,
            model=model,
            deployment_id=self.config.llm_deployment_id,
            timeout=self.timeout,
        )

    def make_kickoff_inputs(self, user_prompt_content: str) -> dict[str, Any]:
        """Map the user prompt into Crew kickoff inputs expected by tasks/agents."""
        return {"topic": str(user_prompt_content)}

    @property
    def agents(self) -> List[Agent]:
        return [self.agent_planner, self.agent_writer, self.agent_editor]

    @property
    def tasks(self) -> List[Task]:
        return [self.task_plan, self.task_write, self.task_edit]

    @property
    def agent_planner(self) -> Agent:
        """Content Planner agent."""
        return Agent(
            role="Planner",
            goal="Plan engaging and factually accurate content on {topic}",
            backstory="You're working on planning a blog article about the topic: {topic}. You collect "
            "information that helps the audience learn something and make informed decisions. Your work is "
            "the basis for the Content Writer to write an article on this topic.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm(preferred_model="datarobot/azure/gpt-4o-mini"),
            tools=self._mcp_tools,
        )

    @property
    def agent_writer(self) -> Agent:
        """Content Writer agent."""
        return Agent(
            role="Writer",
            goal="Write insightful and factually accurate opinion piece about the topic: {topic}",
            backstory="You're working on writing a new opinion piece about the topic: {topic}. You base your writing "
            "on the work of the Content Planner, who provides an outline and relevant context about the topic. "
            "You follow the main objectives and direction of the outline, as provided by the Content Planner. "
            "You also provide objective and impartial insights and back them up with information provided by the "
            "Content Planner. You acknowledge in your opinion piece when your statements are opinions as opposed "
            "to objective statements.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm(preferred_model="datarobot/azure/gpt-4o-mini"),
            tools=self._mcp_tools,
        )

    @property
    def agent_editor(self) -> Agent:
        """Editor agent."""
        return Agent(
            role="Editor",
            goal="Edit a given blog post to align with the writing style of the organization.",
            backstory="You are an editor who receives a blog post from the Content Writer. Your goal is to review "
            "the blog post to ensure that it follows journalistic best practices, provides balanced viewpoints "
            "when providing opinions or assertions, and also avoids major controversial topics or opinions when "
            "possible.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm(),
            tools=self._mcp_tools,
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
