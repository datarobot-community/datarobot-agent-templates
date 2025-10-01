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
from unittest.mock import MagicMock, patch

import pytest

from cli import Environment, Kernel


class TestEnvironment:
    def test_init_default_values(self):
        """Test initialization with default values."""
        # Clear environment variables to test default behavior
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                Environment()

    def test_init_with_parameters(self):
        """Test initialization with explicitly provided parameters."""
        with patch.dict(os.environ, {}, clear=True):
            env = Environment(
                api_token="test-token",
                base_url="https://test.example.com",
            )

            assert env.api_token == "test-token"
            assert env.base_url == "https://test.example.com"

    def test_init_with_environment_variables(self):
        """Test initialization with values from environment variables."""
        env_vars = {
            "DATAROBOT_API_TOKEN": "env-token",
            "DATAROBOT_ENDPOINT": "https://env.example.com",
        }

        with patch.dict(os.environ, env_vars):
            env = Environment()

            assert env.api_token == "env-token"
            assert env.base_url == "https://env.example.com"

    def test_environment_variables_override_parameters(self):
        """Test that environment variables take precedence over parameters."""
        env_vars = {
            "DATAROBOT_API_TOKEN": "env-token",
            "DATAROBOT_ENDPOINT": "https://env.example.com",
        }

        with patch.dict(os.environ, env_vars):
            env = Environment(
                api_token="test-token",
                base_url="https://test.example.com",
            )

            assert env.api_token == "env-token"
            assert env.base_url == "https://env.example.com"

    def test_api_v2_removed_from_base_url(self):
        """Test that '/api/v2' is removed from base_url."""
        with patch.dict(os.environ, {}, clear=True):
            env = Environment(
                api_token="test-token",
                base_url="https://test.example.com/api/v2",
            )
            assert env.base_url == "https://test.example.com"

    @patch("cli.Kernel")
    def test_interface_property(self, mock_kernel):
        """Test that the interface property returns an Kernel instance."""
        # Setup mock
        with patch.dict(os.environ, {}, clear=True):
            mock_kernel_instance = MagicMock(spec=Kernel)
            mock_kernel.return_value = mock_kernel_instance

            # Create environment and access interface
            env = Environment(
                api_token="test-token",
                base_url="https://test.example.com",
            )
            interface = env.interface

            # Verify Kernel was created with correct parameters
            mock_kernel.assert_called_once_with(
                api_token="test-token",
                base_url="https://test.example.com",
            )

            # Verify interface is the mock kernel
            assert interface == mock_kernel_instance
