<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-templates">
    <img src="./.github/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">DataRobot Agentic Workflow Templates</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/index.html">Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-templates/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/datarobot-agent-templates?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-templates" alt="License">
  </a>
</p>

This repository provides ready-to-use templates for building and deploying agentic workflows with multi-agent frameworks.
Agentic templates streamline the process of setting up new workflows with minimal configuration requirements.
They support local development and testing, as well as deployment to production environments within DataRobot.

```diff
-IMPORTANT: This repository updates frequently. Make sure to update your
-local branch regularly to obtain the latest changes.
```

---

# Table of contents

- [Available templates](#available-templates)
- [Installation](#installation)
- [Create and deploy your agent](#create-and-deploy-your-agent)
- [Develop your agent](#develop-your-agent)
- [Get help](#get-help)

---

# Available templates

This repository includes templates for three popular agent frameworks and a generic base template that can be adapted to any framework of your choice.
Each template includes a simple example agentic workflow with 3 agents and 3 tasks.

| Framework        | Description                                                | GitHub Repo | Docs  |
|------------------|------------------------------------------------------------|-------------|-------|
| **CrewAI**       | A multi-agent framework with focus on role-based agents.   | [GitHub](https://github.com/crewAIInc/crewAI)       | [Docs](https://docs.crewai.com/)|
| **Generic Base** | A barebones template that can be adapted to any framework. | -           | -     |
| **LangGraph**    | Multi-agent orchestration with state graphs.               | [GitHub](https://github.com/langchain-ai/langgraph) | [Docs](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)|
| **Llama-Index**  | A framework for building RAG systems.                      | [GitHub](https://github.com/run-llama/llama_index) | [Docs](https://gpt-index.readthedocs.io/en/latest/)|
| **NVIDIA NeMo Agent Toolkit** | A framework for connecting enterprise agents to data sources and tools. | [GitHub](https://github.com/NVIDIA/NeMo-Agent-Toolkit) | [Docs](https://developer.nvidia.com/nemo-agent-toolkit)|

# Installation

```diff
-IMPORTANT: This repository is only compatible with macOS and Linux operating systems.
```

> If you are using Windows, consider using a [DataRobot codespace](https://docs.datarobot.com/en/docs/workbench/wb-notebook/codespaces/index.html), Windows Subsystem for Linux (WSL), or a virtual machine running a supported OS.

Ensure you have the following tools installed and on your system at the required version (or newer).
It is **recommended to install the tools system-wide** rather than in a virtual environment to ensure they are available in your terminal session.

## Prerequisite tools

The following tools are required to install and run the agent templates.
For detailed installation steps, see [Installation instructions](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-install.html#installation-instructions) in the DataRobot documentation.

| Tool         | Version    | Description                     | Installation guide            |
|--------------|------------|---------------------------------|-------------------------------|
| **git**      | >= 2.30.0  | A version control system.       | [git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) |
| **uv**       | >= 0.6.10  | A Python package manager.       | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)     |
| **Pulumi**   | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/)        |
| **Taskfile** | >= 3.43.3  | A task runner.                  | [Taskfile installation guide](https://taskfile.dev/docs/installation)                 |

> **IMPORTANT**: You will also need a compatible C++ compiler and build tools installed on your system to compile some Python packages.

# Create and deploy your agent

```diff
-IMPORTANT: Ensure all prerequisites are installed before proceeding.
```

This guide walks you through setting up an agentic workflow using one of several provided templates.
It returns a Markdown (`.md`) document about your specified topic based on the research of a series of agents.
The example workflow contains these 3 agents:

- **Researcher**: Gathers information on a given topic using web search.
- **Writer**: Creates a document based on the research.
- **Editor**: Reviews and edits the document for clarity and correctness.

## Clone the agent template repository

The method for cloning the repository is dependent on whether your DataRobot application instance&mdash;either Managed SaaS (cloud) or Self-Managed (on-premise).

### Cloud users

You can either clone the repository to your local machine using Git or [download it as a ZIP file](https://github.com/datarobot-community/datarobot-agent-templates/archive/refs/heads/main.zip).

```bash
git clone https://github.com/datarobot-community/datarobot-agent-templates.git
cd datarobot-agent-templates
```

### On-premise users

Clone the release branch for your installation using Git, replacing `[YOUR_DATA_ROBOT_VERSION]` with the version of DataRobot you are using:

```bash
git clone -b release/[YOUR_DATA_ROBOT_VERSION] https://github.com/datarobot-community/datarobot-agent-templates.git
cd datarobot-agent-templates
```

> **NOTE**: To customize or track your own workflows, you can 
> [fork this repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo), 
> [change the remote URL](https://docs.github.com/en/get-started/git-basics/managing-remote-repositories), or 
> [create a new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository).

## Locate your DataRobot API key and endpoint

The section after this requires you to add your DataRobot API key and endpoint to the environment variables file.
See the [DataRobot API keys and endpoints](https://docs.datarobot.com/en/docs/get-started/acct-mgmt/acct-settings/api-key-mgmt.html) documentation for specific steps on how to locate them.

## Configure environment variables

Create an `.env` file in the root directory before running any commands:

1. Copy the sample environment file.

  ```bash
  cp .env.template .env
  ```

2. Edit the file with your preferred text editor.

  ```bash
  nano .env  # or vim .env, code .env, etc.
  ```

3. Paste the DataRobot API key and endpoint that you copied in [Locate your DataRobot API key and endpoint](#locate-your-datarobot-api-key-and-endpoint) into your `.env` file. Leave other variables at their default values during setup.

```bash
# Your DataRobot API token.
# Refer to https://docs.datarobot.com/en/docs/api/api-quickstart/index.html#configure-your-environment for help.
DATAROBOT_API_TOKEN=<YOUR_API_KEY>

# The URL of your DataRobot instance API.
DATAROBOT_ENDPOINT=<YOUR_API_ENDPOINT>
```

## Start and choose an agent framework

Run the helper script to start development:

```bash
task start
```

> **NOTE**: If you encounter errors with `task start`, ensure you've completed all [prerequisite](#installation) steps.

Specify which of the four available templates you would like to use during the `task start` process:

| Directory            | Framework   | Description                                    |
|----------------------|-------------|------------------------------------------------|
| `agent_crewai`       | CrewAI      | Role-based multi-agent collaboration framework |
| `agent_generic_base` | Generic     | Base template for any framework                |
| `agent_langgraph`    | LangGraph   | State-based orchestration framework            |
| `agent_llamaindex`   | Llama-Index | RAG-focused framework                          |
| `agent_nat`          | NeMo Agent Toolkit | NVIDIA NeMo Agent Toolkit framework     |

<details>
<summary><b>Which template should I choose?</b></summary>

  While all templates can use DataRobot tools and the DataRobot LLM Gateway, the ideal scenario for each can vary.

  **CrewAI**: A simple way to think about the CrewAI template is that it focuses on 'Who'.
  It is best suited to solving problems that require roles and collaboration, and excels at quickly prototyping multi-agent teams of specialists to collaborate on creative or analytical tasks.

  **LangGraph**: The LangGraph template focuses on 'How', and is ideal for problems that can be solved with process and auditing.
  It excels at building reliable systems where you need granular control, and can build incredibly robust systems with error handling and human approval loops.
  LangGraph's process control makes it ideal for workflows that require human approval before calling DataRobot prediction tools, or for building robust error handling around Data Registry operations.

  **LlamaIndex**: LlamaIndex focuses on the 'What', and is best suited to solving problems that require data and expertise.
  It excels at building powerful RAG-based agents that are experts in a specific, document-heavy domain.
  It can be combined with DataRobot's Vector Database for semantic search, Aryn DocParse for document processing, and Search Data Registry for discovering relevant datasets.

  **Generic base**: The Generic base template is a clean slate for situations where you need a barebones foundation that you can fully customize.
  Select this template if you already have experience developing and modifying agentic workflows, or if you need to build a custom agentic workflow from scratch.
  Generic base provides maximum flexibility for integrating custom DataRobot [agentic tools](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools.html) or building workflows that don't fit standard patterns.

</details>

<!--
  **NeMo Agent Toolkit**: NeMo Agent Toolkit focuses on 'How well', and is ideal for problems that require optimization, observability, and performance monitoring.
  It excels at enhancing existing agent workflows with built-in profiling, observability integrations, and evaluation systems without requiring you to replatform.
  It can be combined with DataRobot tools and observability platforms like Phoenix, Weave, and Langfuse to provide end-to-end visibility into agent performance and costs.
-->

When prompted to setup the Python environment and install prerequisites, type `y` and press `Enter`.

After selection, setup will finish, leaving only files relevant to the template specified in your branch.
**To switch frameworks later, re-clone the repository and run the steps above again**.

> **NOTE**: Run `task` (with no parameters) from the root directory to see all available commands.
> Aside from `start`, none are necessary to complete installation.

## Test your agent for local development

Now your agent is ready to be tested locally using the CLI.
Local testing requires a DataRobot connection for LLM communication.
Ensure your `.env` file has the correct API token and endpoint, as detailed in [Configure environment variables](#configure-environment-variables).

Run the following command to test your agent:

```bash
# You can run task agent:dev in a separate window or use `START_DEV=1` to run the local agent inline
task agent:cli START_DEV=1 -- execute --user_prompt 'Tell me about Generative AI'
```

Depending on the framework you selected, the test output will vary.
An example of the output is shown below:

```bash
{
  "id": "5379a74f-045e-4720-9c1b-3feb560d77ee",
  "choices": "[Truncated for display]",
  "created": 1761327008,
  "model": "datarobot-deployed-llm",
  "object": "chat.completion",
  "service_tier": null,
  "system_fingerprint": null,
  "usage": {
    "completion_tokens": 0,
    "prompt_tokens": 0,
    "total_tokens": 0,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  },
  "pipeline_interactions": "[Truncated for display]",
  "datarobot_association_id": "3eb947b0-8a58-4088-a873-5a9f4aeeaeb4",
  "trace_id": "19e357620b00cee0130314cc58646ddf"
}
```

Continue to the next section to deploy and test in a production-like environment.

## Deploy your agent

Next, deploy your agent to DataRobot, which requires a Pulumi login.
If you do not have one, use `pulumi login --local` for local login or create a free account at [the Pulumi website](https://app.pulumi.com/signup).

```bash
task deploy
```

During the deploy process, you will be asked to provide a **Pulumi stack name** (e.g., `myagent`, `test`, etc.) to identify your DataRobot resources.
Once you have provided one, the deploy process provides a preview link.
Review the Pulumi preview and approve changes by typing `yes` or pressing `Enter`.

> **NOTE**: If prompted to perform an update, select `yes` and press `Enter`.

Deployment takes several minutes.
When complete, a resource summary with important IDs/URLs is displayed:

```bash
Outputs:
    AGENT_CREWAI_DEPLOYMENT_ID                                    : "1234567890abcdef"
    Agent Custom Model Chat Endpoint [agentic-test] [agent_crewai]: "https://[YOUR_DATAROBOT_ENDPOINT]/api/v2/genai/agents/fromCustomModel/1234567890abcdef/chat/"
    Agent Deployment Chat Endpoint [agentic-test] [agent_crewai]  : "https://[YOUR_DATAROBOT_ENDPOINT]/api/v2/deployments/1234567890abcdef/chat/completions"
    Agent Execution Environment ID [agentic-test] [agent_crewai]  : "68fbc0eab1af04e6982ff7b1"
    Agent Playground URL [agentic-test] [agent_crewai]            : "https://[YOUR_DATAROBOT_ENDPOINT]/usecases/68fbc0eafb98d9d6d59c65db/agentic-playgrounds/1234567890abcdef/comparison/chats"
    LLM_DEFAULT_MODEL                                             : "datarobot/azure/gpt-4o-mini"
    USE_DATAROBOT_LLM_GATEWAY                                     : "1"

Resources:
    + 10 created

Duration: 2m12s

```

### Find your deployment ID

The deployment ID is displayed in the terminal output after running `task deploy`.
In the example output at the end of the previous section, the deployment ID is `1234567890abcdef`.

For more details, see [Model information](https://docs.datarobot.com/en/docs/mlops/deployment/deploy-methods/add-deploy-info.html#model-information) in the DataRobot documentation.

## Test your deployed agent

Use the CLI to test your deployed agent.
In the following command, replace <YOUR_DEPLOYMENT_ID> with your actual deployment ID from the previous step:

```bash
task agent:cli -- execute-deployment --user_prompt 'Tell me about Generative AI' --deployment_id <YOUR_DEPLOYMENT_ID>
```

> **NOTE**: The command may take a few minutes to complete.

Once the repsonse has been processed, the response displays.
The output below is an example, but your actual response will vary.

```bash
Execution result preview:
{
  "id": "f47cb925-39e0-4507-a843-5aa8b9420b01",
  "choices": "[Truncated for display]",
  "created": 1762448266,
  "model": "datarobot-deployed-llm",
  "object": "chat.completion",
  "service_tier": null,
  "system_fingerprint": null,
  "usage": {
    "completion_tokens": 0,
    "prompt_tokens": 0,
    "total_tokens": 0,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  },
  "datarobot_association_id": "461e6489-505b-43f9-84c3-3832ef0e3a25",
  "pipeline_interactions": "[Truncated for display]"
}
```

## Develop your agent

Once setup is complete, you are ready customize your agent, allowing you to add your own logic and functionality to the agent.
See the following documentation for more details:

- [Customize your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-development.html)
- [Add tools to your agent](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-tools-integrate.html)
- [Configure LLM providers](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-llm-providers.html)
- [Use the agent CLI](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-cli-guide.html)
- [Add Python requirements](https://docs.datarobot.com/en/docs/agentic-ai/agentic-develop/agentic-python-packages.html)

# Get help

If you encounter issues or have questions, try the following:

- Check [the documentation](#available-templates) for your chosen framework.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-templates).
