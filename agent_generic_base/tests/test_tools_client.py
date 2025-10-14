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
from unittest.mock import patch

import pytest
from helpers import ToolClient

application_base_url = "https://example.com"


@pytest.mark.parametrize(
    "base_url",
    [
        f"{application_base_url}/api/v2",
        f"{application_base_url}/api/v2/",
        f"{application_base_url}",
        f"{application_base_url}/",
    ],
)
@pytest.mark.parametrize("api_key", ["test-api-key"])
def test_tool_client_config(base_url, api_key):
    def _assert(tool_client):
        assert tool_client.api_key == api_key
        assert tool_client.base_url == application_base_url
        assert tool_client.datarobot_api_endpoint == f"{application_base_url}/api/v2"

    _assert(ToolClient(api_key=api_key, base_url=base_url))

    overrides = {"DATAROBOT_API_TOKEN": api_key, "DATAROBOT_ENDPOINT": base_url}
    with patch.dict(os.environ, overrides, clear=True):
        _assert(ToolClient())


def test_tool_client_config_defaults():
    tool_client = ToolClient()
    assert tool_client.api_key is None
    assert tool_client.base_url == "https://app.datarobot.com"
    assert tool_client.datarobot_api_endpoint == "https://app.datarobot.com/api/v2"
