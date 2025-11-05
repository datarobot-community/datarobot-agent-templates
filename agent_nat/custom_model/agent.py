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
from pathlib import Path
from typing import Any

from datarobot_genai.core.agents import (
    BaseAgent,
    InvokeReturn,
    default_usage_metrics,
)
from nat.runtime.loader import load_workflow
from nat.utils.type_utils import StrPath
from openai.types.chat import CompletionCreateParams


class MyAgent(BaseAgent):
    """MyAgent is a custom agent that uses NVIDIA NeMo Agent Toolkit and can be used for creating
    a custom agentic flow defined in workflow.yaml. It utilizes DataRobot's LLM Gateway or a
    specific deployment for language model interactions. This example illustrates 3 agents that
    handle content creation tasks, including planning, writing, and editing blog posts.
    """

    def __init__(
        self,
        **kwargs: Any,
    ):
        """Initializes the MyAgent class.

        Args:
            **kwargs: Any: Additional keyword arguments passed to the agent.
                Contains any parameters received in the CompletionCreateParams.

        Returns:
            None
        """

    async def invoke(
        self, completion_create_params: CompletionCreateParams
    ) -> InvokeReturn:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Args:
            completion_create_params: The completion request parameters including input topic and settings.
        Returns:

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

        # Get the config file path
        config_file = Path(__file__).parent / "workflow.yaml"

        # Create and invoke the NAT (Nemo Agent Toolkit) Agentic Workflow with the inputs
        result = await self.run_nat_workflow(config_file, user_prompt_content)

        # Create a list of events from the event listener
        events: list[Any]
        events = []  # This should be populated with the agent's events/messages

        usage_metrics = default_usage_metrics()
        pipeline_interactions = self.create_pipeline_interactions_from_events(events)

        return result, pipeline_interactions, usage_metrics

    async def run_nat_workflow(self, config_file: StrPath, input_str: str) -> str:
        """Run the NAT workflow with the provided config file and input string.

        Args:
            config_file: Path to the NAT workflow configuration file
            input_str: Input string to process through the workflow

        Returns:
            str: The result from the NAT workflow
        """
        async with load_workflow(config_file) as workflow:
            async with workflow.run(input_str) as runner:
                runner_outputs = await runner.result(to_type=str)

        line = f"{'-' * 50}"
        prefix = f"{line}\nWorkflow Result:\n"
        suffix = f"\n{line}"

        print(f"{prefix}{runner_outputs}{suffix}")

        return runner_outputs  # type: ignore[no-any-return]
