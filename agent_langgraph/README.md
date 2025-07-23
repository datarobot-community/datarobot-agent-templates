# DataRobot Agent Templates: Agent agent_langgraph

The DataRobot agent template provides a starting point for building custom agents that can be deployed in DataRobot.
This template can be modified to support various frameworks, including CrewAI, LangGraph, Llama-Index, or
a generic base framework that can be customized to use any other agentic framework.

This README provides an overview of how to set up, develop, test, and deploy an agent using this template.

## Prerequisites

Before getting started, ensure that you have the following tools installed on your system. You can use `brew` (on macOS) or your preferred package manager.

| Tool | Description | Installation guide |
|------|-------------|-------------------|
| **uv** | A Python package manager. | [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) |
| **Pulumi** | An Infrastructure as Code tool. | [Pulumi installation guide](https://www.pulumi.com/docs/iac/download-install/) |
| **Taskfile** | A task runner. | [Taskfile installation guide](https://taskfile.dev/#/installation) |

## Develop an agent

### Update dependencies

To update dependencies for an agent, run the following command in the agent directory.

```bash
task task agent_langgraph:agent:req
```

### Available task commands

The repository uses Taskfile to simplify common operations. View available commands in the root directory by running the following.

```bash
task
```

This will display a list of available commands (the prefix will change based on the agent framework you selected).

```
❯ task
task: Available tasks for this project:
* build:                     🔵 [agent_crewai] Run Pulumi up in [BUILD] mode
* default:                   🗒️ Show all available tasks
* deploy:                    🟢 [agent_crewai] Run Pulumi up in [DEPLOY] mode
* destroy:                   🔴 [agent_crewai] Run Pulumi destroy
* install:                   🏗️ Install and setup the agent and infra environments      (aliases: setup, req)
* refresh:                   ⚪️ [agent_crewai] Run Pulumi refresh
* agent:cli:                 🖥️ [agent_crewai] Run the CLI with provided arguments
* agent:dev:                 🔨 [agent_crewai] Run the development server
* agent:install:             🛠️ [agent_crewai] Update local dependencies      (aliases: agent:req)
* agent:lint:                🧹 [agent_crewai] Lint the codebase
* agent:lint-check:          🧹 [agent_crewai] Check whether the codebase is linted
* agent:test:                🧪 [agent_crewai] Run tests
* agent:test-coverage:       🧪 [agent_crewai] Run tests with coverage
* agent:update:              🛠️ [agent_crewai] Update local dependencies (refresh uv locks)
```

You can also run `task` commands from various directories. Please note that the task command may change
based on the agent framework you selected and the current directory you are in. You may also need to source the `.env`
file to ensure that environment variables are set correctly if you are running commands outside the agent directory.

### Use the agent CLI

The `cli` command provides a convenient interface for testing your agent.

```bash
# Root directory
task agent:cli

# Agent directory
task cli
```

This displays CLI usage information.

```
❯ task cli
Running CLI
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  A CLI for interacting executing agent custom models using the chat endpoint
  and OpenAI completions.

  For more information on the main CLI commands and all available options, run
  the help command: > task cli -- execute --help > task cli -- execute-
  deployment --help

  Common examples:

  # Run the agent with a string user prompt > task cli -- execute
  --user_prompt "Artificial Intelligence"

  # Run the agent with a JSON user prompt > task cli -- execute --user_prompt
  '{"topic": "Artificial Intelligence"}'

  # Run the agent with a JSON file containing the full chat completion json >
  task cli -- execute --completion_json "example-completion.json"

  # Run the deployed agent with a string user prompt [Other prompt methods are
  also supported similar to execute] > task cli -- execute-deployment
  --user_prompt "Artificial Intelligence" --deployment_id 680a77a9a3

Options:
  --api_token TEXT  API token for authentication.
  --base_url TEXT   Base URL for the API.
  --help            Show this message and exit.

Commands:
  execute             Execute agent code using OpenAI completions.
  execute-deployment  Query a deployed model using the command line.
```

### Modify the agent code

The main agent code is located in the `custom_model` directory:

| File | Purpose |
|------|---------|
| `agent.py` | The main agent implementation file. |
| `custom.py` | Handles execution of the agent in DataRobot. |
| `helpers.py` | Helper functions for the agent. |
| `tools_client.py` | Tool definitions for the agent. |

The main class you need to modify is in `agent.py`. See this class for details of the implementation
based on the framework for which you are developing.

> **Note:** If you rename the `MyAgent` class, you'll need to update the reference in `custom.py`.

## Test an agent

There are two primary methods for testing your agent, outlined below.

### Method 1: Use the CLI (Recommended)

Test your agent using the CLI interface with a sample prompt:

```bash
task cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'
```

The JSON object is passed directly to the agent's `run` method as the `inputs` parameter.

You can also test your agent by providing a full chat completion request as a JSON file. An
example json is provided in the `example-completion.json` file.

```bash
task cli -- execute --chat_completion "example-completion.json"
```

### Method 2: Use direct execution

For more advanced testing scenarios, you can use the `run_agent.py` script directly:

```bash
uv run run_agent.py --chat_completion '{"your": "parameters"}' --custom_model_dir "./custom_model"
```

### Method 3: Use DataRobot User Models (DRUM)

To test your agent using DataRobot's User Model (DRUM) framework, you can find more information about
running your agent in a self contained local in the repository and README documentation:
- [datarobot-user-models repository](https://github.com/datarobot/datarobot-user-models)
- [DRUM CLI documentation](https://docs.datarobot.com/en/docs/modeling/special-workflows/cml/cml-drum.html/).

## Build and deploy an agent

When you're ready to move your agent to DataRobot, you have two options depending on your needs.

### Step 1: Ensure that the environment variables are set

Make sure your `.env` file contains the required DataRobot credentials and configuration:

```bash
DATAROBOT_API_TOKEN=<Your API Token>
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2
PULUMI_CONFIG_PASSPHRASE=<Optional passphrase>
```

### Choose your deployment option

#### Option A: Build a custom model for testing and refinement

To create a custom model that can be refined using the DataRobot LLM Playground.

```bash
task build
```

This command runs the Pulumi infrastructure to create a custom model in DataRobot but does not create a full production deployment. This is significantly faster and is ideal for iterative development and testing.

#### Option B: Deploy to production

To create a full production-grade deployment:

```bash
task deploy
```

This command builds the custom model and creates a production deployment with the necessary infrastructure, which takes longer but provides a complete production environment.

### Step 3: Manual deployment (Alternative)

If needed, you can manually run the Pulumi commands.

```bash
# Load environment variables
set -o allexport && source .env

# For build mode only (custom model without deployment)
export AGENT_DEPLOY=0

# Or for full deployment mode (default)
# export AGENT_DEPLOY=1

# Navigate to the infrastructure directory
cd ./infra

# Run Pulumi deployment
pulumi up
```

The `AGENT_DEPLOY` environment variable controls whether Pulumi creates only the custom model (`DEPLOY=0`) or both the custom model and a production deployment (`DEPLOY=1`). If not set, Pulumi defaults to full deployment mode.

Pulumi will prompt you to confirm the resources to be created or updated.

### Use the CLI to execute the deployment

Test your deployed agent using the CLI interface with a sample prompt:

```bash
task cli -- execute-deployment --user_prompt '{"topic": "Artificial Intelligence"}' --deployment "<deployment_id>"
```

Similar to the `execute` command, you can also provide a full chat completion request as a JSON file for the
deployed agent:

```bash
task cli -- execute-deployment --chat_completion "example-completion.json" --deployment "<deployment_id>"
```

## Next steps

After deployment, your agent will be available in your DataRobot environment. You can:

1. Test your deployed agent using `task cli -- execute-deployment`.
2. Integrate your agent with other DataRobot services.
3. Monitor usage and performance in the DataRobot dashboard.
