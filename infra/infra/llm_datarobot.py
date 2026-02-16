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

import datarobot as dr
import pulumi
import pulumi_datarobot as datarobot
from datarobot_pulumi_utils.pulumi.stack import PROJECT_NAME
from datarobot_pulumi_utils.pulumi.custom_model_deployment import (
    CustomModelDeployment,
    DeploymentArgs,
    RegisteredModelArgs,
)
from datarobot_pulumi_utils.schema.custom_models import CustomModelArgs
from datarobot_pulumi_utils.schema.llms import (
    LLMSettings,
    LLMBlueprintArgs,
)
from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironments

from . import use_case

# To use the LLM DataRobot Deployment please disable the LLM Gateway by setting the environment variable
# Optionally, you may delete the check below if you ALWAYS want to deploy an LLM on DataRobot
if os.environ.get("USE_DATAROBOT_LLM_GATEWAY") not in [0, "0", False, "false", "False"]:
    exit()

__all__ = [
    "llm_datarobot_application_name",
    "llm_datarobot_resource_name",
]

llm_datarobot_application_name: str = "llm_datarobot"
llm_datarobot_resource_name: str = "[llm_datarobot]"

playground = datarobot.Playground(
    use_case_id=use_case.id,
    resource_name="LLM Playground " + llm_datarobot_resource_name,
)

llm_blueprint_args = LLMBlueprintArgs(
    resource_name="LLM Blueprint " + llm_datarobot_resource_name,
    llm_id="azure-openai-gpt-4",
    llm_settings=LLMSettings(
        max_completion_length=2048,
        temperature=0.1,
        top_p=None,
    ),
)

llm_blueprint = datarobot.LlmBlueprint(
    playground_id=playground.id,
    **llm_blueprint_args.model_dump(),
)

custom_model_args = CustomModelArgs(
    resource_name="LLM Custom Model " + llm_datarobot_resource_name,
    name="LLM Custom Model " + llm_datarobot_resource_name,
    target_name="resultText",
    target_type=dr.enums.TARGET_TYPE.TEXT_GENERATION,
    replicas=1,
    base_environment_id=RuntimeEnvironments.PYTHON_312_MODERATIONS.value.id,
)

llm_custom_model = datarobot.CustomModel(
    **custom_model_args.model_dump(exclude_none=True),
    use_case_ids=[use_case.id],
    source_llm_blueprint_id=llm_blueprint.id,
)

registered_model_args = RegisteredModelArgs(
    resource_name="LLM Registered Model " + llm_datarobot_resource_name,
)

prediction_environment = datarobot.PredictionEnvironment(
    resource_name="LLM Prediction Environment " + llm_datarobot_resource_name,
    platform=dr.enums.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,
)

deployment_args = DeploymentArgs(
    resource_name="LLM Deployment Args " + llm_datarobot_resource_name,
    label=f"LLM Deployment [{PROJECT_NAME}] " + llm_datarobot_resource_name,
    association_id_settings=datarobot.DeploymentAssociationIdSettingsArgs(
        column_names=["association_id"],
        auto_generate_id=False,
        required_in_prediction_requests=True,
    ),
    predictions_data_collection_settings=datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
        enabled=True,
    ),
    predictions_settings=(
        datarobot.DeploymentPredictionsSettingsArgs(min_computes=0, max_computes=2)
    ),
)

llm_deployment = CustomModelDeployment(
    resource_name="LLM Deployment " + llm_datarobot_resource_name,
    use_case_ids=[use_case.id],
    custom_model_version_id=llm_custom_model.version_id,
    registered_model_args=registered_model_args,
    prediction_environment=prediction_environment,
    deployment_args=deployment_args,
)

app_runtime_parameters = [
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=llm_datarobot_application_name.upper() + "_DEPLOYMENT_ID",
        type="string",
        value=llm_deployment.id,
    ),
]

pulumi.export("Deployment ID " + llm_datarobot_resource_name, llm_deployment.id)
