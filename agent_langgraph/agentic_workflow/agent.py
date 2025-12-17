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
from datetime import datetime
from typing import Any

from config import Config
from datarobot_genai.core.agents import (
    make_system_prompt,
)
from datarobot_genai.langgraph.agent import LangGraphAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_litellm.chat_models import ChatLiteLLM
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent

config = Config()


class MyAgent(LangGraphAgent):
    """MyAgent is a custom agent that uses Langgraph to plan, write, and edit content.
    It utilizes DataRobot's LLM Gateway or a specific deployment for language model interactions.
    This example illustrates 3 agents that handle content creation tasks, including planning, writing,
    and editing blog posts.
    """

    @property
    def workflow(self) -> StateGraph[MessagesState]:
        langgraph_workflow = StateGraph[
            MessagesState, None, MessagesState, MessagesState
        ](MessagesState)
        langgraph_workflow.add_node("planner_node", self.agent_planner)
        langgraph_workflow.add_node("writer_node", self.agent_writer)
        langgraph_workflow.add_edge(START, "planner_node")
        langgraph_workflow.add_edge("planner_node", "writer_node")
        langgraph_workflow.add_edge("writer_node", END)
        return langgraph_workflow  # type: ignore[return-value]

    @property
    def prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "user",
                    f"The topic is {{topic}}. Make sure you find any interesting and relevant information given the current year is {datetime.now().year}.",
                ),
            ]
        )

    def llm(
        self,
        preferred_model: str | None = None,
        auto_model_override: bool = True,
    ) -> ChatLiteLLM:
        """Returns the ChatLiteLLM to use for a given model.

        If a `preferred_model` is provided, it will be used. Otherwise, the default model will be used.
        If auto_model_override is True, it will try and use the model specified in the request
        but automatically back out to the default model if the LLM Gateway is not configured

        Args:
            preferred_model: Optional[str]: The model to use. If none, it defaults to config.llm_default_model.
            auto_model_override: Optional[bool]: If True, it will try and use the model
                specified in the request but automatically back out if the LLM Gateway is
                not available.

        Returns:
            ChatLiteLLM: The model to use.
        """
        api_base = self.litellm_api_base(config.llm_deployment_id)
        model = preferred_model
        if preferred_model is None:
            model = config.llm_default_model
        if auto_model_override and not config.use_datarobot_llm_gateway:
            model = config.llm_default_model
        if self.verbose:
            print(f"Using model: {model}")
        return ChatLiteLLM(
            model=model,
            api_base=api_base,
            api_key=self.api_key,
            timeout=self.timeout,
            streaming=True,
            max_retries=3,
        )

    @property
    def agent_planner(self) -> Any:
        return create_react_agent(
            self.llm(preferred_model="datarobot/azure/gpt-5-mini-2025-08-07"),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are a content planner. You are working with a content writer colleague.\n"
                "You're working on planning a blog article about the topic. You collect information that helps the "
                "audience learn something and make informed decisions. Your work is the basis for the Content Writer "
                "to write an article on this topic. Keep your plan focused and concise - don't overthink it. "
                "This is a simple example task."
                "\n"
                "1. Prioritize the latest trends, key players, and noteworthy news on the topic.\n"
                "2. Identify the target audience, considering their interests and pain points.\n"
                "3. Develop a detailed content outline including an introduction, key points, and a call to action.\n"
                "4. Include SEO keywords and relevant data or sources."
                "\n"
                "Plan engaging and factually accurate content on the topic. You must create a concise content "
                "plan document with an outline, audience analysis, SEO keywords, and resources. Keep it brief and "
                "to the point.",
            ),
            name="Planner Agent",
        )

    @property
    def agent_writer(self) -> Any:
        return create_react_agent(
            self.llm(preferred_model="datarobot/azure/gpt-5-mini-2025-08-07"),
            tools=self.mcp_tools,
            prompt=make_system_prompt(
                "You are a content writer. You are working with a planner colleague.\n"
                "You're working on writing a new opinion piece about the topic. You base your writing on the work "
                "of the Content Planner, who provides an outline and relevant context about the topic. You follow "
                "the main objectives and direction of the outline, as provided by the Content Planner. You also "
                "provide objective and impartial insights and back them up with information provided by the Content "
                "Planner. You acknowledge in your opinion piece when your statements are opinions as opposed to "
                "objective statements. IMPORTANT: Keep your output concise and under 500 words total. Don't overthink - "
                "this is a simple example task.\n"
                "1. Use the content plan to craft a compelling blog post.\n"
                "2. Incorporate SEO keywords naturally.\n"
                "3. Sections/Subtitles are properly named in an engaging manner.\n"
                "4. Ensure the post is structured with an engaging introduction, insightful body, and a summarizing "
                "conclusion.\n"
                "5. Proofread for grammatical errors and alignment with the brand's voice.\n"
                "6. CRITICAL: Keep the total output under 500 words. Be concise and don't overthink it.\n"
                "Write a concise, insightful opinion piece about the topic. You must create a "
                "well-written blog post in markdown format, ready for publication. Maximum 500 words total. "
                "Each section should have 1-2 brief paragraphs.",
            ),
            name="Writer Agent",
        )
