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
import json
import os
import time
import uuid
from typing import Any, Generator, Iterator, Optional, Union, cast

import datarobot as dr
import openai
import pandas as pd
from datarobot.models.genai.agent.auth import (
    get_authorization_context,
    set_authorization_context,
)
from datarobot_predict.deployment import (
    PredictionResult,
    UnstructuredPredictionResult,
    predict,
    predict_unstructured,
)
from openai.types import CompletionCreateParams, CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsNonStreaming,
    CompletionCreateParamsStreaming,
)


class CustomModelChatResponse(ChatCompletion):
    pipeline_interactions: str | None = None


class CustomModelStreamingResponse(ChatCompletionChunk):
    pipeline_interactions: str | None = None


def to_custom_model_chat_response(
    response_text: str,
    pipeline_interactions: Optional[Any],
    usage_metrics: dict[str, int],
    model: Optional[str] = None,
) -> CustomModelChatResponse:
    """Convert the OpenAI ChatCompletion response to CustomModelChatResponse."""
    from openai.types.chat.chat_completion import Choice

    # Convert the text of the agent response into a chat completion response
    choice = Choice(
        index=0,
        message=ChatCompletionMessage(role="assistant", content=response_text),
        finish_reason="stop",
    )

    return CustomModelChatResponse(
        id=str(uuid.uuid4()),  # Create a unique completion id
        object="chat.completion",
        choices=[choice],
        created=int(time.time()),  # ChatCompletion created time should be an integer
        model=model,
        usage=CompletionUsage(**usage_metrics),
        pipeline_interactions=pipeline_interactions.model_dump_json()
        if pipeline_interactions
        else None,
    )


def to_custom_model_streaming_response(
    streaming_response_generator: Generator[
        tuple[str, Any | None, dict[str, int]], None, None
    ],
    model: Optional[str] = None,
) -> Iterator[CustomModelStreamingResponse]:
    """Convert the OpenAI ChatCompletionChunk response to CustomModelStreamingResponse."""
    from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

    completion_id = str(uuid.uuid4())
    created = int(time.time())

    last_pipeline_interactions = None
    last_usage_metrics = None

    for (
        response_text,
        pipeline_interactions,
        usage_metrics,
    ) in streaming_response_generator:
        last_pipeline_interactions = pipeline_interactions
        last_usage_metrics = usage_metrics

        if response_text:
            choice = Choice(
                index=0,
                delta=ChoiceDelta(role="assistant", content=response_text),
                finish_reason=None,
            )
            yield CustomModelStreamingResponse(
                id=completion_id,
                object="chat.completion.chunk",
                created=created,
                model=model,
                choices=[choice],
                usage=CompletionUsage(**usage_metrics) if usage_metrics else None,
            )

    # Yield final chunk indicating end of stream
    choice = Choice(
        index=0,
        delta=ChoiceDelta(role="assistant"),
        finish_reason="stop",
    )
    yield CustomModelStreamingResponse(
        id=completion_id,
        object="chat.completion.chunk",
        created=created,
        model=model,
        choices=[choice],
        usage=CompletionUsage(**last_usage_metrics) if last_usage_metrics else None,
        pipeline_interactions=last_pipeline_interactions.model_dump_json()
        if last_pipeline_interactions
        else None,
    )


def initialize_authorization_context(
    completion_create_params: CompletionCreateParams
    | CompletionCreateParamsNonStreaming
    | CompletionCreateParamsStreaming,
) -> None:
    """Sets the authorization context for the agent.

    Authorization context is required for propagating information needed by downstream
    agents and tools to retrieve access tokens to connect to external services. When set,
    authorization context will be automatically propagated when using ToolClient class.
    """
    # Note: authorization context internally uses contextvars, which are
    # thread-safe and async-safe.
    authorization_context = completion_create_params.get("authorization_context", {})
    set_authorization_context(cast(dict[str, Any], authorization_context))


class ToolClient:
    """Client for interacting with Agent Tools Deployments.

    This class provides methods to call the custom model tool using various hooks:
    `score`, `score_unstructured`, and `chat`. When the `authorization_context` is set,
    the client automatically propagates it to the agent tool. The `authorization_context`
    is required for retrieving access tokens to connect to external services.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the ToolClient.

        Args:
            api_key (Optional[str]): API key for authentication. Defaults to environment variable `DATAROBOT_API_TOKEN`.
            base_url (Optional[str]): Base URL for the DataRobot API. Defaults to environment variable `DATAROBOT_ENDPOINT`.
        """
        self.api_key = api_key or os.getenv("DATAROBOT_API_TOKEN")
        base_url = (
            cast(
                str,
                (
                    base_url
                    or os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com")
                ),
            )
            .rstrip("/")
            .removesuffix("/api/v2")
        )
        self.base_url = base_url

    @property
    def datarobot_api_endpoint(self) -> str:
        return self.base_url + "/api/v2"

    def get_deployment(self, deployment_id: str) -> dr.Deployment:
        """Retrieve a deployment by its ID.

        Args:
            deployment_id (str): The ID of the deployment.

        Returns:
            dr.Deployment: The deployment object.
        """
        dr.Client(self.api_key, self.datarobot_api_endpoint)
        return dr.Deployment.get(deployment_id=deployment_id)

    def call(
        self, deployment_id: str, payload: dict[str, Any], **kwargs: Any
    ) -> UnstructuredPredictionResult:
        """Run the custom model tool using score_unstructured hook.

        Args:
            deployment_id (str): The ID of the deployment.
            payload (dict[str, Any]): The input payload.
            **kwargs: Additional keyword arguments.

        Returns:
            UnstructuredPredictionResult: The response content and headers.
        """
        data = {
            "payload": payload,
            "authorization_context": get_authorization_context(),
        }
        return predict_unstructured(
            deployment=self.get_deployment(deployment_id),
            data=json.dumps(data),
            content_type="application/json",
            **kwargs,
        )

    def score(
        self, deployment_id: str, data_frame: pd.DataFrame, **kwargs: Any
    ) -> PredictionResult:
        """Run the custom model tool using score hook.

        Args:
            deployment_id (str): The ID of the deployment.
            data_frame (pd.DataFrame): The input data frame.
            **kwargs: Additional keyword arguments.

        Returns:
            PredictionResult: The response content and headers.
        """
        return predict(
            deployment=self.get_deployment(deployment_id),
            data_frame=data_frame,
            **kwargs,
        )

    def chat(
        self,
        completion_create_params: CompletionCreateParams,
        model: str,
    ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
        """Run the custom model tool with the chat hook.

        Args:
            completion_create_params (CompletionCreateParams): Parameters for the chat completion.
            model (str): The model to use.

        Returns:
            Union[ChatCompletion, Iterator[ChatCompletionChunk]]: The chat completion response.
        """
        extra_body = {
            "authorization_context": get_authorization_context(),
        }
        return openai.chat.completions.create(
            **completion_create_params,
            model=model,
            extra_body=extra_body,
        )
