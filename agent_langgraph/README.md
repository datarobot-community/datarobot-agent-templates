# DataRobot Agent Templates: Agent agent_langgraph

The agent template provides a set of utilities for constructing a single or multi-agent flow using platforms such
as CrewAI, LangGraph, LlamaIndex, and others. The template is designed to be flexible and extensible, allowing you
to create a wide range of agent-based applications.

## Tech Stack

- uv
- pulumi


## Development
The agent is developed by modifying the `custom_model` code. There are several things to consider:
- The agent itself lives within the `my_agent_class` sub-package. If renamed, please adjust the imports in `custom.py`.
- `custom.py` provides the entry point for the agent. It typically does not need modifications, but can be adjusted if the inputs need to be changed.
- Additional packages if needed can be added to `docker_context/requirements-agent.txt`.


## Agent CLI
The agent CLI is a command line interface that allows you to interact with and execute the agent in a local or remote
execution environment. The primary use case is for simple and rapid local execution.

The CLI can be interacted with via `Taskfile` using the `task cli` command.

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

Environment variables are used to set the `codespace_id`, `api_token`, and `base_url` for the CLI. These can be set in the
`.env` file or passed as command line arguments.
```
DATAROBOT_API_TOKEN=<API_TOKEN>
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2
DATAROBOT_CODESPACE_ID=<CODESPACE_ID>  # If using remote codespace execution from a local environment ONLY
```