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
from unittest import mock
from unittest.mock import Mock, mock_open, patch

import pytest
from openai.types.chat import ChatCompletion

from cli import Kernel


class TestKernel:
    def test_headers_property(self):
        """Test headers property returns correct authorization header."""
        kernel = Kernel(api_token="api-123456", base_url="https://test.example.com")

        headers = kernel.headers

        assert headers == {"Authorization": "Token api-123456"}

    def test_construct_prompt_with_verbose(self):
        """Test construct_prompt with verbose set to True."""
        # Setup
        kernel = Kernel(api_token="test-key", base_url="https://test.example.com")
        user_prompt = "Hello, how are you?"

        # Execute
        result_dict = kernel.construct_prompt(user_prompt, verbose=True)

        # Assert
        assert result_dict["model"] == "datarobot-deployed-llm"
        assert len(result_dict["messages"]) == 2
        assert result_dict["messages"][0]["content"] == "You are a helpful assistant"
        assert result_dict["messages"][0]["role"] == "system"
        assert result_dict["messages"][1]["content"] == "Hello, how are you?"
        assert result_dict["messages"][1]["role"] == "user"
        assert result_dict["n"] == 1
        assert result_dict["temperature"] == 0.01
        assert result_dict["extra_body"]["api_key"] == "test-key"
        assert result_dict["extra_body"]["api_base"] == "https://test.example.com"
        assert result_dict["extra_body"]["verbose"] is True

    def test_construct_prompt_without_verbose(self):
        """Test construct_prompt with verbose set to False."""
        # Setup
        kernel = Kernel(api_token="test-key", base_url="https://test.example.com")
        user_prompt = "Tell me about Python"

        # Execute
        result_dict = kernel.construct_prompt(user_prompt, verbose=False)

        # Assert
        assert result_dict["model"] == "datarobot-deployed-llm"
        assert len(result_dict["messages"]) == 2
        assert result_dict["messages"][0]["content"] == "You are a helpful assistant"
        assert result_dict["messages"][0]["role"] == "system"
        assert result_dict["messages"][1]["content"] == "Tell me about Python"
        assert result_dict["messages"][1]["role"] == "user"
        assert result_dict["n"] == 1
        assert result_dict["temperature"] == 0.01
        assert result_dict["extra_body"]["api_key"] == "test-key"
        assert result_dict["extra_body"]["api_base"] == "https://test.example.com"
        assert result_dict["extra_body"]["verbose"] is False

    @patch("os.path.exists")
    @patch("os.remove")
    @patch("builtins.open", new_callable=mock_open, read_data="test output data")
    def test_get_output_success(self, mock_file, mock_remove, mock_exists):
        """Test get_output_local reads and removes the file successfully."""
        # Setup
        mock_exists.return_value = True
        output_path = "/test/output/path.json"

        # Execute
        result = Kernel.get_output(output_path)

        # Assert
        mock_file.assert_called_once_with(output_path, "r")
        mock_exists.assert_has_calls([mock.call(output_path), mock.call(output_path)])
        mock_remove.assert_called_once_with(output_path)
        assert result == "test output data"

    @patch("os.path.exists")
    @patch("os.remove")
    @patch("builtins.open", new_callable=mock_open, read_data="test output data")
    def test_get_output_file_not_exists(self, mock_file, mock_remove, mock_exists):
        """Test get_output_local when file doesn't exist after reading."""
        # Setup
        mock_exists.return_value = False
        output_path = "/test/output/path.json"

        # Execute
        result = Kernel.get_output(output_path)

        # Assert
        mock_exists.assert_called_once_with(output_path)
        mock_file.assert_not_called()
        mock_remove.assert_not_called()
        assert result is None

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_get_output_file_not_found(self, mock_file):
        """Test get_output_local raises FileNotFoundError if file doesn't exist."""
        # Setup
        output_path = "/test/output/path.json"

        # Execute and Assert
        result = Kernel.get_output(output_path)
        mock_file.assert_not_called()
        assert result is None

    def test_validate_execute_args_empty_prompt(self):
        """Test validate_execute_args raises ValueError with empty prompt."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )

        # Execute and Assert
        with pytest.raises(
            ValueError, match="user_prompt or completion_json must provided."
        ):
            kernel.validate_and_create_execute_args(user_prompt="")

    def test_validate_execute_args_basic(self):
        """Test validate_execute_args with minimal parameters."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        user_prompt = "Hello, assistant!"

        # Execute
        command_args, output_path = kernel.validate_and_create_execute_args(user_prompt)

        # Verify the extra_body contains the correct API details
        extra_body = json.loads(command_args.split("--")[1][17:-2])["extra_body"]
        assert extra_body["api_key"] == "test-token"
        assert extra_body["api_base"] == "https://test.example.com"
        assert extra_body["verbose"] is True

        # Verify output path uses current directory
        expected_output_path = os.path.join(os.getcwd(), "custom_model", "output.json")
        assert output_path == expected_output_path

        # Verify command_args contains all parameters
        assert user_prompt in command_args.split("--")[1]
        assert "--default_headers '{}'" in command_args
        assert (
            f"--custom_model_dir '{os.path.join(os.getcwd(), 'custom_model')}'"
            in command_args
        )
        assert f"--output_path '{expected_output_path}'" in command_args

    @patch.object(Kernel, "construct_prompt")
    def test_validate_execute_args_custom_paths(self, mock_construct_prompt):
        """Test validate_execute_args with custom model_dir and output_path."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        user_prompt = "Hello, assistant!"
        custom_model_dir = "/custom/path/model"
        custom_output_path = "/custom/path/output.json"
        expected_chat_completion = '{"content": "test completion"}'
        mock_construct_prompt.return_value = expected_chat_completion

        # Execute
        command_args, output_path = kernel.validate_and_create_execute_args(
            user_prompt,
            custom_model_dir=custom_model_dir,
            output_path=custom_output_path,
        )

        # Assert
        # Verify custom paths are used
        assert output_path == custom_output_path

        # Verify command_args contains custom paths
        assert f"--custom_model_dir '{custom_model_dir}'" in command_args
        assert f"--output_path '{custom_output_path}'" in command_args

    @patch.object(Kernel, "construct_prompt")
    def test_validate_execute_args_output_format(self, mock_construct_prompt):
        """Test validate_execute_args returns correctly formatted command arguments."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        user_prompt = "Hello, assistant!"
        expected_chat_completion = '{"content": "test completion"}'
        mock_construct_prompt.return_value = expected_chat_completion

        # Execute
        command_args, _ = kernel.validate_and_create_execute_args(user_prompt)

        # Assert
        # Verify command_args structure with single quotes for arguments
        assert command_args.startswith("--chat_completion '")
        assert "--default_headers '{}'" in command_args
        assert "--custom_model_dir '" in command_args
        assert "--output_path '" in command_args

    @patch("cli.OpenAI")
    def test_deployment_basic_functionality(self, mock_openai):
        """Test deployment method creates OpenAI client and calls chat.completions.create correctly."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        deployment_id = "test-deployment-id"
        user_prompt = "Hello, assistant!"

        # Mock the OpenAI client and its methods
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_completions = Mock()
        mock_client.chat.completions = mock_completions
        mock_completion_obj = Mock(spec=ChatCompletion)
        mock_completions.create.return_value = mock_completion_obj

        # Execute
        result = kernel.deployment(deployment_id, user_prompt)

        # Assert
        # Verify OpenAI client was created with correct parameters
        mock_openai.assert_called_once_with(
            base_url=f"https://test.example.com/api/v2/deployments/{deployment_id}/",
            api_key="test-token",
            _strict_response_validation=False,
        )

        # Verify chat.completions.create was called with correct parameters
        mock_completions.create.assert_called_once_with(
            model="datarobot-deployed-llm",
            messages=[
                {"content": "You are a helpful assistant", "role": "system"},
                {"content": "Hello, assistant!", "role": "user"},
            ],
            n=1,
            temperature=0.01,
            extra_body={
                "api_key": "test-token",
                "api_base": "https://test.example.com",
                "verbose": True,
            },
        )

        # Verify the result is the completion object
        assert result == mock_completion_obj

    @patch("cli.OpenAI")
    @patch("builtins.print")
    def test_deployment_prints_debug_info(self, mock_print, mock_openai):
        """Test deployment method prints debug info."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        deployment_id = "test-deployment-id"
        user_prompt = "Hello, assistant!"

        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_completions = Mock()
        mock_client.chat.completions = mock_completions
        mock_completions.create.return_value = Mock(spec=ChatCompletion)

        # Execute
        kernel.deployment(deployment_id, user_prompt)

        # Assert print statements were called with expected arguments
        expected_api_url = (
            "https://test.example.com/api/v2/deployments/test-deployment-id/"
        )
        mock_print.assert_any_call(expected_api_url)

    @patch("cli.OpenAI")
    def test_deployment_error_handling(self, mock_openai):
        """Test deployment method propagates errors from OpenAI client."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        deployment_id = "test-deployment-id"
        user_prompt = "Hello, assistant!"

        # Mock the OpenAI client to raise an exception
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_completions = Mock()
        mock_client.chat.completions = mock_completions
        mock_completions.create.side_effect = ValueError("Test error")

        # Execute and Assert
        with pytest.raises(ValueError, match="Test error"):
            kernel.deployment(deployment_id, user_prompt)

    @patch.object(Kernel, "validate_and_create_execute_args")
    @patch.object(Kernel, "get_output")
    @patch("os.system")
    def test_local_success(self, mock_system, mock_get_output, mock_validate):
        """Test successful local execution path."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )

        # Mock validate_execute_args return values
        mock_validate.return_value = ("--test-args", "/local/output/path.json")

        # Mock successful command execution
        mock_system.return_value = 0

        # Mock successful local output retrieval
        expected_output = '{"result": "success"}'
        mock_get_output.return_value = expected_output

        # Execute
        result = kernel.local("Test prompt")

        # Assert
        mock_validate.assert_called_once_with("Test prompt", "", "", "", False)

        # Verify system command was executed correctly
        mock_system.assert_called_once_with("python3 run_agent.py --test-args")

        # Verify output was retrieved
        mock_get_output.assert_called_once_with("/local/output/path.json")

        # Verify correct result returned
        assert result == expected_output

    @patch.object(Kernel, "validate_and_create_execute_args")
    @patch("os.system")
    def test_local_command_error(self, mock_system, mock_validate):
        """Test local execution with command error."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )

        # Mock validate_execute_args return values
        mock_validate.return_value = ("--test-args", "/local/output/path.json")

        # Mock failed command execution
        mock_system.return_value = 1

        # Execute and Assert
        with pytest.raises(RuntimeError, match="Command failed with exit code 1"):
            kernel.local("Test prompt")

    @patch.object(Kernel, "validate_and_create_execute_args")
    @patch("os.system")
    @patch("builtins.print")
    def test_local_other_exception(self, mock_print, mock_system, mock_validate):
        """Test local execution with unexpected exception."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )

        # Mock validate_execute_args return values
        mock_validate.return_value = ("--test-args", "/local/output/path.json")

        # Mock system call throwing exception
        mock_system.side_effect = FileNotFoundError("Command not found")

        # Execute and Assert
        with pytest.raises(FileNotFoundError, match="Command not found"):
            kernel.local("Test prompt")

        # Verify error message was printed
        mock_print.assert_called_with("Error executing command: Command not found")

    @patch("cli.requests.post")
    @patch("cli.requests.get")
    @patch("cli.time.sleep")
    @patch(
        "os.environ",
        {
            "DATAROBOT_API_TOKEN": "test-api-token",
            "DATAROBOT_ENDPOINT": "https://test.example.com",
        },
    )
    def test_custom_model_basic_functionality(
        self, mock_sleep, mock_requests_get, mock_requests_post
    ):
        """Test custom_model method makes HTTP requests to DataRobot API correctly."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        custom_model_id = "test-custom-model-id"
        user_prompt = "Hello, assistant!"

        # Mock the initial POST response
        mock_post_response = Mock()
        mock_post_response.ok = True
        mock_post_response.headers = {"Location": "https://test.example.com/status/123"}
        mock_requests_post.return_value = mock_post_response

        # Mock the status check response (first call returns status, second redirects)
        mock_status_response = Mock()
        mock_status_response.ok = True
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {"status": "RUNNING"}

        mock_redirect_response = Mock()
        mock_redirect_response.ok = True
        mock_redirect_response.status_code = 303
        mock_redirect_response.headers = {
            "Location": "https://test.example.com/result/123"
        }

        # Mock the final result response
        mock_result_response = Mock()
        mock_result_response.json.return_value = {
            "choices": [{"message": {"content": "Hello! How can I help you?"}}]
        }

        mock_requests_get.side_effect = [
            mock_status_response,
            mock_redirect_response,
            mock_result_response,
        ]

        # Execute
        result = kernel.custom_model(custom_model_id, user_prompt)

        # Assert
        # Verify POST request was made with correct parameters
        mock_requests_post.assert_called_once_with(
            "https://test.example.com/api/v2/genai/agents/fromCustomModel/test-custom-model-id/chat/",
            headers={
                "Authorization": "Bearer test-api-token",
                "Content-Type": "application/json",
            },
            json={"messages": [{"role": "user", "content": "Hello, assistant!"}]},
        )

        # Verify status polling was done
        assert mock_requests_get.call_count == 3

        # Verify the result content
        assert result == "Hello! How can I help you?"

    @patch("cli.requests.post")
    @patch("cli.time.sleep")
    @patch(
        "os.environ",
        {
            "DATAROBOT_API_TOKEN": "test-api-token",
            "DATAROBOT_ENDPOINT": "https://test.example.com",
        },
    )
    def test_custom_model_initial_request_failure(self, mock_sleep, mock_requests_post):
        """Test custom_model handles initial POST request failure."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        custom_model_id = "test-custom-model-id"
        user_prompt = "Hello, assistant!"

        # Mock the initial POST response to fail
        mock_post_response = Mock()
        mock_post_response.ok = False
        mock_post_response.content = b"API request failed with status 500"
        mock_requests_post.return_value = mock_post_response

        # Execute and Assert
        with pytest.raises(Exception):
            kernel.custom_model(custom_model_id, user_prompt)

        # Verify the correct request was attempted
        mock_requests_post.assert_called_once_with(
            "https://test.example.com/api/v2/genai/agents/fromCustomModel/test-custom-model-id/chat/",
            headers={
                "Authorization": "Bearer test-api-token",
                "Content-Type": "application/json",
            },
            json={"messages": [{"role": "user", "content": "Hello, assistant!"}]},
        )

    @patch("cli.requests.post")
    @patch("cli.requests.get")
    @patch("cli.time.sleep")
    @patch(
        "os.environ",
        {
            "DATAROBOT_API_TOKEN": "test-api-token",
            "DATAROBOT_ENDPOINT": "https://test.example.com",
        },
    )
    def test_custom_model_missing_location_header(
        self, mock_sleep, mock_requests_get, mock_requests_post
    ):
        """Test custom_model handles missing Location header in successful response."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        custom_model_id = "test-custom-model-id"
        user_prompt = "Hello, assistant!"

        # Mock the initial POST response with missing Location header
        mock_post_response = Mock()
        mock_post_response.ok = True
        mock_post_response.headers = {}  # No Location header
        mock_post_response.content = b"No Location header provided"
        mock_requests_post.return_value = mock_post_response

        # Execute and Assert
        with pytest.raises(Exception):
            kernel.custom_model(custom_model_id, user_prompt)

    @patch("cli.requests.post")
    @patch("cli.requests.get")
    @patch("cli.time.sleep")
    @patch(
        "os.environ",
        {
            "DATAROBOT_API_TOKEN": "test-api-token",
            "DATAROBOT_ENDPOINT": "https://test.example.com",
        },
    )
    def test_custom_model_status_error(
        self, mock_sleep, mock_requests_get, mock_requests_post
    ):
        """Test custom_model handles ERROR status from status endpoint."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        custom_model_id = "test-custom-model-id"
        user_prompt = "Hello, assistant!"

        # Mock the initial POST response
        mock_post_response = Mock()
        mock_post_response.ok = True
        mock_post_response.headers = {"Location": "https://test.example.com/status/123"}
        mock_requests_post.return_value = mock_post_response

        # Mock the status check response with ERROR status
        mock_status_response = Mock()
        mock_status_response.ok = True
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "status": "ERROR",
            "errorMessage": "Model execution failed",
        }
        mock_requests_get.return_value = mock_status_response

        # Execute and Assert
        with pytest.raises(Exception) as exc_info:
            kernel.custom_model(custom_model_id, user_prompt)

        # Verify the error contains the status response
        assert "status" in str(exc_info.value)
        assert "ERROR" in str(exc_info.value)

    @patch("cli.requests.post")
    @patch("cli.requests.get")
    @patch("cli.time.sleep")
    @patch(
        "os.environ",
        {
            "DATAROBOT_API_TOKEN": "test-api-token",
            "DATAROBOT_ENDPOINT": "https://test.example.com",
        },
    )
    def test_custom_model_error_in_response(
        self, mock_sleep, mock_requests_get, mock_requests_post
    ):
        """Test custom_model handles error message in agent response."""
        # Setup
        kernel = Kernel(
            api_token="test-token",
            base_url="https://test.example.com",
        )
        custom_model_id = "test-custom-model-id"
        user_prompt = "Hello, assistant!"

        # Mock the initial POST response
        mock_post_response = Mock()
        mock_post_response.ok = True
        mock_post_response.headers = {"Location": "https://test.example.com/status/123"}
        mock_requests_post.return_value = mock_post_response

        # Mock the status check responses
        mock_status_response = Mock()
        mock_status_response.ok = True
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {"status": "RUNNING"}

        mock_redirect_response = Mock()
        mock_redirect_response.ok = True
        mock_redirect_response.status_code = 303
        mock_redirect_response.headers = {
            "Location": "https://test.example.com/result/123"
        }

        # Mock the final result response with an error message
        mock_result_response = Mock()
        mock_result_response.json.return_value = {
            "errorMessage": "Failed to process request",
            "errorDetails": "Invalid input format",
        }

        mock_requests_get.side_effect = [
            mock_status_response,
            mock_redirect_response,
            mock_result_response,
        ]

        # Execute
        result = kernel.custom_model(custom_model_id, user_prompt)

        # Assert the result contains the error message
        assert "Error: " in result
        assert "Failed to process request" in result
        assert "Error details:" in result
        assert "Invalid input format" in result
