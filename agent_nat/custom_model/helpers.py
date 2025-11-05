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

import time
import traceback as tb
import uuid
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Iterator

from datarobot_genai.core.agents import default_usage_metrics
from datarobot_genai.core.chat import CustomModelStreamingResponse
from openai.types import CompletionUsage
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from ragas import MultiTurnSample


def to_custom_model_streaming_response(
    thread_pool_executor: ThreadPoolExecutor,
    event_loop: AbstractEventLoop,
    streaming_response_generator: AsyncGenerator[
        tuple[str, MultiTurnSample | None, dict[str, int]], None
    ],
    model: str | object | None,
) -> Iterator[CustomModelStreamingResponse]:
    """Convert the OpenAI ChatCompletionChunk response to CustomModelStreamingResponse."""
    completion_id = str(uuid.uuid4())
    created = int(time.time())

    last_pipeline_interactions = None
    last_usage_metrics = None

    if model is None:
        model = "unspecified-model"
    else:
        model = str(model)

    required_usage_metrics = default_usage_metrics()
    try:
        agent_response = streaming_response_generator.__aiter__()
        while True:
            try:
                (
                    response_text,
                    pipeline_interactions,
                    usage_metrics,
                ) = thread_pool_executor.submit(
                    event_loop.run_until_complete, agent_response.__anext__()
                ).result()
                last_pipeline_interactions = pipeline_interactions
                last_usage_metrics = usage_metrics

                if response_text:
                    choice = ChunkChoice(
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
                        usage=CompletionUsage.model_validate(
                            required_usage_metrics | usage_metrics
                        )
                        if usage_metrics
                        else None,
                    )
            except StopAsyncIteration:
                break
        # Yield final chunk indicating end of stream
        choice = ChunkChoice(
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
            usage=CompletionUsage.model_validate(
                required_usage_metrics | last_usage_metrics
            )
            if last_usage_metrics
            else None,
            pipeline_interactions=last_pipeline_interactions.model_dump_json()
            if last_pipeline_interactions
            else None,
        )
    except Exception as e:
        tb.print_exc()
        created = int(time.time())
        choice = ChunkChoice(
            index=0,
            delta=ChoiceDelta(role="assistant", content=str(e), refusal="error"),
            finish_reason="stop",
        )
        yield CustomModelStreamingResponse(
            id=completion_id,
            object="chat.completion.chunk",
            created=created,
            model=model,
            choices=[choice],
            usage=None,
        )
