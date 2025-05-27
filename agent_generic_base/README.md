# DataRobot Agent Templates: Agent agent_generic_base

The agent template provides a set of utilities for constructing a single or multi-agent flow using platforms such
as CrewAI, LangGraph, LlamaIndex, and others. The template is designed to be flexible and extensible, allowing you
to create a wide range of agent-based applications.

## Requirements
These requirements need to be installed before using the templates. You can install them with `brew` or the package
mangager of your choice.
- uv (https://docs.astral.sh/uv/getting-started/installation/)
- pulumi (https://www.pulumi.com/docs/iac/download-install/)
- taskfile (https://taskfile.dev/#/installation)

## Getting Started
### Environment files
It is recommended to use a `.env` file to store your environment variables. The `.env` file should be placed in the
root of the project directory. A sample `.env` file is provided as .env.sample. You can copy it to `.env` and modify it
to suit your needs. The `.env` file is used to store sensitive information such as API keys and secrets.

The default `.env` file should contain the following:
```bash
# DataRobot API keys and endpoint
DATAROBOT_API_TOKEN=<Your API Token>
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2

# Required, unless logged in to pulumi cloud.
PULUMI_CONFIG_PASSPHRASE=

# If empty, a new use case will be created
DATAROBOT_DEFAULT_USE_CASE=

# If empty, a new execution environment will be created
DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT=
```

### Agent CLI Commands
To start local development, you should first navigate to the directory of the agent you want to work on. For example,
if you want to work on the CrewAI agent, you would run:
```bash
   cd agent_crewai
```

A CLI interface is provided through Taskfile. The CLI is designed to be used for local development and testing of the
agent. It allows you to execute the agent code and interact with the agent in a local or remote environment. It can
also be used to help you clean up the agent code and correct formatting or setup the environment.

You can see the task commands available by running `task` or `task help` in the agent directory.

```bash
> task
Available task commands:
  To run commands, use the following format:
    task <command> [<args>]

Commands:
help                           - Show this help message
req                            - Update dependencies for the agent
cli                            - Run the CLI with the provided arguments or no arguments to see help.
lint                           - Lint the agent templates
test                           - Run unit tests for the agent
fix-licenses                   - Fix licenses for the agent files
```

To execute the agent via `Taskfile` there is a `task cli` command provided. This command accepts several options
for helping you test and debug agents. You can see the cli commands available by running `task cli` or
`task cli --help` in the agent directory.

```bash
> task cli
Running CLI
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  A CLI for interacting executing agent custom models using the chat endpoint
  and OpenAI completions.

  Examples:

  > task cli -- execute --help

  > task cli -- execute-deployment --help

  > task cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'

Options:
  --codespace_id TEXT  Codespace ID for the session.
  --api_token TEXT     API token for authentication.
  --base_url TEXT      Base URL for the API.
  --help               Show this message and exit.

Commands:
  execute             Execute agent code using OpenAI completions.
  execute-deployment  Query a deployed model using the command line for...
```

### Setup Agent Environment
You can get started with the agent by running the `task req` command. This will install all the dependencies for the agent
and set up local `uv` environment in the `.venv` directory. If you make changes to the agent code, you may need
to re-run this command to synchronize the dependencies.

### Developing Your Agent
The agent code is located in the `agent_*/custom_model` directory. The code is organized into several files and folders
to help you get started. The main file that is edited is the `agent.py` file. This file contains the main logic for the
agent.

By default and agent implements the following standard:
```python
class MyAgent:
    def __init__(
        self, api_key: str, api_base: str, verbose: Union[bool, str], **kwargs: Any
    ):
        self.api_key = api_key
        self.api_base = api_base
        if isinstance(verbose, str):
            self.verbose = verbose.lower() == "true"
        elif isinstance(verbose, bool):
            self.verbose = verbose

    def run(self, inputs: Dict[str, str]) -> Tuple[str, Dict[str, int]]:
        _ = inputs, self.api_key
        usage = {
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "total_tokens": 0,
        }
        return "success", usage
```

Individual framework examples may support returning a slightly different type from the `def run()` function,
but an agent must implement a compatible `__init__` and `run` function.

> **_NOTE:_** The `agent.py` file is called by `custom.py` to execute the agent inside DataRobot. In many cases,
> the users may not need to edit `custom.py` at all for it to be compatible with their agent. If you rename the
> class `MyAgent` to another name, you will need to update the `custom.py` file to use the new name.

### Testing Your Agent
The agent code can be tested using `pytest` or through the CLI. The CLI is the recommended way to test the agent
code for execution purposes and to understand how the agentic workflow will operate. An example of testing an agent
is to navigate to the agent directory and run the following command:
```bash
   task cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'
```

In this case the `user_prompt` is actually a JSON object that is passed to the agent. The agent will then select the inputs
from the JSON object and execute the agent code. Alternatively an agent can be made to accept a string as the input
if that is a preferable start to the workflow. If you wish to send more complex commands these can be done
using uv to directly interact with the agent execution code, although often the `task cli` flow is preferable and more
straightforward to use.
```bash
   uv run run_agent.py --chat_completion {"complete ChatCompletion": "Dictionary"} --custom_model_dir "./custom_model"
```

There are additional options available through the `uv run run_agent.py` command. You can explore this executor and
adjust it to suit your needs if so desired.

## Deploying Your Agent
The agent can be deployed using the `pulumi` framework. The `pulumi` framework is used to create and manage
all of the remote resources.

> **_NOTE:_** Before running pulumi please ensure that your `.env` file is populated with the correct API and
> endpoint values.

> **_NOTE:_** You can define a default `PULUMI_CONFIG_PASSPHRASE` in the `.env` file. This will be used to encrypt
> the pulumi stack. You can leave this blank if you do not want to use a passphrase, or do not need local encryption.

You can initiate a full pulumi run through a `task` command by running
```bash
   task deploy
```

You can also manually run pulumi by running the following command:
```bash
   set -o allexport && source .env
   cd ./infra
   pulumi up
```
