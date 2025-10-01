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
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union

logger = logging.getLogger()

if sys.version_info[0] < 3 or (sys.version_info[0] >= 3 and sys.version_info[1] < 10):
    print("Must be using Python version 3.10 or higher")
    exit(1)

work_dir = Path(os.path.dirname(__file__))
dot_env_file = Path(work_dir / ".env")
venv_dir = work_dir / ".venv"


def check_dotenv_exists():
    if not dot_env_file.exists():
        print(
            "Could not find `.env`. Please rename the file `.env.sample` and fill in your details\n\n"
            "For more help please go to:\n"
            "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/getting-started.md"
        )
        exit(1)


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


def check_taskfile_installed():
    try:
        subprocess.check_call(
            ["task", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Could not find `task` (Taskfile / go-task) in your environment.\n\n"
            "For more help with pre-requisites please go to:\n"
            "  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
            "getting-started-prerequisites.md"
        )
        exit(1)


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
        try_to_remove(str(work_dir / ".github" / "workflows" / f"{agent_name}-test.yml"))
        try_to_remove(str(work_dir / ".datarobot" / "answers" / f"agent-{agent_name}.yml"))
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
    try_to_remove(str(work_dir / f"Taskfile_dev.yml"))

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
    check_dotenv_exists()

    check_uv_installed()
    check_taskfile_installed()
    check_pulumi_installed()
    print("All pre-requisites are installed.\n")

    agent_templates = [
        "agent_crewai",
        "agent_generic_base",
        "agent_langgraph",
        "agent_llamaindex",
    ]
    print("You will now select an agentic framework to use for this project.")
    print("For more information on the different agentic frameworks please go to:")
    print("  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/getting-started.md")
    print()
    print("Please select an agentic framework to use:")
    for i, template in enumerate(agent_templates, start=1):
        print(f"{i}. {template}")
    choice = input("Enter your choice (1-4): ")
    if choice not in ["1", "2", "3", "4"]:
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
        print("DataRobot agent templates provide you with several CLI tools to help you")
        print("manage your agent development and deployment.")
        print("For more information please go to:")
        print("  https://github.com/datarobot-community/datarobot-agent-templates/blob/main/docs/"
              "developing-agents-cli.md")
        print("\nYou can also run the following command for a list of actions:")
        print("> task")
        print()
        print("\nYou can refresh your environment at any time by running:")
        print("> task install")


if __name__ == "__main__":
    main()
