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
from typing import Any, Generator, Optional, Union

from openai.types.chat import CompletionCreateParams
from ragas import MultiTurnSample


class MyAgent:
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
        self.api_key = api_key or os.environ.get("DATAROBOT_API_TOKEN")
        self.api_base = api_base or os.environ.get("DATAROBOT_ENDPOINT")
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

        usage_metrics = {
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

    @property
    def llm(self) -> Any:
        """The LLM property should return an instance of the LLM client being used by the agent.

        For help configuring different LLM backends see:
        https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/developing-agents-llm-providers.md
        """
        return None

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

    @staticmethod
    def create_pipeline_interactions_from_events(
        events: list[Any],
    ) -> MultiTurnSample | None:
        """Convert a list of events into a MultiTurnSample.

        Creates the pipeline interactions for moderations and evaluation
        (e.g. Task Adherence, Agent Goal Accuracy, Tool Call Accuracy)
        """
        if not events:
            return None
        return MultiTurnSample(user_input=events)
