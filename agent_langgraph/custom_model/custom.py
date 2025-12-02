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
# isort: off
from helpers_telemetry import *  # noqa # pylint: disable=unused-import
import os

# Some libraries collect telemetry data by default. Let's disable that.
os.environ["RAGAS_DO_NOT_TRACK"] = "true"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
# isort: on

from agent import MyAgent
from auth import initialize_authorization_context
from datarobot_drum import RuntimeParameters
from helpers import (
    CustomModelChatResponse,
    to_custom_model_response,
)
from openai.types.chat import CompletionCreateParams


def maybe_set_env_from_runtime_parameters(key: str) -> None:
    """
    Set an environment variable from a runtime parameter if it exists.

    In local development, the runtime parameters are not available, and environment variable
    is set from the .env file, so it's safe to ignore the exception.
    """
    RUNTIME_PARAMETER_PLACEHOLDER_VALUE = "SET_VIA_PULUMI_OR_MANUALLY"
    try:
        runtime_parameter_value = RuntimeParameters.get(key)
        if (
            runtime_parameter_value
            and len(runtime_parameter_value) > 0
            and runtime_parameter_value != RUNTIME_PARAMETER_PLACEHOLDER_VALUE
        ):
            os.environ[key] = runtime_parameter_value
    except ValueError:
        pass


def load_model(code_dir: str) -> str:
    """The agent is instantiated in this function and returned."""
    _ = code_dir
    return "success"


def chat(
    completion_create_params: CompletionCreateParams,
    model: str,
) -> CustomModelChatResponse:
    """When using the chat endpoint, this function is called.

    Agent inputs are in OpenAI message format and defined as the 'user' portion
    of the input prompt.

    Example:
        prompt = {
            "topic": "Artificial Intelligence",
        }
        client = OpenAI(...)
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{json.dumps(prompt)}"},
            ],
            extra_body = {
                "environment_var": True,
            },
            ...
        )
    """
    _ = model

    # Initialize the authorization context for downstream agents and tools to retrieve
    # access tokens for external services.
    initialize_authorization_context(completion_create_params)

    maybe_set_env_from_runtime_parameters("LLM_DATAROBOT_DEPLOYMENT_ID")

    # Instantiate the agent, all fields from the completion_create_params are passed to the agent
    # allowing environment variables to be passed during execution
    agent = MyAgent(**completion_create_params)

    # Execute the agent with the inputs
    agent_result = agent.run(completion_create_params=completion_create_params)

    return to_custom_model_response(
        *agent_result, model=completion_create_params["model"]
    )
