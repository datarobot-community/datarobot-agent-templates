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

import datarobot as dr
import pulumi
import pulumi_datarobot
from datarobot_pulumi_utils.pulumi.custom_model_deployment import CustomModelDeployment
from datarobot_pulumi_utils.pulumi.stack import PROJECT_NAME
from datarobot_pulumi_utils.schema.custom_models import (
    DeploymentArgs,
    RegisteredModelArgs,
)

from . import project_dir, use_case

EXCLUDE_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"tests.*",
        r"\.coverage",
        r".*\.DS_Store",
        r".*\.pyc",
        r"\.ruff_cache.*",
        r"\.venv.*",
        r"\.mypy_cache.*",
        r"__pycache__.*",
        r"\.pytest_cache.*",
    ]
]


__all__ = [
    "agent_langgraph_application_name",
    "agent_langgraph_resource_name",
    "agent_langgraph_application_path",
]

agent_langgraph_application_name: str = "agent_langgraph"
agent_langgraph_resource_name: str = "[agent_langgraph]"
agent_langgraph_application_path = project_dir.parent / "agent_langgraph"


# Start of Pulumi settings and application infrastructure
if "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT" in os.environ:
    execution_environment_id = os.environ["DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT"]
    pulumi.info(f"Using existing execution environment '{execution_environment_id}'")
    execution_environment = pulumi_datarobot.ExecutionEnvironment.get(
        id=execution_environment_id,
        resource_name="Execution Environment [PRE-EXISTING]",
    )
else:
    execution_environment = pulumi_datarobot.ExecutionEnvironment(
        resource_name="Agent Python 3.11 " + agent_langgraph_resource_name,
        programming_language="python",
        description="DataRobot Agent Execution Environment [Python 3.11]",
        docker_context_path=os.path.join(
            str(agent_langgraph_application_path), "docker_context"
        ),
        use_cases=["customModel", "notebook"],
    )

prediction_environment = pulumi_datarobot.PredictionEnvironment(
    resource_name="Agent Prediction Environment " + agent_langgraph_resource_name,
    platform=dr.enums.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,
)

custom_model = pulumi_datarobot.CustomModel(
    resource_name="Agent Custom Model " + agent_langgraph_resource_name,
    base_environment_id=execution_environment.id,
    target_type=dr.TARGET_TYPE.TEXT_GENERATION,
    target_name="response",
    language="python",
    runtime_parameter_values=[],
    use_case_ids=[use_case.id],
    folder_path=os.path.join(str(agent_langgraph_application_path), "custom_model"),
)

registered_model_args = RegisteredModelArgs(
    resource_name="Agent Registered Model " + agent_langgraph_resource_name,
)

deployment_args = DeploymentArgs(
    resource_name="Agent Deployment " + agent_langgraph_resource_name,
    label=f"Agent Deployment [{PROJECT_NAME}] " + agent_langgraph_resource_name,
    association_id_settings=pulumi_datarobot.DeploymentAssociationIdSettingsArgs(
        column_names=["association_id"],
        auto_generate_id=False,
        required_in_prediction_requests=True,
    ),
    predictions_data_collection_settings=(
        pulumi_datarobot.DeploymentPredictionsDataCollectionSettingsArgs(enabled=True)
    ),
    predictions_settings=(
        pulumi_datarobot.DeploymentPredictionsSettingsArgs(
            min_computes=0, max_computes=2
        )
    ),
)

agent_deployment = CustomModelDeployment(
    resource_name="Agent Chat Deployment " + agent_langgraph_resource_name,
    use_case_ids=[use_case.id],
    custom_model_version_id=custom_model.version_id,
    prediction_environment=prediction_environment,
    registered_model_args=registered_model_args,
    deployment_args=deployment_args,
)

app_runtime_parameters = [
    pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=agent_langgraph_application_name.upper() + "_DEPLOYMENT_ID",
        type="deployment",
        value=agent_deployment.id,
    ),
]

pulumi.export("Use Case ID " + agent_langgraph_resource_name, use_case.id)
pulumi.export(
    "Execution Environment ID " + agent_langgraph_resource_name,
    execution_environment.id,
)
pulumi.export("Deployment ID " + agent_langgraph_resource_name, agent_deployment.id)
