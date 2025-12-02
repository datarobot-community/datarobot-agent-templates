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
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info[0] < 3 or (sys.version_info[0] >= 3 and sys.version_info[1] < 10):
    print("Must be using Python version 3.10 or higher")
    exit(1)

work_dir = Path(os.path.dirname(__file__))
dot_env_file = Path(work_dir / ".env")
venv_dir = work_dir / ".venv"


def check_dotenv_exists():
    if not dot_env_file.exists():
        print(
            "Could not find `.env`. Please rename the file `.env.sample` and fill in your details"
        )
        exit(1)


def check_pulumi_installed():
    try:
        subprocess.check_call(
            ["pulumi"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        print(
            "Is pulumi installed? If not, please go to `https://www.pulumi.com/docs/iac/download-install/`"
        )
        exit(1)


def check_taskfile_installed():
    try:
        subprocess.check_call(
            ["task", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        print(
            "Is Taskfile installed? If not, please go to `https://taskfile.dev/installation/`"
        )
        exit(1)


def check_uv_installed():
    try:
        subprocess.check_call(
            ["uv", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        print(
            "Is UV installed? If not, please go to `https://docs.astral.sh/uv/getting-started/installation/`"
        )
        exit(1)


def remove_agent_environment(agent_name: str):
    """Remove the agent environment if it exists."""
    agent_env_path = work_dir / f"{agent_name}"
    if agent_env_path.exists():
        print(f"Removing existing agent environment: {agent_env_path}")
        shutil.rmtree(str(agent_env_path), ignore_errors=True)
        os.remove(str(work_dir / ".github" / "workflows" / f"{agent_name}-test.yml"))
        os.remove(str(work_dir / ".datarobot" / "answers" / f"agent-{agent_name}.yml"))
        os.remove(str(work_dir / "infra" / "infra" / f"{agent_name}.py"))
        os.remove(str(work_dir / f"Taskfile_{agent_name}.yml"))
        print(f"Removed agent environment: {agent_env_path}")
    else:
        print(f"No existing agent environment found at: {agent_env_path}")


def remove_global_environment_files():
    """
    Removes global environment files such as the .git directory and quickstart.py,
    then initializes a new git repository in the work directory.
    """
    # Remove .git directory
    # try:
    #     shutil.rmtree(str(work_dir / ".git"))
    #     print("Removed existing .git directory")
    # except Exception as e:
    #     print(f"Warning: Could not remove .git directory: {e}")

    # Remove quickstart.py file
    try:
        os.remove(str(work_dir / "quickstart.py"))
        print("Removed quickstart.py file")
    except FileNotFoundError:
        print("Warning: quickstart.py file not found, skipping removal")
    except PermissionError:
        print("Warning: Permission denied when trying to remove quickstart.py")
    except Exception as e:
        print(f"Warning: Could not remove quickstart.py: {e}")

    # Remove RELEASE.yaml file
    try:
        os.remove(str(work_dir / "RELEASE.yaml"))
        print("Removed RELEASE.yaml file")
    except FileNotFoundError:
        print("Warning: RELEASE.yaml file not found, skipping removal")
    except PermissionError:
        print("Warning: Permission denied when trying to remove RELEASE.yaml")
    except Exception as e:
        print(f"Warning: Could not remove RELEASE.yaml: {e}")

    # Initialize a new git repository
    # try:
    #     subprocess.run(["git", "init"], cwd=work_dir, check=True)
    #     print("Initialized new git repository")
    # except subprocess.CalledProcessError as e:
    #     print(f"Warning: Failed to initialize git repository: {e}")
    # except FileNotFoundError:
    #     print("Warning: Git is not installed or not found in PATH")
    # except Exception as e:
    #     print(f"Warning: Could not initialize git repository: {e}")


def create_new_taskfile(agent_name: str):
    """Create a new Taskfile for the selected agent."""
    taskfile_path = work_dir / "Taskfile.yml"
    taskfile_agent_path = work_dir / f"Taskfile_{agent_name}.yml"

    new_task_file = [
        "---\n",
        "# https://taskfile.dev\n",
        "version: '3'\n",
        "env:\n",
        "  ENV: testing\n",
        "dotenv: ['.env', '.env.{{.ENV}}']\n",
    ]
    with open(taskfile_agent_path, "r") as f:
        agent_task_file = f.readlines()

    includes_line = next(
        idx for idx, line in enumerate(agent_task_file) if "includes:" in line
    )
    with open(taskfile_path, "w") as f:
        f.writelines(new_task_file + agent_task_file[includes_line:])

    os.remove(work_dir / f"Taskfile_{agent_name}.yml")
    os.remove(work_dir / f"Taskfile_development.yml")


def main():
    print("Checking environment setup...")
    check_dotenv_exists()

    check_uv_installed()
    check_taskfile_installed()
    check_pulumi_installed()
    print("All pre-requisites are installed.")

    agent_templates = [
        "agent_crewai",
        "agent_generic_base",
        "agent_langgraph",
        "agent_llamaindex",
    ]
    print("Please select an agent environment to set up:")
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
        agent_templates_to_remove = [
            agent for agent in agent_templates if agent != template_name
        ]
        for agent in agent_templates_to_remove:
            remove_agent_environment(agent)
        create_new_taskfile(template_name)
        remove_global_environment_files()

        print("\nPlease run the following command for a list of actions:")
        print("task")

        print("\nPlease run the following command to set up the agent environment:")
        print("task setup")


if __name__ == "__main__":
    main()
