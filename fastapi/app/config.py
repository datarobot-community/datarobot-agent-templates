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
from core.config import DataRobotAppFrameworkBaseSettings
from core.telemetry.logging import FormatType, LogLevel


class Config(DataRobotAppFrameworkBaseSettings):
    session_secret_key: str
    session_max_age: int = 14 * 24 * 60 * 60  # 14 days, in seconds
    session_https_only: bool = True
    session_cookie_name: str = "sess"  # Can be overridden for different apps
    agent_langgraph_deployment_id: str = ""

    log_level: LogLevel = LogLevel.INFO
    log_format: FormatType = "json"
