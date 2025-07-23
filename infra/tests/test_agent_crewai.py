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
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# Ensure the test directory is in sys.path for proper imports
sys.path.insert(0, str(Path(__file__).resolve().parent))


# Patch all Pulumi resources and functions used in the module
@pytest.fixture(autouse=True)
def pulumi_mocks(monkeypatch):
    # Mock infra.__init__ exported objects
    mock_use_case = MagicMock()
    mock_use_case.id = "mock-use-case-id"
    mock_project_dir = Path("/mock/project/dir")
    monkeypatch.setattr("infra.use_case", mock_use_case)
    monkeypatch.setattr("infra.project_dir", mock_project_dir)

    # Mock pulumi_datarobot resources
    monkeypatch.setattr("pulumi_datarobot.ExecutionEnvironment", MagicMock())
    monkeypatch.setattr("pulumi_datarobot.CustomModel", MagicMock())
    monkeypatch.setattr("pulumi_datarobot.PredictionEnvironment", MagicMock())
    monkeypatch.setattr(
        "pulumi_datarobot.DeploymentAssociationIdSettingsArgs", MagicMock()
    )
    monkeypatch.setattr(
        "pulumi_datarobot.DeploymentPredictionsDataCollectionSettingsArgs", MagicMock()
    )
    monkeypatch.setattr(
        "pulumi_datarobot.DeploymentPredictionsSettingsArgs", MagicMock()
    )
    monkeypatch.setattr(
        "pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs", MagicMock()
    )

    # Patch the id property of the RuntimeEnvironment instance for PYTHON_311_GENAI_AGENTS
    from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironments

    patcher = patch.object(
        RuntimeEnvironments.PYTHON_311_GENAI_AGENTS.value.__class__,
        "id",
        new_callable=PropertyMock,
        return_value="python-311-genai-agents-id",
    )
    patcher.start()

    # Mock pulumi functions
    monkeypatch.setattr("pulumi.export", MagicMock())
    monkeypatch.setattr("pulumi.info", MagicMock())

    # Mock CustomModelDeployment
    monkeypatch.setattr(
        "datarobot_pulumi_utils.pulumi.custom_model_deployment.CustomModelDeployment",
        MagicMock(),
    )

    # Mock Output to behave like a Pulumi Output with .apply() and support subscript notation
    class MockOutput(MagicMock):
        def __new__(cls, val=None, *args, **kwargs):
            m = super().__new__(cls)
            m.apply = MagicMock(side_effect=lambda fn: fn(val))
            return m

        @classmethod
        def __class_getitem__(cls, item):
            return cls

    monkeypatch.setattr("pulumi.Output", MockOutput)

    yield
    patcher.stop()


def test_execution_environment_not_set(monkeypatch):
    """Test execution environment creation when DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT is not set"""
    monkeypatch.delenv("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", raising=False)

    import importlib
    import infra.agent_crewai as agent_infra

    # Reset the mock to clear calls from the initial import
    agent_infra.pulumi_datarobot.ExecutionEnvironment.reset_mock()
    importlib.reload(agent_infra)

    # Check that ExecutionEnvironment constructor was called correctly
    agent_infra.pulumi_datarobot.ExecutionEnvironment.assert_called_once()
    args, kwargs = agent_infra.pulumi_datarobot.ExecutionEnvironment.call_args

    assert (
        kwargs["resource_name"]
        == "Execution Environment [docker_context] [agent_crewai]"
    )
    assert kwargs["programming_language"] == "python"
    assert kwargs["description"] == "Execution Environment [agent docker_context]"
    assert "docker_context_path" in kwargs
    assert kwargs["use_cases"] == ["customModel", "notebook"]

    # ExecutionEnvironment.get should not be called when env var is not set
    agent_infra.pulumi_datarobot.ExecutionEnvironment.get.assert_not_called()


def test_execution_environment_default_set(monkeypatch):
    """Test execution environment when DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT is set to default value"""
    monkeypatch.setenv(
        "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT",
        "[DataRobot] Python 3.11 GenAI Agents",
    )

    import importlib
    import infra.agent_crewai as agent_infra

    importlib.reload(agent_infra)

    # Check that pulumi.info was called with the correct message
    agent_infra.pulumi.info.assert_any_call(
        "Using default GenAI Agents execution environment [DataRobot] Python 3.11 GenAI Agents"
    )

    # Check that ExecutionEnvironment.get was called with the correct parameters
    agent_infra.pulumi_datarobot.ExecutionEnvironment.get.assert_called_once()
    args, kwargs = agent_infra.pulumi_datarobot.ExecutionEnvironment.get.call_args

    assert kwargs["id"] == "python-311-genai-agents-id"
    assert (
        kwargs["resource_name"] == "Execution Environment [PRE-EXISTING] [agent_crewai]"
    )

    # ExecutionEnvironment constructor should not be called when using default env
    agent_infra.pulumi_datarobot.ExecutionEnvironment.assert_not_called()


def test_execution_environment_custom_set(monkeypatch):
    """Test execution environment when DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT is set to a custom value"""
    monkeypatch.setenv(
        "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", "Custom Execution Environment"
    )

    import importlib
    import infra.agent_crewai as agent_infra

    importlib.reload(agent_infra)

    # Check that pulumi.info was called with the correct message
    agent_infra.pulumi.info.assert_any_call(
        "Using existing execution environment Custom Execution Environment"
    )

    # Check that ExecutionEnvironment.get was called with the correct parameters
    agent_infra.pulumi_datarobot.ExecutionEnvironment.get.assert_called_once()
    args, kwargs = agent_infra.pulumi_datarobot.ExecutionEnvironment.get.call_args

    assert kwargs["id"] == "Custom Execution Environment"
    assert (
        kwargs["resource_name"] == "Execution Environment [PRE-EXISTING] [agent_crewai]"
    )

    # ExecutionEnvironment constructor should not be called when using custom env
    agent_infra.pulumi_datarobot.ExecutionEnvironment.assert_not_called()


def test_reset_environment_between_tests():
    """Test to ensure that environment variables don't leak between tests"""
    # This test should run with no environment variables set from previous tests
    assert os.environ.get("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT") is None

    import importlib
    import infra.agent_crewai as agent_infra

    importlib.reload(agent_infra)

    # Default behavior should be to create a new execution environment
    agent_infra.pulumi_datarobot.ExecutionEnvironment.assert_called_once()
    agent_infra.pulumi_datarobot.ExecutionEnvironment.get.assert_not_called()


def test_custom_model_created(monkeypatch):
    """Test that pulumi_datarobot.CustomModel is created with correct arguments."""
    monkeypatch.delenv("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", raising=False)

    import importlib
    import infra.agent_crewai as agent_infra

    # Reset the mock to clear calls from the initial import
    agent_infra.pulumi_datarobot.CustomModel.reset_mock()
    importlib.reload(agent_infra)

    agent_infra.pulumi_datarobot.CustomModel.assert_called_once()
    args, kwargs = agent_infra.pulumi_datarobot.CustomModel.call_args
    assert kwargs["resource_name"].startswith("Custom Model")
    assert (
        kwargs["base_environment_id"]
        == agent_infra.agent_crewai_execution_environment.id
    )
    assert (
        kwargs["base_environment_version_id"]
        == agent_infra.agent_crewai_execution_environment.version_id
    )
    assert kwargs["target_type"] == "AgenticWorkflow"
    assert kwargs["target_name"] == "response"
    assert kwargs["language"] == "python"
    assert kwargs["use_case_ids"] == [agent_infra.use_case.id]
    assert isinstance(kwargs["files"], list)
    assert kwargs["runtime_parameter_values"] == []


def test_agent_deployment_created_when_env(monkeypatch):
    """Test that agent deployment resources are created when AGENT_DEPLOY is not '0'."""
    monkeypatch.setenv("AGENT_DEPLOY", "1")
    monkeypatch.delenv("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", raising=False)

    import importlib
    import infra.agent_crewai as agent_infra

    # Reset mocks to clear calls from the initial import
    agent_infra.pulumi_datarobot.PredictionEnvironment.reset_mock()
    agent_infra.pulumi_datarobot.DeploymentAssociationIdSettingsArgs.reset_mock()
    agent_infra.pulumi_datarobot.DeploymentPredictionsDataCollectionSettingsArgs.reset_mock()
    agent_infra.pulumi_datarobot.DeploymentPredictionsSettingsArgs.reset_mock()
    agent_infra.CustomModelDeployment.reset_mock()
    importlib.reload(agent_infra)

    # Check that PredictionEnvironment was created
    agent_infra.pulumi_datarobot.PredictionEnvironment.assert_called_once()
    # Check that CustomModelDeployment was created
    agent_infra.CustomModelDeployment.assert_called_once()
    # Check that pulumi.export was called for deployment id and endpoint
    agent_infra.pulumi.export.assert_any_call(
        "Agent Deployment ID " + agent_infra.agent_crewai_resource_name,
        agent_infra.CustomModelDeployment.return_value.id,
    )
    agent_infra.pulumi.export.assert_any_call(
        "Agent Deployment Chat Endpoint " + agent_infra.agent_crewai_resource_name,
        agent_infra.CustomModelDeployment.return_value.id.apply.return_value,
    )


def test_agent_deployment_not_created_when_env_zero(monkeypatch):
    """Test that agent deployment resources are not created when AGENT_DEPLOY is '0'."""
    monkeypatch.setenv("AGENT_DEPLOY", "0")
    monkeypatch.delenv("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", raising=False)

    import importlib
    import infra.agent_crewai as agent_infra

    # Reset mocks to clear calls from the initial import
    agent_infra.pulumi_datarobot.PredictionEnvironment.reset_mock()
    agent_infra.CustomModelDeployment.reset_mock()
    importlib.reload(agent_infra)

    # Check that PredictionEnvironment and CustomModelDeployment were not called
    agent_infra.pulumi_datarobot.PredictionEnvironment.assert_not_called()
    agent_infra.CustomModelDeployment.assert_not_called()


class TestGetCustomModelFiles:
    def test_get_custom_model_files_basic(self, tmp_path):
        import infra.agent_crewai as agent_infra

        # Create a simple file structure
        (tmp_path / "file1.py").write_text("print('hi')")
        (tmp_path / "file2.txt").write_text("hello")
        files = agent_infra.get_custom_model_files(str(tmp_path))
        file_names = [f[1] for f in files]
        assert "file1.py" in file_names
        assert "file2.txt" in file_names
        assert len(files) == 2

    def test_get_custom_model_files_excludes(self, tmp_path):
        import infra.agent_crewai as agent_infra

        # Create files that should be excluded
        (tmp_path / "file1.py").write_text("print('hi')")
        (tmp_path / ".DS_Store").write_text("")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "foo.pyc").write_text("")
        files = agent_infra.get_custom_model_files(str(tmp_path))
        file_names = [f[1] for f in files]
        assert "file1.py" in file_names
        assert ".DS_Store" not in file_names
        assert "__pycache__/foo.pyc" not in file_names
        assert len(files) == 1

    def test_get_custom_model_files_symlinks(self, tmp_path):
        import infra.agent_crewai as agent_infra

        # Create a real file and a symlink to it
        real_file = tmp_path / "real.py"
        real_file.write_text("print('hi')")
        symlink_dir = tmp_path / "symlink_dir"
        symlink_dir.mkdir()
        symlink = symlink_dir / "link.py"
        symlink.symlink_to(real_file)
        files = agent_infra.get_custom_model_files(str(tmp_path))
        file_names = [f[1] for f in files]
        assert "real.py" in file_names
