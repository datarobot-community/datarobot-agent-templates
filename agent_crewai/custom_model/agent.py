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
from typing import Any, Dict, Optional, Union

from crewai import LLM, Agent, Crew, CrewOutput, Task


class MyAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        verbose: Optional[Union[bool, str]] = True,
        **kwargs: Any,
    ):
        self.api_key = api_key or os.environ.get("DATAROBOT_API_TOKEN")
        self.api_base = api_base or os.environ.get("DATAROBOT_ENDPOINT")
        self.model = model
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    @property
    def llm_with_datarobot_llm_gateway(self) -> LLM:
        return LLM(
            model="datarobot/vertex_ai/gemini-1.5-flash-002",
            clientId="custom-model",
            api_base=self.api_base,
            api_key=self.api_key,
        )

    @property
    def llm_with_datarobot_deployment(self) -> LLM:
        return LLM(
            model="datarobot/vertex_ai/gemini-1.5-flash-002",
            api_base=f"{self.api_base}/api/v2/deployments/{os.environ.get('LLM_DEPLOYMENT_ID')}/",
            api_key=self.api_key,
        )

    @property
    def agent_planner(self) -> Agent:
        return Agent(
            role="Content Planner",
            goal="Plan engaging and factually accurate content on {topic}",
            backstory="You're working on planning a blog article "
            "about the topic: {topic}."
            "You collect information that helps the "
            "audience learn something "
            "and make informed decisions. "
            "Your work is the basis for "
            "the Content Writer to write an article on this topic.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm_with_datarobot_llm_gateway,
        )

    @property
    def agent_writer(self) -> Agent:
        return Agent(
            role="Content Writer",
            goal="Write insightful and factually accurate opinion piece "
            "about the topic: {topic}",
            backstory="You're working on a writing "
            "a new opinion piece about the topic: {topic}. "
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
            "as opposed to objective statements.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm_with_datarobot_llm_gateway,
        )

    @property
    def agent_editor(self) -> Agent:
        return Agent(
            role="Editor",
            goal="Edit a given blog post to align with the writing style "
            "of the organization. ",
            backstory="You are an editor who receives a blog post "
            "from the Content Writer. "
            "Your goal is to review the blog post "
            "to ensure that it follows journalistic best practices,"
            "provides balanced viewpoints "
            "when providing opinions or assertions, "
            "and also avoids major controversial topics "
            "or opinions when possible.",
            allow_delegation=False,
            verbose=self.verbose,
            llm=self.llm_with_datarobot_llm_gateway,
        )

    @property
    def task_plan(self) -> Task:
        return Task(
            description=(
                "1. Prioritize the latest trends, key players, "
                "and noteworthy news on {topic}.\n"
                "2. Identify the target audience, considering "
                "their interests and pain points.\n"
                "3. Develop a detailed content outline including "
                "an introduction, key points, and a call to action.\n"
                "4. Include SEO keywords and relevant data or sources."
            ),
            expected_output="A comprehensive content plan document "
            "with an outline, audience analysis, "
            "SEO keywords, and resources.",
            agent=self.agent_planner,
        )

    @property
    def task_write(self) -> Task:
        return Task(
            description=(
                "1. Use the content plan to craft a compelling "
                "blog post on {topic}.\n"
                "2. Incorporate SEO keywords naturally.\n"
                "3. Sections/Subtitles are properly named "
                "in an engaging manner.\n"
                "4. Ensure the post is structured with an "
                "engaging introduction, insightful body, "
                "and a summarizing conclusion.\n"
                "5. Proofread for grammatical errors and "
                "alignment with the brand's voice.\n"
            ),
            expected_output="A well-written blog post "
            "in markdown format, ready for publication, "
            "each section should have 2 or 3 paragraphs.",
            agent=self.agent_writer,
        )

    @property
    def task_edit(self) -> Task:
        return Task(
            description=(
                "Proofread the given blog post for grammatical errors "
                "and alignment with the brand's voice."
            ),
            expected_output="A well-written blog post in markdown format, "
            "ready for publication, "
            "each section should have 2 or 3 paragraphs.",
            agent=self.agent_editor,
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[self.agent_planner, self.agent_writer, self.agent_editor],
            tasks=[self.task_plan, self.task_write, self.task_edit],
            verbose=self.verbose,
        )

    def run(self, inputs: Dict[str, str]) -> CrewOutput:
        # This crew uses one input which is a dictionary with the topic
        # Example: {"topic": "Artificial Intelligence"}
        return self.crew().kickoff(inputs=inputs)
