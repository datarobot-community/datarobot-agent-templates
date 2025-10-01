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
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import Span
from pydantic import ValidationError

from run_agent import (
    DEFAULT_OUTPUT_JSON_PATH,
    DEFAULT_OUTPUT_LOG_PATH,
    argparse_args,
    construct_prompt,
    main,
    main_stdout_redirect,
    run_agent_procedure,
    set_otel_attributes,
    setup_logging,
    setup_otel,
    setup_otel_env_variables,
    setup_otel_exporter,
    store_result,
    tracer,
)


@pytest.fixture
def tempdir_and_cleanup():
    with tempfile.TemporaryDirectory() as tempdir:
        yield Path(tempdir)
    # Also remove the default output log path
    if os.path.exists(DEFAULT_OUTPUT_LOG_PATH):
        os.remove(DEFAULT_OUTPUT_LOG_PATH)


class TestArgparseArgs:
    def test_argparse_args_custom_values(self):
        """Test that custom values are correctly parsed from command line arguments."""
        # Mock sys.argv to simulate passing command line arguments
        with patch(
            "sys.argv",
            [
                "run_agent.py",
                "--chat_completion",
                '{"messages": [{"role": "user", "content": "Hello"}]}',
                "--default_headers",
                '{"X-API-Key": "test-key"}',
                "--custom_model_dir",
                "/path/to/model",
                "--output_path",
                "/path/to/output",
                "--otel_entity_id",
                "test-entity-id",
                "--otel_attributes",
                '{"key": "value"}',
            ],
        ):
            args = argparse_args()

            # Check custom values
            assert (
                args.chat_completion
                == '{"messages": [{"role": "user", "content": "Hello"}]}'
            )
            assert args.default_headers == '{"X-API-Key": "test-key"}'
            assert args.custom_model_dir == "/path/to/model"
            assert args.output_path == "/path/to/output"
            assert args.otel_entity_id == "test-entity-id"
            assert args.otel_attributes == '{"key": "value"}'

    def test_argparse_args_partial_values(self):
        """Test that partial arguments work correctly with others taking default values."""
        # Mock sys.argv to simulate passing only some arguments
        with patch(
            "sys.argv",
            [
                "run_agent.py",
                "--chat_completion",
                '{"messages": []}',
                "--custom_model_dir",
                "/path/to/model",
            ],
        ):
            args = argparse_args()

            # Check mixture of custom and default values
            assert args.chat_completion == '{"messages": []}'
            assert args.default_headers == "{}"  # default
            assert args.custom_model_dir == "/path/to/model"
            assert args.output_path is None
            assert args.otel_entity_id is None
            assert args.otel_attributes is None


class TestSetupLogging:
    @pytest.fixture
    def logger(self):
        logger = logging.getLogger("test_logger")
        # Clear any existing handlers
        logger.handlers = []
        return logger

    @patch("logging.StreamHandler")
    def test_setup_logging(self, mock_stream_handler, logger):
        # GIVEN mock stream handler
        mock_stream = MagicMock()
        mock_stream_handler.return_value = mock_stream

        # WHEN setup_logging is called
        setup_logging(logger=logger, log_level=logging.INFO)

        # THEN logger configuration is set
        assert logger.level == logging.INFO

        # THEN the stream handler is called with stderr
        mock_stream_handler.assert_called_once_with(sys.stderr)

        # THEN logger has a single handler
        assert len(logger.handlers) == 1
        mock_stream.setFormatter.assert_called_once()
        stream_formatter_call = mock_stream.setFormatter.call_args[0][0]
        assert stream_formatter_call._fmt == "%(asctime)s - %(levelname)s - %(message)s"

    @patch("logging.StreamHandler")
    def test_setup_logging_custom_stream(self, mock_stream_handler, logger):
        # GIVEN mock stream handler
        mock_stream = MagicMock()
        mock_stream_handler.return_value = mock_stream

        # GIVEN a custom stream
        custom_stream = MagicMock()

        # WHEN setup_logging is called
        setup_logging(logger=logger, stream=custom_stream, log_level=logging.INFO)

        # THEN logger configuration is set
        assert logger.level == logging.INFO

        # THEN the stream handler is called with stderr
        mock_stream_handler.assert_called_once_with(custom_stream)

        # THEN logger has a single handler
        assert len(logger.handlers) == 1
        mock_stream.setFormatter.assert_called_once()
        stream_formatter_call = mock_stream.setFormatter.call_args[0][0]
        assert stream_formatter_call._fmt == "%(asctime)s - %(levelname)s - %(message)s"

    @patch("logging.StreamHandler")
    def test_setup_logging_removes_existing_handlers(self, mock_stream_handler, logger):
        # GIVEN mock stream handler with two different handlers
        mock_stream1 = MagicMock()
        mock_stream2 = MagicMock()
        mock_stream_handler.side_effect = [mock_stream1, mock_stream2]

        # GIVEN setup_logging already called
        setup_logging(logger=logger, log_level=logging.INFO)

        # WHEN setup_logging is called again
        setup_logging(logger=logger, log_level=logging.INFO)

        # THEN the logger has only one handler
        assert len(logger.handlers) == 1

        # THEN this handler is the second one
        assert logger.handlers[0] == mock_stream2


class TestSetupOtelEnvVariables:
    @pytest.fixture
    def entity_id(self):
        return "test-entity-id"

    @pytest.mark.parametrize(
        "headers, endpoint",
        [
            ("some-headers", "some-endpoint"),
            ("some-headers", None),
            (None, "some-endpoint"),
        ],
    )
    def test_setup_otel_env_variables_does_not_override_existing_variables(
        self, headers, endpoint, entity_id
    ):
        # GIVEN Datarobot os environment variables
        os_environ = {
            "DATAROBOT_ENDPOINT": "https://app.datarobot.com/api/v2",
            "DATAROBOT_API_TOKEN": "test-api-key",
        }
        # GIVEN existing otel config variables
        if headers:
            os_environ["OTEL_EXPORTER_OTLP_HEADERS"] = headers
        if endpoint:
            os_environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
        with patch.dict(os.environ, os_environ, clear=True):
            # WHEN setup_otel_env_variables is called
            setup_otel_env_variables(entity_id)

            # THEN the environment variables are not overridden
            assert os.environ.get("OTEL_EXPORTER_OTLP_HEADERS") == headers
            assert os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") == endpoint

    @pytest.mark.parametrize(
        "datarobot_endpoint, datarobot_api_token, expected_headers, expected_endpoint",
        [
            (None, None, None, None),
            ("https://app.datarobot.com/api/v2", None, None, None),
            (None, "test-api-key", None, None),
            (
                "https://app.datarobot.com/api/v2",
                "test-api-key",
                "X-DataRobot-Api-Key=test-api-key,X-DataRobot-Entity-Id=test-entity-id",
                "https://app.datarobot.com/otel",
            ),
        ],
    )
    def test_setup_otel_env_variables(
        self,
        datarobot_endpoint,
        datarobot_api_token,
        expected_headers,
        expected_endpoint,
        entity_id,
    ):
        # GIVEN os environment variables
        os_environ = {}
        if datarobot_endpoint:
            os_environ["DATAROBOT_ENDPOINT"] = datarobot_endpoint
        if datarobot_api_token:
            os_environ["DATAROBOT_API_TOKEN"] = datarobot_api_token
        with patch.dict(os.environ, os_environ, clear=True):
            # WHEN setup_otel_env_variables is called
            setup_otel_env_variables(entity_id)

            # THEN the environment variables are set
            assert os.environ.get("OTEL_EXPORTER_OTLP_HEADERS") == expected_headers
            assert os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") == expected_endpoint

    def test_setup_otel_env_variables_with_on_prem_collector(self, entity_id):
        datarobot_api_token = "test-api-key"
        expected_headers = (
            "X-DataRobot-Api-Key=test-api-key,X-DataRobot-Entity-Id=test-entity-id"
        )
        expected_endpoint = "http://datarobot-otel-collector:4318"

        os_environ = {}
        os_environ["DATAROBOT_ENDPOINT"] = "https://app.datarobot.com/api/v2"
        os_environ["DATAROBOT_OTEL_COLLECTOR_BASE_URL"] = (
            "http://datarobot-otel-collector:4318"
        )
        os_environ["DATAROBOT_API_TOKEN"] = datarobot_api_token

        with patch.dict(os.environ, os_environ, clear=True):
            # WHEN setup_otel_env_variables is called
            setup_otel_env_variables(entity_id)

            # THEN the environment variables are set
            assert os.environ.get("OTEL_EXPORTER_OTLP_HEADERS") == expected_headers
            assert os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") == expected_endpoint


class TestSetupOtelExporter:
    def test_setup_otel_exporter(self):
        # WHEN setup_otel_exporter is called
        setup_otel_exporter()

        # THEN the tracer provider has a simple span processor
        # The first is still the batch processor but it does not matter
        assert len(tracer.span_processor._span_processors) >= 1
        assert isinstance(
            tracer.span_processor._span_processors[-1], SimpleSpanProcessor
        )


class TestSetOtelAttributes:
    def test_set_otel_attributes(self):
        # GIVEN a span and a string of attributes
        attributes = '{"key": "value"}'
        # WHEN set_otel_attributes is called
        span = Mock()
        set_otel_attributes(span, attributes)

        # THEN the span has the attribute
        span.set_attribute.assert_called_once_with("key", "value")

    def test_set_otel_attributes_invalid_json(self):
        # GIVEN a span and an invalid JSON string
        attributes = "invalid json"
        span = Mock()

        # WHEN set_otel_attributes is called
        set_otel_attributes(span, attributes)

        # THEN no exception is raised

        # THEN the span does not have the attribute
        span.set_attribute.assert_not_called()


class TestSetupOtel:
    @patch("run_agent.setup_otel_env_variables")
    @patch("run_agent.setup_otel_exporter")
    @patch("run_agent.set_otel_attributes")
    def test_setup_otel_all_values(
        self,
        mock_set_otel_attributes,
        mock_setup_otel_exporter,
        mock_setup_otel_env_variables,
    ):
        # GIVEN a mock args with otel_entity_id and otel_attributes
        mock_args = MagicMock()
        mock_args.otel_entity_id = "test-entity-id"
        mock_args.otel_attributes = '{"key": "value"}'

        # GIVEN the environment variables are set
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"},
            clear=True,
        ):
            # WHEN setup_otel is called
            span = setup_otel(mock_args)

        # THEN the span is Span
        assert isinstance(span, Span)

        # THEN setup_otel_env_variables was called with the correct parameters
        mock_setup_otel_env_variables.assert_called_once_with("test-entity-id")
        mock_setup_otel_exporter.assert_called_once()
        mock_set_otel_attributes.assert_called_once_with(span, '{"key": "value"}')

    @patch("run_agent.setup_otel_env_variables")
    @patch("run_agent.setup_otel_exporter")
    @patch("run_agent.set_otel_attributes")
    def test_setup_otel_no_otel_context(
        self,
        mock_set_otel_attributes,
        mock_setup_otel_exporter,
        mock_setup_otel_env_variables,
    ):
        # GIVEN a mock args with no otel_entity_id and no otel_attributes
        mock_args = MagicMock()
        mock_args.otel_entity_id = None
        mock_args.otel_attributes = None

        # GIVEN the environment variables are not set
        with patch.dict(os.environ, {}, clear=True):
            # WHEN setup_otel is called
            span = setup_otel(mock_args)

        # THEN the span is Span
        assert isinstance(span, Span)

        # THEN setup_otel_env_variables was not called
        mock_setup_otel_env_variables.assert_not_called()
        # THEN setup_otel_exporter was not called
        mock_setup_otel_exporter.assert_not_called()
        # THEN set_otel_attributes was not called
        mock_set_otel_attributes.assert_not_called()

    @patch("run_agent.setup_otel_env_variables")
    @patch("run_agent.setup_otel_exporter")
    @patch("run_agent.set_otel_attributes")
    def test_setup_otel_otlp_endpoint_set(
        self,
        mock_set_otel_attributes,
        mock_setup_otel_exporter,
        mock_setup_otel_env_variables,
    ):
        # GIVEN a mock args with no otel_entity_id and no otel_attributes
        mock_args = MagicMock()
        mock_args.otel_entity_id = None
        mock_args.otel_attributes = None

        # GIVEN the environment variables are set
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"},
            clear=True,
        ):
            # WHEN setup_otel is called
            span = setup_otel(mock_args)

        # THEN the span is Span
        assert isinstance(span, Span)

        # THEN setup_otel_env_variables was not called
        mock_setup_otel_env_variables.assert_not_called()
        # THEN setup_otel_exporter was called
        mock_setup_otel_exporter.assert_called_once()
        # THEN set_otel_attributes was not called
        mock_set_otel_attributes.assert_not_called()

    @patch("run_agent.setup_otel_env_variables")
    @patch("run_agent.setup_otel_exporter")
    @patch("run_agent.set_otel_attributes")
    def test_setup_otel_otlp_endpoint_not_set(
        self,
        mock_set_otel_attributes,
        mock_setup_otel_exporter,
        mock_setup_otel_env_variables,
    ):
        # GIVEN a mock args with otel_entity_id and no otel_attributes
        mock_args = MagicMock()
        mock_args.otel_entity_id = "test-entity-id"
        mock_args.otel_attributes = None

        # GIVEN the environment variables are set
        with patch.dict(os.environ, {}, clear=True):
            # WHEN setup_otel is called
            span = setup_otel(mock_args)

        # THEN the span is Span
        assert isinstance(span, Span)

        # THEN setup_otel_env_variables was called
        mock_setup_otel_env_variables.assert_called_once_with("test-entity-id")
        # THEN setup_otel_exporter was not called
        mock_setup_otel_exporter.assert_not_called()
        # THEN set_otel_attributes was not called
        mock_set_otel_attributes.assert_not_called()

    @patch("run_agent.setup_otel_env_variables")
    @patch("run_agent.setup_otel_exporter")
    @patch("run_agent.set_otel_attributes")
    def test_setup_otel_otlp_endpoint_otel_attributes_set(
        self,
        mock_set_otel_attributes,
        mock_setup_otel_exporter,
        mock_setup_otel_env_variables,
    ):
        # GIVEN a mock args with no otel_entity_id and otel_attributes
        mock_args = MagicMock()
        mock_args.otel_entity_id = None
        mock_args.otel_attributes = '{"key": "value"}'

        # GIVEN the environment variables are set
        with patch.dict(os.environ, {}, clear=True):
            # WHEN setup_otel is called
            span = setup_otel(mock_args)

        # THEN the span is Span
        assert isinstance(span, Span)

        # THEN setup_otel_env_variables was called
        mock_setup_otel_env_variables.assert_not_called()
        # THEN setup_otel_exporter was not called
        mock_setup_otel_exporter.assert_not_called()
        # THEN set_otel_attributes was called
        mock_set_otel_attributes.assert_called_once_with(span, '{"key": "value"}')


class TestConstructPrompt:
    def test_construct_prompt_valid_json(self):
        """Test that a valid JSON string is correctly parsed."""
        chat_completion = (
            '{"messages": [{"role": "user", "content": "Hello"}], "model": "gpt-4o"}'
        )
        result = construct_prompt(chat_completion)
        assert result["messages"] == [{"role": "user", "content": "Hello"}]
        assert result["model"] == "gpt-4o"

    def test_construct_prompt_adds_model_if_missing(self):
        """Test that a valid JSON string is correctly parsed."""
        chat_completion = '{"messages": [{"role": "user", "content": "Hello"}]}'
        result = construct_prompt(chat_completion)
        assert result["messages"] == [{"role": "user", "content": "Hello"}]
        assert result["model"] == "unknown"

    def test_construct_prompt_invalid_json(self):
        """Test that an invalid JSON string raises an error."""
        chat_completion = "invalid json"
        with pytest.raises(json.JSONDecodeError):
            construct_prompt(chat_completion)

    def test_construct_prompt_empty_json(self):
        """Test that an empty JSON string raises an error."""
        chat_completion = "{}"
        with pytest.raises(ValidationError):
            construct_prompt(chat_completion)

    def test_construct_prompt_unexpected_key(self):
        """Test that an unexpected key raises an error."""
        chat_completion = '{"messages": [{"role": "user", "content": "Hello"}], "unexpected_key": "value"}'

        # OpenAI interface accepts extra keys and ignores them
        prompt = construct_prompt(chat_completion)
        assert prompt["unexpected_key"] == "value"


class TestStoreResult:
    @patch("builtins.open")
    def test_store_result_success(self, mock_file_open):
        """Test that a result is correctly stored."""
        result = MagicMock()
        result.model_dump.return_value = {"id": "test-id", "choices": []}
        store_result(result, "1234567890", "/path/to/output.json")
        mock_file_open.assert_called_once_with("/path/to/output.json", "w")
        mock_file_open.return_value.__enter__.return_value.write.assert_called_once_with(
            '{"id": "test-id", "choices": [], "trace_id": "1234567890"}'
        )


class TestRunAgentProcedure:
    @patch("run_agent.construct_prompt")
    @patch("run_agent.execute_drum_inline")
    @patch("run_agent.store_result")
    @patch("run_agent.setup_otel")
    def test_run_agent_with_custom_model_dir(
        self,
        mock_setup_otel,
        mock_store_result,
        mock_execute_drum_inline,
        mock_construct_prompt,
    ):
        # GIVEN simple input arguments
        mock_args = MagicMock()
        mock_args.chat_completion = '{"messages": []}'
        mock_args.default_headers = "{}"
        mock_args.custom_model_dir = "/path/to/custom/model"

        # GIVEN output_path is set
        mock_args.output_path = "/path/to/output"

        # GIVEN a mock completion
        mock_completion = MagicMock()
        mock_execute_drum_inline.return_value = mock_completion

        # GIVEN mock_setup_otel returns a span with a trace_id
        mock_span = MagicMock()
        mock_span.context.trace_id = 0x1234567890
        mock_setup_otel.return_value = mock_span

        # GIVEN mock_construct_prompt returns a dict
        mock_construct_prompt.return_value = {"messages": []}

        # WHEN main is called
        run_agent_procedure(mock_args)

        # THEN setup_otel was called with args
        mock_setup_otel.assert_called_once_with(mock_args)

        # THEN execute_drum was called with correct parameters
        mock_execute_drum_inline.assert_called_once_with(
            chat_completion={"messages": []},
            custom_model_dir="/path/to/custom/model",
        )

        # THEN store_result was called with correct parameters
        mock_store_result.assert_called_once_with(
            mock_completion,
            "1234567890",
            Path("/path/to/output"),
        )

    @patch("run_agent.construct_prompt")
    @patch("run_agent.execute_drum_inline")
    @patch("run_agent.store_result")
    @patch("run_agent.setup_otel")
    def test_run_agent_without_custom_model_dir(
        self,
        mock_setup_otel,
        mock_store_result,
        mock_execute_drum_inline,
        mock_construct_prompt,
    ):
        # GIVEN simple input arguments
        mock_args = MagicMock()
        mock_args.chat_completion = '{"messages": []}'
        mock_args.default_headers = "{}"
        mock_args.custom_model_dir = "/path/to/custom/model"

        # GIVEN output_path is not set
        mock_args.output_path = None

        # GIVEN a mock completion
        mock_completion = MagicMock()
        mock_execute_drum_inline.return_value = mock_completion

        # GIVEN mock_setup_otel returns a span with a trace_id
        mock_span = MagicMock()
        mock_span.context.trace_id = 0x1234567890
        mock_setup_otel.return_value = mock_span

        # GIVEN mock_construct_prompt returns a dict
        mock_construct_prompt.return_value = {"messages": []}

        # WHEN main is called
        run_agent_procedure(mock_args)

        # THEN setup_otel was called with args
        mock_setup_otel.assert_called_once_with(mock_args)

        # THEN execute_drum was called with correct parameters
        mock_execute_drum_inline.assert_called_once_with(
            chat_completion={"messages": []},
            custom_model_dir="/path/to/custom/model",
        )

        # THEN store_result was called with correct parameters
        mock_store_result.assert_called_once_with(
            mock_completion,
            "1234567890",
            DEFAULT_OUTPUT_JSON_PATH,
        )


class TestMain:
    """This procedure alone is trivial, and does not require unit tests. Therefore we
    use it to test the integration of the other procedures."""

    @patch("run_agent.argparse_args")
    @patch("run_agent.execute_drum_inline")
    def test_main_integration(
        self, mock_execute_drum_inline, mock_argparse_args, tempdir_and_cleanup
    ):
        """Test main function with a more integrated approach."""
        # GIVEN valid input arguments
        mock_args = MagicMock()
        mock_args.chat_completion = (
            '{"messages": [{"role": "user", "content": "Hello"}]}'
        )
        mock_args.default_headers = '{"X-Custom": "value"}'
        mock_args.custom_model_dir = "/path/to/model"
        # GIVEN a temporary directory for the output path
        mock_args.output_path = str(tempdir_and_cleanup / "output.json")
        mock_argparse_args.return_value = mock_args

        # GIVEN a mock completion returned from execute_drum
        mock_completion = MagicMock()
        mock_completion.model_dump.return_value = {"id": "test-id", "choices": []}
        mock_execute_drum_inline.return_value = mock_completion

        # WHEN main is called
        main()

        # THEN execute_drum was called with correct parsed parameters
        mock_execute_drum_inline.assert_called_once_with(
            chat_completion={
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "unknown",
            },
            custom_model_dir="/path/to/model",
        )

        # THEN results were stored in the temporary directory
        assert os.path.exists(tempdir_and_cleanup / "output.json")
        with open(tempdir_and_cleanup / "output.json", "r") as f:
            response_dict = json.load(f)

        # THEN the response contains the trace_id
        assert "trace_id" in response_dict

        # THEN choice and id are expected values
        assert response_dict["id"] == "test-id"
        assert response_dict["choices"] == []


class TestMainStdoutRedirect:
    @patch("run_agent.argparse_args")
    @patch("run_agent.run_agent_procedure")
    @patch("run_agent.setup_logging")
    @patch("builtins.open")
    @patch("run_agent.root")
    def test_main_stdout_redirect(
        self,
        mock_root,
        mock_open,
        mock_setup_logging,
        mock_run_agent_procedure,
        mock_argparse_args,
    ):
        # GIVEN valid input arguments
        mock_args = MagicMock()
        mock_args.output_path = "/path/to/output"
        mock_argparse_args.return_value = mock_args

        # GIVEN files opened
        f = mock_open.return_value.__enter__.return_value

        # WHEN main_stdout_redirect is called
        main_stdout_redirect()

        # THEN argparse_args was called
        mock_argparse_args.assert_called_once()

        # THEN setup_logging was called twice
        mock_setup_logging.assert_has_calls(
            [
                call(logger=mock_root, stream=f, log_level=logging.INFO),
                call(logger=mock_root, stream=f, log_level=logging.INFO),
            ]
        )

        # THEN run_agent_procedure was called with the parsed arguments
        mock_run_agent_procedure.assert_called_once_with(mock_args)

        # THEN mock_open was called twice: for default output log path and for the output path
        mock_open.assert_any_call(DEFAULT_OUTPUT_LOG_PATH, "w")
        mock_open.assert_any_call(mock_args.output_path + ".log", "a")

        # THEN f.flush was called 2 times
        assert f.flush.call_count == 2

    @patch("run_agent.argparse_args")
    @patch("run_agent.run_agent_procedure")
    @patch("run_agent.setup_logging")
    @patch("builtins.open")
    @patch("run_agent.root")
    def test_main_stdout_redirect_output_path_not_set(
        self,
        mock_root,
        mock_open,
        mock_setup_logging,
        mock_run_agent_procedure,
        mock_argparse_args,
    ):
        # GIVEN valid input arguments
        mock_args = MagicMock()
        mock_args.output_path = None
        mock_argparse_args.return_value = mock_args

        # GIVEN files opened
        f = mock_open.return_value.__enter__.return_value

        # WHEN main_stdout_redirect is called
        main_stdout_redirect()

        # THEN argparse_args was called
        mock_argparse_args.assert_called_once()

        # THEN setup_logging was called twice
        mock_setup_logging.assert_has_calls(
            [
                call(logger=mock_root, stream=f, log_level=logging.INFO),
                call(logger=mock_root, stream=f, log_level=logging.INFO),
            ]
        )

        # THEN run_agent_procedure was called with the parsed arguments
        mock_run_agent_procedure.assert_called_once_with(mock_args)

        # THEN mock_open was called twice for default output log
        mock_open.assert_any_call(DEFAULT_OUTPUT_LOG_PATH, "w")
        mock_open.assert_any_call(str(DEFAULT_OUTPUT_LOG_PATH), "a")

        # THEN f.flush was called 2 times
        assert f.flush.call_count == 2

    @patch("run_agent.argparse_args")
    @patch("run_agent.run_agent_procedure")
    @patch("run_agent.setup_logging")
    @patch("builtins.open")
    @patch("run_agent.root")
    def test_main_stdout_redirect_argparse_exception(
        self,
        mock_root,
        mock_open,
        mock_setup_logging,
        mock_run_agent_procedure,
        mock_argparse_args,
    ):
        # GIVEN argparse_args raises an exception
        mock_argparse_args.side_effect = Exception("Test exception 1")

        # GIVEN files opened
        f = mock_open.return_value.__enter__.return_value

        # WHEN main_stdout_redirect is called
        with pytest.raises(Exception, match="Test exception 1"):
            main_stdout_redirect()

        # THEN argparse_args was called
        mock_argparse_args.assert_called_once()

        # THEN setup_logging was called once
        mock_setup_logging.assert_called_once_with(
            logger=mock_root, stream=f, log_level=logging.INFO
        )

        # THEN run_agent_procedure was not called
        mock_run_agent_procedure.assert_not_called()

        # THEN mock_open was called once
        mock_open.assert_called_once_with(DEFAULT_OUTPUT_LOG_PATH, "w")

        # THEN f.flush was called 1 time
        assert f.flush.call_count == 1

        # THEN root.exception was called with the exception
        mock_root.exception.assert_called_once_with(
            "Error parsing arguments: Test exception 1"
        )

    @patch("run_agent.argparse_args")
    @patch("run_agent.run_agent_procedure")
    @patch("run_agent.setup_logging")
    @patch("builtins.open")
    @patch("run_agent.root")
    def test_main_stdout_redirect_run_agent_procedure_exception(
        self,
        mock_root,
        mock_open,
        mock_setup_logging,
        mock_run_agent_procedure,
        mock_argparse_args,
    ):
        # GIVEN valid input arguments
        mock_args = MagicMock()
        mock_args.output_path = "/path/to/output"
        mock_argparse_args.return_value = mock_args

        # GIVEN files opened
        f = mock_open.return_value.__enter__.return_value

        # GIVEN run_agent_procedure raises an exception
        mock_run_agent_procedure.side_effect = Exception("Test exception 2")

        # WHEN main_stdout_redirect is called
        with pytest.raises(Exception, match="Test exception 2"):
            main_stdout_redirect()

        # THEN argparse_args was called
        mock_argparse_args.assert_called_once()

        # THEN setup_logging was called twice
        mock_setup_logging.assert_has_calls(
            [
                call(logger=mock_root, stream=f, log_level=logging.INFO),
                call(logger=mock_root, stream=f, log_level=logging.INFO),
            ]
        )

        # THEN run_agent_procedure was called with the parsed arguments
        mock_run_agent_procedure.assert_called_once_with(mock_args)

        # THEN mock_open was called twice: for default output log path and for the output path
        mock_open.assert_any_call(DEFAULT_OUTPUT_LOG_PATH, "w")
        mock_open.assert_any_call(mock_args.output_path + ".log", "a")

        # THEN root.exception was called with the exception
        mock_root.exception.assert_called_once_with(
            "Error executing agent: Test exception 2"
        )

        # THEN f.flush was called 2 times
        assert f.flush.call_count == 2

    @patch("run_agent.argparse_args")
    @patch("run_agent.execute_drum_inline")
    def test_main_stdout_redirect_integration(
        self, mock_execute_drum_inline, mock_argparse_args, tempdir_and_cleanup
    ):
        """Test main function with a more integrated approach."""
        # GIVEN valid input arguments
        mock_args = MagicMock()
        mock_args.chat_completion = (
            '{"messages": [{"role": "user", "content": "Hello"}]}'
        )
        mock_args.default_headers = '{"X-Custom": "value"}'
        mock_args.custom_model_dir = "/path/to/model"
        # GIVEN a temporary directory for the output path
        mock_args.output_path = str(tempdir_and_cleanup / "output.json")
        mock_argparse_args.return_value = mock_args

        # GIVEN a mock completion returned from execute_drum
        mock_completion = MagicMock()
        mock_completion.model_dump.return_value = {"id": "test-id", "choices": []}
        mock_execute_drum_inline.return_value = mock_completion

        # WHEN main is called
        main_stdout_redirect()

        # THEN execute_drum was called with correct parsed parameters
        mock_execute_drum_inline.assert_called_once_with(
            chat_completion={
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "unknown",
            },
            custom_model_dir="/path/to/model",
        )

        # THEN results were stored in the temporary directory
        assert os.path.exists(tempdir_and_cleanup / "output.json")
        with open(tempdir_and_cleanup / "output.json", "r") as f:
            response_dict = json.load(f)

        # THEN the response contains the trace_id
        assert "trace_id" in response_dict

        # THEN choice and id are expected values
        assert response_dict["id"] == "test-id"
        assert response_dict["choices"] == []
