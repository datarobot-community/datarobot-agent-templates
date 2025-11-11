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
from typing import Any, Optional, Union

from config import Config
from datarobot_genai.core.agents import (
    BaseAgent,
    InvokeReturn,
    UsageMetrics,
    default_usage_metrics,
    extract_user_prompt_content,
    is_streaming,
)
from openai.types.chat import CompletionCreateParams


class MyAgent(BaseAgent[None]):
    """MyAgent is a generic base class that can be used for creating a custom agentic flow. This template
    implements the minimum required methods and attributes to function as a DataRobot agent.
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
        self.model = model

    async def invoke(
        self, completion_create_params: CompletionCreateParams
    ) -> InvokeReturn:
        """Run the agent with the provided completion parameters.

        [THIS METHOD IS REQUIRED FOR THE AGENT TO WORK WITH DRUM SERVER]

        Args:
            completion_create_params: The completion request parameters including input topic and settings.
        Returns:
            Union[
                AsyncGenerator[tuple[str, Any | None, dict[str, int]], None],
                tuple[str, Any | None, dict[str, int]],
            ]: For streaming requests, returns a generator yielding tuples of (response_text, pipeline_interactions, usage_metrics).
               For non-streaming requests, returns a single tuple of (response_text, pipeline_interactions, usage_metrics).
        """
        # Retrieve the starting user prompt from the CompletionCreateParams
        user_prompt_content = extract_user_prompt_content(completion_create_params)

        # Print commands may need flush=True to ensure they are displayed in real-time.
        print("Running agent with user prompt:", user_prompt_content, flush=True)

        usage_metrics: UsageMetrics = default_usage_metrics()

        # The following code demonstrate both a synchronous and streaming response.
        # You can choose one or the other based on your use case, they function the same.
        # The main difference is returning a generator for streaming or a final response for sync.
        if is_streaming(completion_create_params):
            # Streaming response: yield each message as it is generated
            async def stream_generator() -> InvokeReturn:
                # -----------------------------------------------------------
                # Here you would implement the streaming logic of your agent using the inputs.
                # -----------------------------------------------------------
                yield "streaming success", None, usage_metrics

                # Create a list of events from the event listener
                events: list[
                    Any
                ] = []  # This should be populated with the agent's events/messages

                pipeline_interactions = self.create_pipeline_interactions_from_events(
                    events
                )

                # Final response after streaming is complete
                yield "", pipeline_interactions, usage_metrics

            return stream_generator()
        else:
            # -----------------------------------------------------------
            # Here you would implement the logic of your agent using the inputs.
            # -----------------------------------------------------------
            response_text = "success"

            # Create a list of events from the event listener
            events: list[
                Any
            ] = []  # This should be populated with the agent's events/messages

            pipeline_interactions = self.create_pipeline_interactions_from_events(
                events
            )

            return response_text, pipeline_interactions, usage_metrics
