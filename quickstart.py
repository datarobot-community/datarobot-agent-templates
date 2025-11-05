#!/usr/bin/env python
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
import logging
import os
import dotenv
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union
from urllib.parse import urlparse

logger = logging.getLogger()


if sys.version_info[0] < 3 or (sys.version_info[0] >= 3 and sys.version_info[1] < 10):
    print("Must be using Python version 3.10 or higher")
    exit(1)

work_dir = Path(os.path.dirname(__file__))
dot_env_file = Path(work_dir / ".env")
venv_dir = work_dir / ".venv"


class DotEnvBuilder:
    """This class will be replaced by a CLI in the future."""

    ENV_VARIABLES_INFO = {
        "DATAROBOT_API_TOKEN": "Your DataRobot API token.",
        "DATAROBOT_ENDPOINT": "The URL of your DataRobot instance API.",
        "PULUMI_STACK_NAME": "The Pulumi stack name to use for this project.",
        "PULUMI_CONFIG_PASSPHRASE": "If empty, a blank passphrase will be used",
        "DATAROBOT_DEFAULT_USE_CASE": "If empty, a new use case will be created",
        "DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT": "If empty, a new execution environment will be created for each agent using the docker_context folder",
        "USE_DATAROBOT_LLM_GATEWAY": "Whether to use the DataRobot LLM Gateway (true/false)",
        "LLM_DEPLOYMENT_ID": "Your DataRobot LLM Deployment ID (required if not using the LLM Gateway)",
    }

    @classmethod
    def check_dotenv_exists(cls):
        if not dot_env_file.exists():
            print("""
A pre-existing `.env` file was not found.

This interactive script will help you set up your environment. Alternatively, you can manually
create a `.env` file by copying the `.env.example` file and filling in the required values.
            """)

            env_variables = cls.build_dotenv()
            cls.write_dotenv(env_variables)
            print(".env file created successfully.")
            dotenv.load_dotenv(dotenv_path=dot_env_file)

    @classmethod
    def build_dotenv(cls):
        env_variables: dict[str, str | None] = {
            key: None for key in cls.ENV_VARIABLES_INFO.keys()
        }

        # Unprompted defaults
        env_variables["PULUMI_CONFIG_PASSPHRASE"] = "123"
        env_variables["DATAROBOT_DEFAULT_USE_CASE"] = ""
        env_variables["DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT"] = (
            '"[DataRobot] Python 3.11 GenAI Agents"'
        )

        # Prompt for API token
        print("""
> To connect to your DataRobot instance, please provide your API credentials.
> If you need help finding your API token, please go to:
>     https://docs.datarobot.com/en/docs/api/api-quickstart/index.html#configure-your-environment
        """)
        while not env_variables["DATAROBOT_API_TOKEN"]:
            value = input("Please enter your DataRobot API token: ").strip()
            if cls.validate_field("DATAROBOT_API_TOKEN", value):
                env_variables["DATAROBOT_API_TOKEN"] = value
            else:
                print("Invalid API token. Please try again.")

        # Prompt for API URL
        while not env_variables["DATAROBOT_ENDPOINT"]:
            value = input(
                "Please enter your DataRobot API URL [default: https://app.datarobot.com/api/v2]: "
            ).strip()
            if cls.validate_field("DATAROBOT_ENDPOINT", value) or value == "":
                if value == "":
                    value = "https://app.datarobot.com/api/v2"
                env_variables["DATAROBOT_ENDPOINT"] = value
            else:
                print("Invalid URL. Please try again.")

        # Prompt for the pulumi stack name
        print("""
> Agentic workflows and llm resources are deployed using Pulumi.
> A unique pulumi stack name is used to help you easily identify resources associated
> with this project in the DataRobot registry and deployments.
        """)
        while not env_variables["PULUMI_STACK_NAME"]:
            value = input(
                "Please enter your Pulumi stack name [default: dev]: "
            ).strip()
            if value == "":
                value = "dev"
            env_variables["PULUMI_STACK_NAME"] = value

        # Ask if a user wants to use the DataRobot LLM Gateway
        print("""
> DataRobot Agent Templates are designed to get you quickly started. If you have access
> to the DataRobot LLM Gateway, we recommend using it to simplify your setup.
> 
> If you wish to use a custom DataRobot LLM deployment or a NIM deployment, or if you
> do not have access to the LLM Gateway, you should select no.
        """)
        while env_variables["USE_DATAROBOT_LLM_GATEWAY"] is None:
            value = (
                input(
                    "Would you like to use the DataRobot LLM Gateway? (y/n) [default: y]: "
                )
                .strip()
                .lower()
            )
            if value in ["y", "yes", ""]:
                env_variables["USE_DATAROBOT_LLM_GATEWAY"] = "true"
            elif value in ["n", "no"]:
                env_variables["USE_DATAROBOT_LLM_GATEWAY"] = "false"

        if env_variables["USE_DATAROBOT_LLM_GATEWAY"] == "false":
            # Prompt for LLM deployment ID
            while not env_variables["LLM_DEPLOYMENT_ID"]:
                value = input(
                    "Please enter your DataRobot LLM Deployment ID (or press Ctrl+C to exit): "
                ).strip()
                if cls.validate_field("DATAROBOT_DEPLOYMENT_ID", value):
                    env_variables["LLM_DEPLOYMENT_ID"] = value
                else:
                    print("Invalid LLM Deployment ID. Please try again.")

        return env_variables

    @classmethod
    def write_dotenv(cls, env_variables: dict):
        """
        Write the collected environment variables to a .env file.
        """
        # Write to .env file
        with open(dot_env_file, "w", encoding="utf-8") as f:
            for key, value in env_variables.items():
                if value is None:
                    value = ""
                f.write(f"# {cls.ENV_VARIABLES_INFO[key]}\n")
                f.write(f"{key}={value}\n\n")

    @staticmethod
    def validate_field(field_name: str, value: str) -> bool:
        """
        Validate that the provided field is valid.
        """
        if field_name == "PULUMI_STACK_NAME":
            return bool(value and " " not in value)
        if field_name == "DATAROBOT_API_TOKEN":
            return len(value) == 92
        if field_name == "DATAROBOT_DEPLOYMENT_ID":
            return len(value) == 24
        if field_name == "DATAROBOT_ENDPOINT":
            try:
                parsed = urlparse(value)
                return bool(parsed.scheme and parsed.netloc)
            except Exception:
                return False
        return True  # No specific validation for other fields


class EnvValidator:
    @staticmethod
    def check_pulumi_installed():
        try:
            subprocess.check_call(
                ["pulumi"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Could not find `pulumi` in your environment.\n\n"
                "For more help with pre-requisites please go to:\n"
                "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
                "getting-started-prerequisites.md"
            )
            exit(1)

    @staticmethod
    def check_taskfile_installed():
        try:
            subprocess.check_call(
                ["task", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Could not find `task` (Taskfile / go-task) in your environment.\n\n"
                "For more help with pre-requisites please go to:\n"
                "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
                "getting-started-prerequisites.md"
            )
            exit(1)

    @staticmethod
    def check_uv_installed():
        try:
            subprocess.check_call(
                ["uv", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Could not find `uv` in your environment.\n\n"
                "For more help with pre-requisites please go to:\n"
                "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
                "getting-started-prerequisites.md"
            )
            exit(1)


def try_to_remove(path: Union[str, Path]):
    """Attempt to remove a file or directory, ignoring errors."""
    try:
        if os.path.isdir(str(path)):
            shutil.rmtree(str(path), ignore_errors=True)
        else:
            os.remove(str(path))
    except Exception as e:
        logger.info(f"Warning: Could not remove {path}: {e}")


def remove_agent_environment(agent_name: str):
    """Remove the agent environment if it exists."""
    agent_env_path = work_dir / f"{agent_name}"
    if agent_env_path.exists():
        logger.info(f"Removing existing agent environment: {agent_env_path}")
        try_to_remove(str(agent_env_path))
        try_to_remove(
            str(work_dir / ".github" / "workflows" / f"{agent_name}-test.yml")
        )
        try_to_remove(
            str(work_dir / ".datarobot" / "answers" / f"agent-{agent_name}.yml")
        )
        try_to_remove(str(work_dir / "infra" / "feature_flags" / f"{agent_name}.yaml"))
        try_to_remove(str(work_dir / "infra" / "infra" / f"{agent_name}.py"))
        try_to_remove(str(work_dir / f"Taskfile_{agent_name}.yml"))
        logger.info(f"Removed agent environment: {agent_env_path}")
    else:
        print(f"No existing agent environment found at: {agent_env_path}")


def remove_global_environment_files():
    """
    Removes global environment files such as the .git directory and quickstart.py,
    then initializes a new git repository in the work directory.
    """
    # Remove quickstart.py file
    try_to_remove(str(work_dir / "quickstart.py"))

    # Remove RELEASE.yaml file
    try_to_remove(str(work_dir / "RELEASE.yaml"))

    # Remove harness pipelines directory if it exists
    try_to_remove(str(work_dir / ".harness"))

    # Remove development Taskfile if it exists
    try_to_remove(str(work_dir / "Taskfile_dev.yml"))

    # Remove the infra Taskfile if it exists
    try_to_remove(str(work_dir / "infra" / "Taskfile.yaml"))
    try_to_remove(str(work_dir / "infra" / "Taskfile.yml"))


def create_new_taskfile(agent_name: str):
    """Create a new Taskfile for the selected agent."""
    taskfile_path = work_dir / "Taskfile.yml"
    new_task_file = f"""---
# https://taskfile.dev
version: '3'
env:
  ENV: testing
dotenv: ['.env', '.env.{{.ENV}}']
includes:
  # Source the agent Taskfile
  agent:
    taskfile: ./{agent_name}/Taskfile.yml
    dir: ./{agent_name}
  # Source the infra Taskfile as flat tasks and point at the infra directory
  infra:
    taskfile: ./{agent_name}/Taskfile_infra.yml
    dir: ./infra
tasks:
  default:
    desc: "ℹ️ Show all available tasks (run `task --list-all` to see hidden tasks)"
    cmds:
      - task --list --sort none
    silent: true
  install:
    desc: "🛠️ Install all dependencies for agent and infra"
    cmds:
      - task: agent:install
      - task: infra:install
    silent: true
  build:
    cmds:
      - task: infra:build
  deploy:
    cmds:
      - task: infra:deploy
  destroy:
    cmds:
      - task: infra:destroy
"""
    with open(taskfile_path, "w", encoding="utf-8") as f:
        f.writelines(new_task_file)


def main():
    print("*****           *          ****        *             *  ")
    print("*    *  ***   *****  ***   *   *  ***  ****   ***  *****")
    print("*    * *   *    *   *   *  ****  *   * *  *  *   *   *  ")
    print("*****   *** *   *    *** * *   *  ***  ****   ***    *  ")
    print()
    print("--------------------------------------------------------")
    print("           Quickstart for DataRobot AI Agents           ")
    print("--------------------------------------------------------")

    print("Checking environment setup for required pre-requisites...")
    DotEnvBuilder.check_dotenv_exists()

    EnvValidator.check_uv_installed()
    EnvValidator.check_taskfile_installed()
    EnvValidator.check_pulumi_installed()
    print("All pre-requisites are installed.\n")

    agent_templates = [
        "agent_crewai",
        "agent_generic_base",
        "agent_langgraph",
        "agent_llamaindex",
        "agent_nat",
    ]
    print("\nYou will now select an agentic framework to use for this project.")
    print("For more information on the different agentic frameworks please go to:")
    print(
        "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/getting-started.md"
    )
    print()
    print("Please select an agentic framework to use:")
    for i, template in enumerate(agent_templates, start=1):
        print(f"{i}. {template}")
    choice = input("Enter your choice (1-5): ")
    if choice not in ["1", "2", "3", "4", "5"]:
        print("Invalid choice. Exiting.")
        return
    else:
        template_name = agent_templates[int(choice) - 1]
        print(f"You selected: {template_name}")
        print("Setting up the agent environment...")
        print("Cleaning up other framework templates to streamline your workspace.")
        agent_templates_to_remove = [
            agent for agent in agent_templates if agent != template_name
        ]
        for agent in agent_templates_to_remove:
            remove_agent_environment(agent)
        create_new_taskfile(template_name)
        remove_global_environment_files()

        print(
            "\nWould you like to setup the uv python environments and install pre-requisites now?"
        )
        run_install = input("(y/n): ").strip().lower()
        if run_install == "y":
            print("Running installation...")
            try:
                subprocess.run(
                    ["task", "install"],
                    cwd=work_dir,
                    check=True,
                )
                print("Installation completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Installation failed: {e}")
                return

        print()
        print(
            "DataRobot agent templates provide you with several CLI tools to help you"
        )
        print("manage your agent development and deployment.")
        print("For more information please go to:")
        print(
            "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
            "developing-agents-cli.md"
        )
        print("\nYou can also run the following command for a list of actions:")
        print("> task")
        print()
        print("\nYou can refresh your environment at any time by running:")
        print("> task install")


if __name__ == "__main__":
    main()
