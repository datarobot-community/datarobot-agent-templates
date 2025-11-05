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
"""
All configuration for the agent application. The config class handles
loading variables from environment, .env files, Pulumi outputs, and
DataRobot credentials automatically.
"""

from typing import Any
from urllib.parse import urlparse

from datarobot.core.config import DataRobotAppFrameworkBaseSettings
from pydantic import Field, model_validator


class Config(DataRobotAppFrameworkBaseSettings):
    """
    This class finds variables in the priority order of: env
    variables (including Runtime Parameters), .env, file_secrets, then
    Pulumi output variables.
    """

    llm_deployment_id: str | None = None
    llm_default_model: str = "datarobot/azure/gpt-4o-mini"
    use_datarobot_llm_gateway: bool = False
    mcp_deployment_id: str | None = None
    external_mcp_url: str | None = None

    agent_endpoint: str = Field(
        default="http://localhost:8842", validation_alias="AGENT_NAT_ENDPOINT"
    )

    @property
    def local_dev_port(self) -> int:
        parsed_url = urlparse(self.agent_endpoint)
        if parsed_url.port:
            return parsed_url.port
        raise ValueError(f"No port in {self.agent_endpoint}")

    @model_validator(mode="before")
    @classmethod
    def replace_placeholder_values(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field_name, field_info in cls.model_fields.items():
                if data.get(field_name) == "SET_VIA_PULUMI_OR_MANUALLY":
                    data[field_name] = field_info.default
        return data
