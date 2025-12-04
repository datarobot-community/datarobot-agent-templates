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
# ------------------------------------------------------------------------------
# THIS SECTION OF CODE IS REQUIRED TO SETUP TRACING AND TELEMETRY FOR THE AGENTS.
# REMOVING THIS CODE WILL DISABLE ALL MONITORING, TRACING AND TELEMETRY.
# isort: off
from datarobot_genai.core.telemetry_agent import instrument

instrument(framework="langgraph")
# ruff: noqa: E402
from agent import MyAgent
from config import Config

# isort: on
# ------------------------------------------------------------------------------
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, AsyncGenerator, Iterator, Union

from datarobot.models.genai.agent.auth import (
    get_authorization_context,
    set_authorization_context,
)
from datarobot_genai.core.chat import (
    CustomModelChatResponse,
    CustomModelStreamingResponse,
    initialize_authorization_context,
    to_custom_model_chat_response,
    to_custom_model_streaming_response,
)
from openai.types.chat import CompletionCreateParams
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsNonStreaming,
    CompletionCreateParamsStreaming,
)


def load_model(code_dir: str) -> tuple[ThreadPoolExecutor, asyncio.AbstractEventLoop]:
    """The agent is instantiated in this function and returned."""
    thread_pool_executor = ThreadPoolExecutor(1)
    event_loop = asyncio.new_event_loop()
    thread_pool_executor.submit(asyncio.set_event_loop, event_loop).result()
    return (thread_pool_executor, event_loop)


def chat(
    completion_create_params: CompletionCreateParams
    | CompletionCreateParamsNonStreaming
    | CompletionCreateParamsStreaming,
    load_model_result: tuple[ThreadPoolExecutor, asyncio.AbstractEventLoop],
    **kwargs: Any,
) -> Union[CustomModelChatResponse, Iterator[CustomModelStreamingResponse]]:
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
    thread_pool_executor, event_loop = load_model_result

    # Change working directory to the directory containing this file.
    # Some agent frameworks expect this for expected pathing.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load MCP runtime parameters and session secret if configured
    # ["EXTERNAL_MCP_URL", "MCP_DEPLOYMENT_ID", "SESSION_SECRET_KEY"]
    _ = Config()

    # Initialize the authorization context for downstream agents and tools to retrieve
    # access tokens for external services.
    initialize_authorization_context(completion_create_params, **kwargs)

    # Get the authorization context from the main thread to propagate to the worker thread
    # ContextVars are thread-local, so we need to set it in the worker thread
    try:
        auth_context = get_authorization_context()
    except LookupError:
        auth_context = {}

    # Instantiate the agent, all fields from the completion_create_params are passed to the agent
    # allowing environment variables to be passed during execution
    agent = MyAgent(**completion_create_params)

    # Invoke the agent and check if it returns a generator or a tuple
    # Set the authorization context in the worker thread before invoking the agent
    def invoke_with_auth_context():  # type: ignore[no-untyped-def]
        try:
            set_authorization_context(auth_context)
        except AttributeError:
            pass

        return event_loop.run_until_complete(
            agent.invoke(completion_create_params=completion_create_params)
        )

    result = thread_pool_executor.submit(invoke_with_auth_context).result()

    # Check if the result is a generator (streaming response)
    if isinstance(result, AsyncGenerator):
        # Streaming response
        return to_custom_model_streaming_response(
            thread_pool_executor,
            event_loop,
            result,
            model=completion_create_params.get("model"),
        )
    else:
        # Non-streaming response
        response_text, pipeline_interactions, usage_metrics = result

        return to_custom_model_chat_response(
            response_text,
            pipeline_interactions,
            usage_metrics,
            model=completion_create_params.get("model"),
        )
