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
from typing import Optional

from .kernel import Kernel


class Environment:
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_token = os.environ.get("DATAROBOT_API_TOKEN") or api_token
        self.base_url = (
            os.environ.get("DATAROBOT_ENDPOINT")
            or base_url
            or "https://app.datarobot.com"
        )
        self.base_url = self.base_url.replace("/api/v2", "")

    @property
    def interface(self) -> Kernel:
        return Kernel(
            api_token=str(self.api_token),
            base_url=str(self.base_url),
        )
