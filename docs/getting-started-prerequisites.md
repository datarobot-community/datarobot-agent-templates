### DataRobot Agent Templates Navigation

- [Home](/README.md)
- [Installing prerequisites](/docs/getting-started-prerequisites.md)
- [Getting started](/docs/getting-started.md)
- [Updating Agentic Templates](/docs/getting-started-updating.md)
- Developing Agents
  - [Developing your agent](/docs/developing-agents.md)
  - [Using the agent CLI](/docs/developing-agents-cli.md)
  - [Adding python requirements](/docs/developing-agents-python-requirements.md)
  - [Configuring LLM providers](/docs/developing-agents-llm-providers.md)
  - [Adding tools to your agent](/docs/developing-agents-tools.md)

---

# Installing prerequisites

```diff
-IMPORTANT: This repository is only compatible with macOS and Linux operating systems.
```

If you are using Windows, consider using a [DataRobot Codespace](https://docs.datarobot.com/en/docs/workbench/wb-notebook/codespaces/index.html), Windows Subsystem for Linux (WSL), or a virtual machine running a supported OS.

Ensure you have the following tools installed and on your system at the required version (or newer).
It is **recommended to install the tools system-wide** rather than in a virtual environment to ensure they are available in your terminal session.
Refer to the [Installation instructions](#installation-instructions) section for more details.

## Prerequisite tools

[More information and diagrams about these tools are available here.](/docs/uv-task-pulumi.md)

| Tool         | Version    | Description                     | Installation guide                                                                      |
|--------------|------------|---------------------------------|-----------------------------------------------------------------------------------------|
| **git**      | >= 2.30.0  | A version control system.       | [git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |
| **uv**       | >= 0.6.10  | A Python package manager.       | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)        |
| **Pulumi**   | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/)          |
| **Taskfile** | >= 3.43.3  | A task runner.                  | [Taskfile installation guide](https://taskfile.dev/docs/installation)                   |

> **IMPORTANT:** You will also need a compatible C++ compiler and build tools installed on your system to compile some Python packages.
> As these will vary based on your OS, see the installation instructions below for specific details.

## Installation instructions

The following sections provide common installation instructions for each tool on both macOS and Linux.

- [macOS](#macos)
- [Linux](#linux)

> **IMPORTANT**: Installation instructions may change over time. If you encounter any issues, please [refer to the official documentation links](#prerequisite-tools) and websites above for the most current installation instructions.

### macOS

The easiest way to install the required tools on macOS is using [Homebrew](https://brew.sh/).
If it is not already installed, run the following command to install it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Once it is finished, you can install and/or update the required tools using the following commands:

- [**Xcode Command Line Tools**](https://developer.apple.com/documentation/xcode/):

  ```bash
  xcode-select --install
  ```

- [**Git**](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if not already installed by Xcode:

  ```bash
  brew install git
  ```

- [**uv**](https://docs.astral.sh/uv/getting-started/installation/):
  ```bash
  brew install uv
  ```

- [**Pulumi**](https://www.pulumi.com/docs/iac/download-install/):
  ```bash
  brew install pulumi
  ```

- [**Taskfile**](https://taskfile.dev/docs/installation):
  
  ```bash
  brew install go-task/tap/go-task
  ```
  
### Linux

The easiest way to install the required tools on Linux is using `curl` to download and run the installation scripts.

- **Build tools** can be installed using the OS package manager:
  - On Ubuntu/Debian:

    ```bash
    sudo apt-get update
    sudo apt-get install build-essential
    ```
  
  - On Fedora:
  
    ```bash
    sudo dnf groupinstall "Development Tools"
    ```

  - On CentOS/RHEL:
  
    ```bash
    sudo yum groupinstall "Development Tools"
    ```

- [**Git**](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) can be installed using your package manager.
  - On Ubuntu/Debian:
  
    ```bash
    sudo apt-get update
    sudo apt-get install git
    ```

  - On Fedora:
  
    ```bash
    sudo dnf install git
    ```

  - On CentOS/RHEL:
  
    ```bash
    sudo yum install git
    ```

- [**uv**](https://docs.astral.sh/uv/getting-started/installation/)

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [**Pulumi**](https://www.pulumi.com/docs/iac/download-install/)

  ```bash
  curl -fsSL https://get.pulumi.com/ | sh
  ```

- [**Taskfile**](https://taskfile.dev/docs/installation)

  ```bash
  curl -sL https://taskfile.dev/install.sh | sh
  ```

> **NOTE:** You may need to restart your terminal or run `source ~/.bashrc` (or `source ~/.zshrc` or equivalent)
> after installation to ensure the tools are available in your terminal session.

# Next steps

From here, proceed to [Getting started](/docs/getting-started.md).
