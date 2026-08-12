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

from typing import Any, cast

from datarobot.models.genai.agent.auth import set_authorization_context
from openai.types.chat import CompletionCreateParams


def initialize_authorization_context(
    completion_create_params: CompletionCreateParams,
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
