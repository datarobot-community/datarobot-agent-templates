# [DataRobot AI agent templates](https://github.com/datarobot-community/datarobot-agent-templates)

This repository provides ready-to-use templates for building and deploying AI agents with multi-agent frameworks. These templates streamline the process of setting up your own agents with minimal configuration requirements. 

These templates support:

- Local development workflows
- Remote development (via GitHub Codespaces)
- Building and deploying agents within DataRobot

## Prerequisites

Before getting started, ensure you have the following tools installed on your system. You can use `brew` (on macOS) or your preferred package manager.
Please ensure your local tools are at or above the minimum versions required.

| Tool | Version | Description | Installation guide |
|------|---------|-------------|-------------------|
| **uv** | >= 0.6.10 | A Python package manager. | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) |
| **Pulumi** | >= 3.163.0 | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/) |
| **Taskfile** | >= 3.43.3 | A task runner. | [Taskfile installation guide](https://taskfile.dev/#/installation) |

## Available templates

This repository includes templates for four popular agent frameworks:

| Framework | Description | GitHub Repository |
|-----------|-------------|-------------------|
| **CrewAI** | A multi-agent framework with focus on role-based agents, | [GitHub](https://github.com/crewAIInc/crewAI) |
| **LangGraph** | Multi-agent orchestration with state graphs. | [GitHub](https://github.com/langchain-ai/langgraph) |
| **Llama-Index** | A framework for building RAG systems. | [GitHub](https://github.com/run-llama/llama_index) |
| **Generic Base** | A flexible template for any custom framework. | - |

## Getting started

> **NOTE:** Please ensure all prerequisites are installed before proceeding with the following workflow.

### Step 1: Clone the repository

```bash
git clone https://github.com/datarobot-community/datarobot-agent-templates.git
cd datarobot-agent-templates
```

Alternatively, you can download the repository as a ZIP file and extract it to your preferred location.

### Step 2: Configure environment variables

Create an `.env` file in the root directory to store your configuration:

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit the file with your preferred editor
nano .env  # or vim .env, code .env, etc.
```

Your `.env` file must contain, at minimum, the following variables, but it is recommended to set all variables for a 
complete setup:

```bash
# DataRobot API keys and endpoint
DATAROBOT_API_TOKEN=<Your API Token>
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2
```

### Step 3: Choose an agent framework

This repository includes four templates to get started. They are selected during the quickstart process.

| Directory | Framework | Description |
|-----------|-----------|-------------|
| `agent_crewai` | CrewAI | Role-based multi-agent collaboration framework |
| `agent_langgraph` | LangGraph | State-based orchestration framework |
| `agent_llamaindex` | Llama-Index | RAG-focused framework |
| `agent_generic_base` | Generic | Base template for any framework |

### Step 4: Use quickstart

The templates provide a `quickstart.py` and a `task start` command to help you quickly setup the environment and
remove all unnecessary files. You can run the quickstart script to initialize the agent.

```bash
python quickstart.py
# python3 quickstart.py  # If python points to Python 2.x
# uv run quickstart.py  # If using uv
```

Alternatively, use the Taskfile command.

```bash
task start
```

Answer the prompts to select your agent framework and configure the initial setup. This will remove any
unused files from the repository and prepare help you prepare your environments for agent development and testing.

## Develop the agent


Developing an agent is straightforward and a variety of tools and commands are provided to help you. [See the documentation for your chosen framework](./agent_generic_base/README.md) for development-specific guidelines.

After setting up your agent you can test it locally using the `CLI`, for example:
```bash
task agent:cli -- execute --user_prompt 'Tell me about Generative AI'
```

When you ready, you can start experimenting with your agent in DataRobot:
```bash
task build
```

Pulumi will show a list of resources its going to create, and if you are ready select yes to continue.

It will take some time to create an execution environment (~5 minutes). After that, pulumi will report you 
a custom model id, and a chat interface endpoint for it:
```
Agent Chat Completion Endpoint [agent_generic_base]: "https://staging.datarobot.com/api/v2/genai/agents/fromCustomModel/683ed1fcd767c535b580bc9d/chat/"
```

When you done experimenting, you can deploy your agent:
```bash
task deploy
```

You can test the deployed agent using the CLI as well, or using your own commands for example:
```bash
task agent:cli -- execute-deployment --deployment_id %your_id% --user_prompt 'Tell me about Generative AI'
```

This is only a small subset of the available commands to get you started. It is recommended that you read
the [Agent Development Documentation](./agent_generic_base/README.md) to get a full understanding of the available
commands and the process of developing your agent.

## Adding python packages to Agent or Execution Environments

You can add additional Python packages to any agent execution environment, however a few steps are required to ensure
that all the environments are properly synchronized. There are two different methods for adding packages. **If you
want to be able to run the agent anywhere, it is recommended that you create an updated Execution Environment**

### Execution Environment Requirements
This approach will allow you to add packages to your agent and use all the development pipelines fully. It is 
slightly more complex than the second method but is generally the recommended approach for most use cases.

1. In your `.env` file ensure that `DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT` is unset, or you can delete it completely.
2. Navigate to your agent and use uv to add the new package to the agent project environment:
```bash
  cd agent_generic_base  # or your chosen agent directory
  uv add <package_name>
```
3. Navigate to the `docker_context` directory in your agent and open the `requirements.in` file:
```bash
 # The full path is `agent_generic_base/docker_context`, `agent_crewai/docker_context`, etc.
 cd docker_context  # or your chosen agent directory
 open requirements.in  # or use your preferred editor (code, nano, vim, etc.)
```
4. Add your new package to the `requirements.in` file. For example, if you added `requests` in step 2:
```plaintext
requests  # You can optionally specify a minimum version here, e.g., requests>=2.25.1
```
5. Save the `requirements.in` file and run the following command to update the `requirements.txt`:
```bash
  uv pip compile --no-annotate --no-emit-index-url --output-file=requirements.txt requirements.in
````

You can manually test building your agent image by running the following, this will help you ensure the new dependency can be added:
```bash
  docker build -f Dockerfile . -t docker_context_test
```

After completing these steps, when you run `task build` or `task deploy`, the new environment will be automatically
built the first time. Subsequent builds will use the cached environment if the requirements have not changed. The new
environment will be automatically linked and used for all your agent components, models, and deployments.

> **Note:** It is recommended that you do not remove any packages from the `pyproject.toml` or `requirements.in` files
> unless you are absolutely sure they are no longer needed. Removing packages may lead to unexpected behavior with
> playground or deployment interactions, even if the local execution environment works correctly.

### Custom Model Requirements
The second and simplest way is to add your package to the `custom_model/requirements.txt` file. This will allow you to
locally test the agent with the new package. This will also carry through to deployments of the agent.
> **Note:** Using this method may not work properly with all integrated application templates and interacting
> with a **Custom Model** through the **GenAI Playground** is not supported in this flow. These requirements are
> only supported by fully deployed models.


## Using a DataRobot Deployment as an LLM
_This method can also be used to dynamically pass any variable between pulumi deployments. The dependencies will
automatically be deployed in the appropriate order without any user input._

The template provides two possible methods for developing agents. The default method uses the DataRobot LLM Gateway
as te LLM for your agent. This allows you to use any model available in DataRobot as the LLM for your agent.
Alternatively, you may want to use a custom model to host a Generative AI Playground model. This is a 
supported scenario and you need to make a few edits to some files to enable it.

A sample Playground Model is provided in the `infra/infra/llm_datarobot.py` pulumi file. You can enable this 
to be deployed by default by changing the `.env` file to set `USE_DATAROBOT_LLM_GATEWAY=false`.

1. Edit your `.env` file:
   ```bash
   USE_DATAROBOT_LLM_GATEWAY=false
   ```
2. Open the `infra` file for you agent (e.g. `infra/infra/agent_generic_base.py`)
3. Uncomment the import for the `llm_datarobot` module:
   ```python
   from .llm_datarobot import app_runtime_parameters as llm_datarobot_app_runtime_parameters
   ```
4. Uncomment the `runtime_parameter_values` for the `pulumi_datarobot.CustomModel`, by default these are set to `[]`:
   ```python
    # runtime_parameter_values=[],
    # To use the LLM DataRobot Deployment in your Agent, uncomment the line below
    runtime_parameter_values=llm_datarobot_app_runtime_parameters,
    ```
5. In the `custom_model/model-metadata.yaml` file, ensure that the `ENABLE_LLM_GATEWAY_INFERENCE` has
the default value set to `false`.
6. In the `custom_model/custom.py` folder uncomment the `drum import`:
   ```python
   from datarobot_drum import RuntimeParameters
   ```
7. In the `def chat` function you can now see the imported environment variable that you can use:
    ```python
    llm_datarobot_deployment_id_from_runtime = RuntimeParameters.get(
        "LLM_DATAROBOT_DEPLOYMENT_ID"
    )
    ```

There are a few import things to consider to allow pulumi to dynamically define IDs across different agents and models.

> - The `LLM_DATAROBOT_DEPLOYMENT_ID` environment variable name is set in the `app_runtime_parameters` at the bottom
> of the `llm_datarobot.py` file.
> - If you want to use a different ID you must define this in your `custom_model/model-metadata.yaml`
> - This variable will be dynamically populated in the `RuntimeParameters` class when the agent is deployed, 
> which will overwrite the default value set in the `model-metadata.yaml` file.

## Get help

If you encounter issues or have questions, use one of the following options:

- Check the documentation for your chosen framework.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html?redirect_source=community.datarobot.com) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-templates).
