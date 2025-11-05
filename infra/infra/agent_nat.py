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
import re
import shutil
from typing import cast, Final

import datarobot as dr
import pulumi
import pulumi_datarobot
from datarobot_pulumi_utils.pulumi import export
from datarobot_pulumi_utils.pulumi.custom_model_deployment import CustomModelDeployment
from datarobot_pulumi_utils.pulumi.stack import PROJECT_NAME
from datarobot_pulumi_utils.schema.custom_models import (
    DeploymentArgs,
    RegisteredModelArgs,
)
from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironments

from . import project_dir, use_case

from .llm import custom_model_runtime_parameters as llm_custom_model_runtime_parameters

DEFAULT_EXECUTION_ENVIRONMENT = "Python 3.11 GenAI Agents"

EXCLUDE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r".*tests/.*",
        r".*\.coverage",
        r".*\.DS_Store",
        r".*\.pyc",
        r".*\.ruff_cache/.*",
        r".*\.venv/.*",
        r".*\.mypy_cache/.*",
        r".*__pycache__/.*",
        r".*\.pytest_cache/.*",
    ]
]


__all__ = [
    "agent_nat_application_name",
    "agent_nat_application_path",
    "agent_nat_execution_environment_id",
    "agent_nat_prediction_environment",
    "agent_nat_custom_model",
    "agent_nat_agent_deployment_id",
    "agent_nat_registered_model_args",
    "agent_nat_deployment_args",
    "agent_nat_agent_deployment",
    "agent_nat_app_runtime_parameters",
]

agent_nat_application_name: str = "agent_nat"
agent_nat_asset_name: str = f"[{PROJECT_NAME}] [agent_nat]"
agent_nat_application_path = project_dir.parent / "agent_nat"

SESSION_SECRET_KEY: Final[str] = "SESSION_SECRET_KEY"
session_secret_key = os.environ.get(SESSION_SECRET_KEY)


def get_custom_model_files(custom_model_folder: str) -> list[tuple[str, str]]:
    # Get all files from application path, following symlinks
    # When we've upgraded to Python 3.13 we can use Path.glob(reduce_symlinks=True)
    # https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.glob
    source_files = []
    for dirpath, dirnames, filenames in os.walk(custom_model_folder, followlinks=True):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, custom_model_folder)
            # Convert to forward slashes for Linux destination
            rel_path = rel_path.replace(os.path.sep, "/")
            source_files.append((os.path.abspath(file_path), rel_path))
    source_files = [
        (file_path, file_name)
        for file_path, file_name in source_files
        if not any(
            exclude_pattern.match(file_name) for exclude_pattern in EXCLUDE_PATTERNS
        )
    ]
    return source_files


def synchronize_pyproject_dependencies():
    pyproject_toml_path = os.path.join(
        str(agent_nat_application_path), "pyproject.toml"
    )
    uv_lock_path = os.path.join(str(agent_nat_application_path), "uv.lock")
    custom_model_folder = str(
        os.path.join(str(agent_nat_application_path), "custom_model")
    )
    docker_context_folder = str(
        os.path.join(str(agent_nat_application_path), "docker_context")
    )

    # Check if pyproject.toml exists in the application path
    if not os.path.exists(pyproject_toml_path):
        return

    # Copy pyproject.toml to custom_model folder if it exists
    if os.path.exists(custom_model_folder):
        custom_model_pyproject_path = os.path.join(
            custom_model_folder, "pyproject.toml"
        )
        shutil.copy2(pyproject_toml_path, custom_model_pyproject_path)
        if os.path.exists(uv_lock_path):
            custom_model_uv_lock_path = os.path.join(custom_model_folder, "uv.lock")
            shutil.copy2(uv_lock_path, custom_model_uv_lock_path)

    # Copy pyproject.toml to docker_context folder if it exists
    if os.path.exists(docker_context_folder):
        docker_context_pyproject_path = os.path.join(
            docker_context_folder, "pyproject.toml"
        )
        shutil.copy2(pyproject_toml_path, docker_context_pyproject_path)
        if os.path.exists(uv_lock_path):
            docker_context_uv_lock_path = os.path.join(docker_context_folder, "uv.lock")
            shutil.copy2(uv_lock_path, docker_context_uv_lock_path)


synchronize_pyproject_dependencies()
pulumi.info("NOTE: [unknown] values will be populated after performing an update.")  # fmt: skip

# Start of Pulumi settings and application infrastructure
if len(os.environ.get("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", "")) > 0:
    agent_nat_execution_environment_id = os.environ[
        "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT"
    ]

    if DEFAULT_EXECUTION_ENVIRONMENT in agent_nat_execution_environment_id:
        pulumi.info(
            "Using default GenAI Agents execution environment "
            + agent_nat_execution_environment_id
        )
        agent_nat_execution_environment = pulumi_datarobot.ExecutionEnvironment.get(
            id=RuntimeEnvironments.PYTHON_311_GENAI_AGENTS.value.id,
            resource_name=agent_nat_asset_name + " Execution Environment",
        )
    else:
        pulumi.info(
            "Using existing execution environment " + agent_nat_execution_environment_id
        )
        agent_nat_execution_environment = pulumi_datarobot.ExecutionEnvironment.get(
            id=agent_nat_execution_environment_id,
            resource_name=agent_nat_asset_name + " Execution Environment",
        )
else:
    agent_nat_exec_env_use_cases = ["customModel", "notebook"]
    if os.path.exists(
        os.path.join(str(agent_nat_application_path), "docker_context.tar.gz")
    ):
        pulumi.info(
            "Using prebuilt Dockerfile docker_context.tar.gz to run the execution environment"
        )
        agent_nat_execution_environment = pulumi_datarobot.ExecutionEnvironment(
            resource_name=agent_nat_asset_name + " Execution Environment",
            name=agent_nat_asset_name + " Execution Environment",
            description="Execution Environment for " + agent_nat_asset_name,
            programming_language="python",
            docker_image=os.path.join(
                str(agent_nat_application_path), "docker_context.tar.gz"
            ),
            use_cases=agent_nat_exec_env_use_cases,
        )
    else:
        pulumi.info("Using docker_context folder to compile the execution environment")
        agent_nat_execution_environment = pulumi_datarobot.ExecutionEnvironment(
            resource_name=agent_nat_asset_name + " Execution Environment",
            name=agent_nat_asset_name + " Execution Environment",
            description="Execution Environment for " + agent_nat_asset_name,
            programming_language="python",
            docker_context_path=os.path.join(
                str(agent_nat_application_path), "docker_context"
            ),
            use_cases=agent_nat_exec_env_use_cases,
        )

agent_nat_custom_model_files = get_custom_model_files(
    str(os.path.join(str(agent_nat_application_path), "custom_model"))
)

pulumi.export("SESSION_SECRET_KEY", session_secret_key)
session_secret_cred = pulumi_datarobot.ApiTokenCredential(
    "agent_nat Session Secret Key",
    args=pulumi_datarobot.ApiTokenCredentialArgs(
        api_token=str(session_secret_key),
    ),
)
custom_model_credential_runtime_parameters = [
    pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
        type="string",
        key=SESSION_SECRET_KEY,
        value=session_secret_cred.id.apply(lambda id: str(id)),
    ),
]

agent_nat_custom_model = pulumi_datarobot.CustomModel(
    resource_name=agent_nat_asset_name + " Custom Model",
    name=agent_nat_asset_name + " Custom Model",
    base_environment_id=agent_nat_execution_environment.id,
    base_environment_version_id=agent_nat_execution_environment.version_id,
    target_type="AgenticWorkflow",
    target_name="response",
    language="python",
    use_case_ids=[use_case.id],
    files=agent_nat_custom_model_files,
    runtime_parameter_values=llm_custom_model_runtime_parameters
    + custom_model_credential_runtime_parameters,
)

agent_nat_custom_model_endpoint = agent_nat_custom_model.id.apply(
    lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/genai/agents/fromCustomModel/{id}/chat/"
)

agent_nat_playground = pulumi_datarobot.Playground(
    name=agent_nat_asset_name + " Agentic Playground",
    resource_name=agent_nat_asset_name + " Agentic Playground",
    description="Experimentation Playground for " + agent_nat_asset_name,
    use_case_id=use_case.id,
    playground_type="agentic",
)

agent_nat_blueprint = pulumi_datarobot.LlmBlueprint(
    name=agent_nat_asset_name + " LLM Blueprint",
    resource_name=agent_nat_asset_name + " LLM Blueprint",
    playground_id=agent_nat_playground.id,
    llm_id="chat-interface-custom-model",
    llm_settings=pulumi_datarobot.LlmBlueprintLlmSettingsArgs(
        custom_model_id=agent_nat_custom_model.id
    ),
    prompt_type="ONE_TIME_PROMPT",
)

datarobot_url = (
    os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
    .rstrip("/")
    .rstrip("/api/v2")
)

agent_nat_playground_url = pulumi.Output.format(
    "{0}/usecases/{1}/agentic-playgrounds/{2}/comparison/chats",
    datarobot_url,
    use_case.id,
    agent_nat_playground.id,
)


# Export the IDs of the created resources
pulumi.export(
    "Agent Execution Environment ID " + agent_nat_asset_name,
    agent_nat_execution_environment.id,
)
pulumi.export(
    "Agent Custom Model Chat Endpoint " + agent_nat_asset_name,
    agent_nat_custom_model_endpoint,
)
pulumi.export("Agent Playground URL " + agent_nat_asset_name, agent_nat_playground_url)  # fmt: skip


agent_nat_agent_deployment_id: pulumi.Output[str] = cast(pulumi.Output[str], "None")
if os.environ.get("AGENT_DEPLOY") != "0":
    agent_nat_prediction_environment = pulumi_datarobot.PredictionEnvironment(
        resource_name=agent_nat_asset_name + " Prediction Environment",
        name=agent_nat_asset_name + " Prediction Environment",
        platform=dr.enums.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,
        opts=pulumi.ResourceOptions(retain_on_delete=False),
    )

    agent_nat_registered_model_args = RegisteredModelArgs(
        resource_name=agent_nat_asset_name + " Registered Model",
        name=agent_nat_asset_name + " Registered Model",
    )

    agent_nat_deployment_args = DeploymentArgs(
        resource_name=agent_nat_asset_name + " Deployment",
        label=agent_nat_asset_name + " Deployment",
        association_id_settings=pulumi_datarobot.DeploymentAssociationIdSettingsArgs(
            column_names=["association_id"],
            auto_generate_id=False,
            required_in_prediction_requests=True,
        ),
        predictions_data_collection_settings=(
            pulumi_datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
                enabled=True
            )
        ),
        predictions_settings=(
            pulumi_datarobot.DeploymentPredictionsSettingsArgs(
                min_computes=0, max_computes=2
            )
        ),
    )

    agent_nat_agent_deployment = CustomModelDeployment(
        resource_name=agent_nat_asset_name + " Chat Deployment",
        use_case_ids=[use_case.id],
        custom_model_version_id=agent_nat_custom_model.version_id,
        prediction_environment=agent_nat_prediction_environment,
        registered_model_args=agent_nat_registered_model_args,
        deployment_args=agent_nat_deployment_args,
    )
    agent_nat_agent_deployment_id = agent_nat_agent_deployment.id.apply(
        lambda id: f"{id}"
    )
    agent_nat_deployment_endpoint = agent_nat_agent_deployment.id.apply(
        lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"
    )

    export(
        agent_nat_application_name.upper() + "_DEPLOYMENT_ID",
        agent_nat_agent_deployment.id,
    )
    pulumi.export(
        "Agent Deployment Chat Endpoint " + agent_nat_asset_name,
        agent_nat_deployment_endpoint,
    )

agent_nat_app_runtime_parameters = [
    pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=agent_nat_application_name.upper() + "_DEPLOYMENT_ID",
        type="string",
        value=agent_nat_agent_deployment_id,
    ),
]

# Add MCP runtime parameters if configured
if os.environ.get("MCP_DEPLOYMENT_ID"):
    mcp_deployment_id = os.environ["MCP_DEPLOYMENT_ID"]
    agent_nat_app_runtime_parameters.append(
        pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
            key="MCP_DEPLOYMENT_ID",
            type="string",
            value=mcp_deployment_id,
        )
    )
    pulumi.info(f"MCP configured with DataRobot MCP Server: {mcp_deployment_id}")

# Allow external mcp server.  Currently code will use MCP_DEPLOYMENT_ID first and if that is empty
# then use the EXTERNAL_MCP_URL
if os.environ.get("EXTERNAL_MCP_URL"):
    external_mcp_url = os.environ["EXTERNAL_MCP_URL"].rstrip("/")
    agent_nat_app_runtime_parameters.append(
        pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
            key="EXTERNAL_MCP_URL",
            type="string",
            value=external_mcp_url,
        )
    )
    pulumi.info(f"MCP configured with external server: {external_mcp_url}")
