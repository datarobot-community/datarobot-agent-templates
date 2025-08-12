# # Copyright 2025 DataRobot, Inc.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# import os

# import datarobot as dr
# import pulumi
# import pulumi_datarobot
# from datarobot_pulumi_utils.pulumi.stack import PROJECT_NAME

# __all__ = [
#     "nim_llm_application_name",
#     "nim_llm_resource_name",
# ]

# nim_llm_application_name: str = "nim_llm"
# nim_llm_resource_name: str = "[nim_llm]"
# nim_llm_registered_model_id: str = "NIM_REGISTERED_MODEL_ID"
# nim_llm_deployment_id: str = "NIM_DEPLOYMENT_ID"

# # USING NIM_REGISTERED_MODEL_ID TO CREATE DEPLOYMENT
# nim_llm_prediction_environment = pulumi_datarobot.PredictionEnvironment(
#     resource_name="NIM Prediction Environment "
#     + nim_llm_resource_name,
#     platform=dr.enums.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,
# )

# nim_llm_deployment = pulumi_datarobot.Deployment(
#     resource_name="NIM Deployment " + nim_llm_resource_name,
#     label=f"NIM Deployment [{PROJECT_NAME}] "
#     + nim_llm_resource_name,
#     prediction_environment_id=nim_llm_prediction_environment.id,
#     registered_model_version_id=os.environ[nim_llm_registered_model_id],
#     predictions_data_collection_settings=pulumi_datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
#         enabled=True,
#     ),
#     predictions_settings=(
#         pulumi_datarobot.DeploymentPredictionsSettingsArgs(min_computes=0, max_computes=1)
#     ),
# )

# # RETRIEVING USING NIM_DEPLOYMENT_ID TO CREATE DEPLOYMENT
# # nim_llm_deployment = pulumi_datarobot.Deployment.get(
# #     id=os.environ.get(nim_llm_deployment_id),
# #     resource_name="NIM Deployment [PRE-EXISTING] " + nim_llm_resource_name,
# # )

# app_runtime_parameters = [
#     pulumi_datarobot.ApplicationSourceRuntimeParameterValueArgs(
#         key=nim_llm_deployment_id,
#         type="string",
#         value=nim_llm_deployment.id,
#     ),
# ]

# pulumi.export(
#     "Deployment ID " + nim_llm_resource_name,
#     nim_llm_deployment.id,
# )