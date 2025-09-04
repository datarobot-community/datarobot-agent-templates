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
from typing import cast

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

# To use the LLM DataRobot Deployment in your Agent, uncomment the line below
# from .llm_datarobot import app_runtime_parameters as llm_datarobot_app_runtime_parameters

DEFAULT_EXECUTION_ENVIRONMENT = "[DataRobot] Python 3.11 GenAI Agents"

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
    "agent_llamaindex_application_name",
    "agent_llamaindex_resource_name",
    "agent_llamaindex_application_path",
    "agent_llamaindex_execution_environment_id",
    "agent_llamaindex_prediction_environment",
    "agent_llamaindex_custom_model",
    "agent_llamaindex_agent_deployment_id",
    "agent_llamaindex_registered_model_args",
    "agent_llamaindex_deployment_args",
    "agent_llamaindex_agent_deployment",
    "agent_llamaindex_app_runtime_parameters",
]

agent_llamaindex_application_name: str = "agent_llamaindex"
agent_llamaindex_resource_name: str = "[agent_llamaindex]"
agent_llamaindex_asset_name: str = f"[{PROJECT_NAME}] agent_llamaindex"
agent_llamaindex_application_path = project_dir.parent / "agent_llamaindex"


def get_custom_model_files(custom_model_folder: str) -> list[tuple[str, str]]:
    # Get all files from application path, following symlinks
    # When we've upgraded to Python 3.13 we can use Path.glob(reduce_symlinks=True)
    # https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.glob
    source_files = []
    for dirpath, dirnames, filenames in os.walk(custom_model_folder, followlinks=True):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, custom_model_folder)
            source_files.append((os.path.abspath(file_path), rel_path))
    source_files = [
        (file_path, file_name)
        for file_path, file_name in source_files
        if not any(
            exclude_pattern.match(file_name) for exclude_pattern in EXCLUDE_PATTERNS
        )
    ]
    return source_files


# Start of Pulumi settings and application infrastructure
if len(os.environ.get("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", "")) > 0:
    agent_llamaindex_execution_environment_id = os.environ[
        "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT"
    ]

    if agent_llamaindex_execution_environment_id == DEFAULT_EXECUTION_ENVIRONMENT:
        pulumi.info(
            "Using default GenAI Agents execution environment "
            + agent_llamaindex_execution_environment_id
        )
        agent_llamaindex_execution_environment = (
            pulumi_datarobot.ExecutionEnvironment.get(
                id=RuntimeEnvironments.PYTHON_311_GENAI_AGENTS.value.id,
                resource_name="Execution Environment [PRE-EXISTING] "
                + agent_llamaindex_resource_name,
            )
        )
    else:
        pulumi.info(
            "Using existing execution environment "
            + agent_llamaindex_execution_environment_id
        )
        agent_llamaindex_execution_environment = (
            pulumi_datarobot.ExecutionEnvironment.get(
                id=agent_llamaindex_execution_environment_id,
                resource_name="Execution Environment [PRE-EXISTING] "
                + agent_llamaindex_resource_name,
            )
        )
else:
    agent_llamaindex_exec_env_use_cases = ["customModel", "notebook"]
    if os.path.exists(
        os.path.join(str(agent_llamaindex_application_path), "docker_context.tar.gz")
    ):
        pulumi.info(
            "Using prebuilt Dockerfile docker_context.tar.gz to run the execution environment"
        )
        agent_llamaindex_execution_environment = pulumi_datarobot.ExecutionEnvironment(
            resource_name="Execution Environment [docker_context] "
            + agent_llamaindex_resource_name,
            name=agent_llamaindex_asset_name,
            description="Execution Environment for " + agent_llamaindex_asset_name,
            programming_language="python",
            docker_image=os.path.join(
                str(agent_llamaindex_application_path), "docker_context.tar.gz"
            ),
            use_cases=agent_llamaindex_exec_env_use_cases,
        )
    else:
        pulumi.info("Using docker_context folder to compile the execution environment")
        agent_llamaindex_execution_environment = pulumi_datarobot.ExecutionEnvironment(
            resource_name="Execution Environment [docker_context] "
            + agent_llamaindex_resource_name,
            name=agent_llamaindex_asset_name,
            description="Execution Environment for " + agent_llamaindex_asset_name,
            programming_language="python",
            docker_context_path=os.path.join(
                str(agent_llamaindex_application_path), "docker_context"
            ),
            use_cases=agent_llamaindex_exec_env_use_cases,
        )

agent_llamaindex_custom_model_files = get_custom_model_files(
    str(os.path.join(str(agent_llamaindex_application_path), "custom_model"))
)

agent_llamaindex_runtime_parameters = []
if os.environ.get("LLM_DATAROBOT_DEPLOYMENT_ID"):
    agent_llamaindex_runtime_parameters = [
        pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
            key="LLM_DATAROBOT_DEPLOYMENT_ID",
            type="string",
            value=os.environ["LLM_DATAROBOT_DEPLOYMENT_ID"],
        ),
    ]
elif os.environ.get("USE_DATAROBOT_LLM_GATEWAY") in [0, "0", False, "false", "False"]:
    from .llm_datarobot import app_runtime_parameters  # type: ignore[import-not-found]

    agent_llamaindex_runtime_parameters = app_runtime_parameters  # type: ignore

agent_llamaindex_custom_model = pulumi_datarobot.CustomModel(
    resource_name="Custom Model " + agent_llamaindex_resource_name,
    name=agent_llamaindex_asset_name,
    base_environment_id=agent_llamaindex_execution_environment.id,
    base_environment_version_id=agent_llamaindex_execution_environment.version_id,
    target_type="AgenticWorkflow",
    target_name="response",
    language="python",
    use_case_ids=[use_case.id],
    files=agent_llamaindex_custom_model_files,
    runtime_parameter_values=agent_llamaindex_runtime_parameters,
)

agent_llamaindex_custom_model_endpoint = agent_llamaindex_custom_model.id.apply(
    lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/genai/agents/fromCustomModel/{id}/chat/"
)

agent_llamaindex_playground = pulumi_datarobot.Playground(
    name=agent_llamaindex_asset_name,
    resource_name="Agentic Playground " + agent_llamaindex_resource_name,
    description="Experimentation Playground for " + agent_llamaindex_asset_name,
    use_case_id=use_case.id,
    playground_type="agentic",
)

agent_llamaindex_blueprint = pulumi_datarobot.LlmBlueprint(
    name=agent_llamaindex_asset_name,
    resource_name="LLM Blueprint " + agent_llamaindex_resource_name,
    playground_id=agent_llamaindex_playground.id,
    llm_id="chat-interface-custom-model",
    llm_settings=pulumi_datarobot.LlmBlueprintLlmSettingsArgs(
        custom_model_id=agent_llamaindex_custom_model.id
    ),
    prompt_type="ONE_TIME_PROMPT",
)

datarobot_url = (
    os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
    .rstrip("/")
    .rstrip("/api/v2")
)

agent_llamaindex_playground_url = pulumi.Output.format(
    "{0}/usecases/{1}/agentic-playgrounds/{2}/comparison/chats",
    datarobot_url,
    use_case.id,
    agent_llamaindex_playground.id,
)


# Export the IDs of the created resources
pulumi.export("Agent Use Case ID " + agent_llamaindex_asset_name, use_case.id)
pulumi.export(
    "Agent Execution Environment ID " + agent_llamaindex_asset_name,
    agent_llamaindex_execution_environment.id,
)
pulumi.export(
    "Agent Custom Model ID " + agent_llamaindex_asset_name,
    agent_llamaindex_custom_model.id,
)
pulumi.export(
    "Agent Custom Model Chat Endpoint " + agent_llamaindex_asset_name,
    agent_llamaindex_custom_model_endpoint,
)
pulumi.export("Agent Playground URL " + agent_llamaindex_asset_name, agent_llamaindex_playground_url)  # fmt: skip


agent_llamaindex_agent_deployment_id: pulumi.Output[str] = cast(
    pulumi.Output[str], "None"
)
if os.environ.get("AGENT_DEPLOY") != "0":
    agent_llamaindex_prediction_environment = pulumi_datarobot.PredictionEnvironment(
        resource_name="Prediction Environment " + agent_llamaindex_resource_name,
        name=agent_llamaindex_asset_name,
        platform=dr.enums.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,
        opts=pulumi.ResourceOptions(retain_on_delete=True),
    )

    agent_llamaindex_registered_model_args = RegisteredModelArgs(
        resource_name="Registered Model " + agent_llamaindex_resource_name,
        name=agent_llamaindex_asset_name,
    )

    agent_llamaindex_deployment_args = DeploymentArgs(
        resource_name="Deployment " + agent_llamaindex_resource_name,
        label=agent_llamaindex_asset_name,
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

    agent_llamaindex_agent_deployment = CustomModelDeployment(
        resource_name="Chat Deployment " + agent_llamaindex_resource_name,
        use_case_ids=[use_case.id],
        custom_model_version_id=agent_llamaindex_custom_model.version_id,
        prediction_environment=agent_llamaindex_prediction_environment,
        registered_model_args=agent_llamaindex_registered_model_args,
        deployment_args=agent_llamaindex_deployment_args,
    )
    agent_llamaindex_agent_deployment_id = agent_llamaindex_agent_deployment.id.apply(
        lambda id: f"{id}"
    )
    agent_llamaindex_deployment_endpoint = agent_llamaindex_agent_deployment.id.apply(
        lambda id: f"{os.getenv('DATAROBOT_ENDPOINT')}/deployments/{id}/chat/completions"
    )

    pulumi.export(
        "Agent Deployment ID " + agent_llamaindex_asset_name,
        agent_llamaindex_agent_deployment.id,
    )
    export(
        agent_llamaindex_application_name.upper() + "_DEPLOYMENT_ID",
        agent_llamaindex_agent_deployment.id,
    )
    pulumi.export(
        "Agent Deployment Chat Endpoint " + agent_llamaindex_asset_name,
        agent_llamaindex_deployment_endpoint,
    )

agent_llamaindex_app_runtime_parameters = [
    pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=agent_llamaindex_application_name.upper() + "_DEPLOYMENT_ID",
        type="string",
        value=agent_llamaindex_agent_deployment_id,
    ),
]
