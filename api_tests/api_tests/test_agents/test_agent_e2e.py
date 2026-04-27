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

import pytest

from api_tests.api_tests.test_agents.helpers import AgentE2EHelper


def test_local_environment_variables():
    # Ensure the required environment variables are set
    print("Checking environment variables (root .env file)")

    required_vars = [
        "DATAROBOT_API_TOKEN",
        "DATAROBOT_ENDPOINT",
    ]
    for var in required_vars:
        assert os.getenv(var), (
            f"Environment variable {var} is not set, please set it in the .env file"
        )


@pytest.mark.parametrize(
    "agent_name, agent_quickstart_index",
    [
        ("agent_crewai", 1),
        ("agent_generic_base", 2),
        ("agent_langgraph", 3),
        ("agent_llamaindex", 4),
    ],
)
def test_e2e_agents(
    agent_name,
    agent_quickstart_index,
    root_path,
    repo_path,
):
    if len(os.environ.get("DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT", "")) > 0:
        print(
            "⚠️ WARNING: DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT is set, "
            "this will use a pre-existing environment. ⚠️"
        )

    dest_path = os.path.join(root_path, f"{agent_name}_e2e_test_dir")
    agent_helper = AgentE2EHelper(
        agent_name=agent_name,
        agent_quickstart_index=agent_quickstart_index,
        repo_path=repo_path,
        dest_path=dest_path,
    )
    try:
        agent_helper.setup_environment()

        agent_helper.run_local_execution("Artificial Intelligence")

        agent_helper.pulumi_create_stack()

        custom_model_id = agent_helper.pulumi_build_agent()
        agent_helper.run_custom_model_execution(
            "Artificial Intelligence", custom_model_id
        )

        deployment_id = agent_helper.pulumi_deploy_agent()
        agent_helper.run_deployment_execution("Artificial Intelligence", deployment_id)

        print("Agent execution completed successfully")
    finally:
        agent_helper.cleanup_environment()
