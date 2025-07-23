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

from contextvars import ContextVar
from typing import Any, cast

from openai.types.chat import CompletionCreateParams

authorization_context_var: ContextVar[dict[str, Any]] = ContextVar(
    "authorization_context"
)


def initialize_authorization_context(
    completion_create_params: CompletionCreateParams,
) -> None:
    """Sets the authorization context for the agent.

    Authorization context is required for propagating information needed by downstream
    agents and tools to retrieve access tokens to connect to external services. When set,
    authorization context will be automatically propagated when using ToolClient class.
    """
    authorization_context = completion_create_params.get("authorization_context", {})
    set_authorization_context(cast(dict[str, Any], authorization_context))


def set_authorization_context(authorization_context: dict[str, Any]) -> None:
    authorization_context_var.set(authorization_context)


def get_authorization_context() -> dict[str, Any]:
    return authorization_context_var.get()
