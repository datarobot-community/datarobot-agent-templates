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
import shutil
import subprocess
import time
from typing import cast

import requests


class AgentE2EHelper:
    def __init__(
        self,
        agent_name=None,
        agent_quickstart_index=None,
        repo_path=None,
        dest_path=None,
    ):
        self.agent_name = agent_name
        self.agent_quickstart_index = agent_quickstart_index
        self.dest_path = dest_path
        self.repo_path = repo_path

    @staticmethod
    def run_process(command, directory, input=None, timeout=240, env=None):
        result = subprocess.check_output(
            command,
            env=env,
            encoding="utf-8",
            shell=True,
            input=input,
            timeout=timeout,
            cwd=directory,
        )
        return result

    def setup_environment(self):
        print("Setting up environment")
        shutil.rmtree(self.dest_path, ignore_errors=True)

        # Start by cloning the repo to a new directory (only working portions, no venvs, git, etc
        os.makedirs(self.dest_path, exist_ok=True)
        shutil.copytree(
            self.repo_path,
            self.dest_path,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.venv*", "api_tests", ".git"),
        )

        # Now run the quickstart script to set up the environment for the agent_generic_base
        print("Running quickstart")
        result = self.run_process(
            ["uv run quickstart.py"],
            self.dest_path,
            input=f"{self.agent_quickstart_index}\n",
        )
        result = cast(str, result)
        assert result.split("\n")[-2] == "task setup"

        # Setup the development environment for the agent
        print("Running task setup")
        result = self.run_process(
            ["task setup"],
            self.dest_path,
        )
        result = cast(str, result)
        assert result.split("\n")[:-1] == [
            "Updating agent environment",
            "Updating local dependencies",
            "Updating infra environment",
        ]

    def cleanup_environment(self):
        # Attempt to destroy the stack
        print("Cancelling any running Pulumi operations for agent")
        try:
            self.run_process(
                [f"pulumi cancel -s {self.agent_name} -y"],
                os.path.join(self.dest_path, "infra"),
            )
        except subprocess.CalledProcessError as e:
            print(f"Destroy could not complete: {e}")

        print("Destroying Pulumi stack for agent")
        try:
            self.run_process(
                [f"pulumi destroy -s {self.agent_name} -f -y"],
                os.path.join(self.dest_path, "infra"),
            )
        except subprocess.CalledProcessError as e:
            print(f"Destroy could not complete: {e}")

        print("Removing Pulumi stack for agent")
        try:
            self.run_process(
                [f"pulumi stack rm -s {self.agent_name} -f -y"],
                os.path.join(self.dest_path, "infra"),
            )
        except subprocess.CalledProcessError as e:
            print(f"Stack does not exist: {e}")

        # Cleanup the directory after the test
        print("Cleaning up environment")
        shutil.rmtree(self.dest_path, ignore_errors=True)

    def pulumi_create_stack(self):
        print("Creating Pulumi stack for agent")
        try:
            self.run_process(
                [f"pulumi stack rm -s {self.agent_name} -f -y"],
                os.path.join(self.dest_path, "infra"),
            )
        except subprocess.CalledProcessError as e:
            print(f"Stack does not exist: {e}")

        result = self.run_process(
            [f"pulumi stack init -s {self.agent_name}"],
            os.path.join(self.dest_path, "infra"),
        )
        print(result)
        assert "Created stack" in result

    def pulumi_build_agent(self):
        print("Running Pulumi up to build the agent")
        result = self.run_process(
            [f"export AGENT_DEPLOY=0 && pulumi up -y -s {self.agent_name}"],
            os.path.join(self.dest_path, "infra"),
            timeout=60
            * 15,  # 15 minute timeout for building the agent (environment can take a while)
        )
        print(result)
        custom_model_rows = [
            row
            for row in result.split("\n")
            if f"Custom Model ID [{self.agent_name}]" in row
        ]
        custom_model_id = custom_model_rows[-1].split('"')[-2]
        print(f"Custom model ID: {custom_model_id}")
        return custom_model_id

    def pulumi_deploy_agent(self):
        print("Running Pulumi up to deploy the agent")
        result = self.run_process(
            [f"export AGENT_DEPLOY=1 && pulumi up -y -s {self.agent_name}"],
            os.path.join(self.dest_path, "infra"),
            timeout=60
            * 6,  # 6 minute timeout for deploying the agent (environment should already be built)
        )
        print(result)
        deployment_rows = [
            row
            for row in result.split("\n")
            if f"Agent Deployment ID [{self.agent_name}]" in row
        ]
        deployment_id = deployment_rows[-1].split('"')[-2]
        print(f"Agent deployment ID: {deployment_id}")
        return deployment_id

    def run_local_execution(self, user_prompt: str):
        print("Running local agent execution")
        result = self.run_process(
            [f'task agent:cli -- execute --user_prompt "{user_prompt}"'],
            self.dest_path,
        )

        # Verify the OpenAI Response
        result = cast(str, result)
        local_result = json.loads(result.split("Stored Execution Result:")[-1])
        assert [
            key in local_result
            for key in [
                "id",
                "choices",
                "created",
                "model",
                "object",
                "usage",
                "pipeline_interactions",
            ]
        ]
        assert len(local_result["choices"]) == 1
        print("Valid agent response:")
        print(local_result)

    def run_custom_model_execution(self, user_prompt: str, custom_model_id: str):
        print("Running custom model agent execution")
        headers = {
            "Authorization": f"Bearer {os.environ['DATAROBOT_API_TOKEN']}",
            "Content-Type": "application/json",
        }
        data = {"messages": [{"role": "user", "content": user_prompt}]}

        print("POST to custom model agent endpoint")
        response = requests.post(
            f"{os.environ['DATAROBOT_ENDPOINT']}/genai/agents/fromCustomModel/{custom_model_id}/chat/",
            headers=headers,
            json=data,
        )
        # Something wrong
        if not response.ok or not response.headers.get("Location"):
            raise Exception(response.content)
        print("Agent execution started, waiting for completion...")
        # Wait for the agent to complete
        status_location = response.headers["Location"]
        while response.ok:
            time.sleep(1)
            response = requests.get(
                status_location, headers=headers, allow_redirects=False
            )
            if response.status_code == 303:
                print("Agent execution completed, fetching response...")
                agent_response = requests.get(
                    response.headers["Location"], headers=headers
                ).json()
                # Show the agent response
                break
            else:
                status_response = response.json()
                if status_response["status"] in ["ERROR", "ABORTED"]:
                    raise Exception(status_response)
        else:
            raise Exception(response.content)

        assert "choices" in agent_response, "No choices in agent response"
        print("Valid agent response:")
        print(agent_response)

    def run_deployment_execution(self, user_prompt: str, deployment_id: str):
        print("Running deployed agent execution")
        deployment_result = self.run_process(
            [
                f'task agent:cli -- execute-deployment --user_prompt "{user_prompt}" --deployment_id {deployment_id}'
            ],
            self.dest_path,
        )

        # Assert there is a chat completion in the response
        deployment_result = cast(str, deployment_result)

        outputs = deployment_result.split("\n")
        assert "Running CLI execute-deployment" in outputs[0]
        assert len(outputs[5].split(", ")) > 10
        assert outputs[5].split(", ")[1] == "choices=[Choice(finish_reason='stop'"
        assert outputs[5].split(", ")[2] == "index=0"

        print("Valid agent response:")
        print(deployment_result)
