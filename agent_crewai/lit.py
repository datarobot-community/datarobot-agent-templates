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

import chainlit as cl
from openai import AsyncOpenAI

from custom_model.config import Config

config = Config()

client = AsyncOpenAI(base_url=config.agent_endpoint, api_key="empty")


@cl.on_chat_start  # type: ignore[misc]
def start_chat() -> None:
    cl.user_session.set(
        "message_history",
        [],
    )


@cl.on_message  # type: ignore[misc]
async def on_message(message: cl.Message) -> None:
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")

    stream = await client.chat.completions.create(
        messages=message_history,
        stream=True,
        model="datarobot/azure/gpt-4o-mini",
    )
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
