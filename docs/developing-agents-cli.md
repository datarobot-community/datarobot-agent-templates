### DataRobot Agent Templates Navigation
- [Home](/README.md)
- [Prerequisites](/docs/getting-started-prerequisites.md)
- [Getting started](/docs/getting-started.md)
- [Updating Agentic Templates](/docs/getting-started-updating.md)
- Developing Agents
  - [Developing your agent](/docs/developing-agents.md)
  - [Using the agent CLI](/docs/developing-agents-cli.md)
  - [Adding python requirements](/docs/developing-agents-python-requirements.md)
  - [Configuring LLM providers](/docs/developing-agents-llm-providers.md)
  - [Adding tools to your agent](/docs/developing-agents-tools.md)
---

# Developing Agents - CLI Guide

## Taskfile CLI commands

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

## Using pulumi terraform to manage your agent infrastructure
The repository uses Pulumi to manage infrastructure as code. The following commands are available to manage your
infrastructure through `task` commands.

```bash
# Update the custom model in DataRobot with your latest code changes
task build
```

```bash
# Deploy your agent with your latest code changes (this includes all build steps)
task deploy
```

```bash
# Teardown all the deployed infrastructure related to your agent
task destroy
```

```bash
# Refresh the Pulumi state file if it is out of sync with the deployed infrastructure
task refresh
```


## Using the agent CLI

The `agent:cli` command provides a convenient interface for testing your agent. This allows you to quickly execute
the entire LLM agent workflow from the command line without having to write any additional code. You should run this
command from the root directory.

```bash
# Root directory
task agent:cli
```

This displays CLI usage information.

```
❯ task cli
Running CLI
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  A CLI for interacting executing agent custom models using the chat endpoint
  and OpenAI completions.

  For more information on the main CLI commands and all available options, run
  the help command: > task agent:cli -- execute --help > task agent:cli -- execute-
  deployment --help

  Common examples:
  ...

Options:
  --api_token TEXT  API token for authentication.
  --base_url TEXT   Base URL for the API.
  --help            Show this message and exit.

Commands:
  execute             Execute agent code using OpenAI completions.
  execute-deployment  Query a deployed model using the command line.
```

### Using the CLI to test your local agent
The following are common examples of how to use the CLI to test your agent on your local environment.

```bash
# Run the agent with a string sent as the user prompt
> task agent:cli -- execute --user_prompt "Artificial Intelligence"
```

```bash
# Run the agent with a JSON sent as the user prompt
> task agent:cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'
```

```bash
# Run the agent with a JSON file containing the full chat completion json
> task agent:cli -- execute --completion_json example-completion.json
```

If you are using the `completion_json` option, the JSON file should contain a full chat completion request.
An example json is provided in the `example-completion.json` file. An example of the JSON structure is shown below.
You can pass additional parameters as needed using the `extra_body` field.

```json
{
  "model": "datarobot-deployed-llm",
  "messages": [
    {
      "content": "You are a helpful assistant",
      "role": "system"
    },
    {
      "content": "Artificial Intelligence",
      "role": "user"
    }
  ],
  "n": 1,
  "temperature": 0.01,
  "extra_body": {
    "api_key": "DATAROBOT_API_KEY",
    "api_base": "https://app.datarobot.com",
    "verbose": true
  }
}
```

### Using the CLI to test your deployed agent
Once you have deployed your agent to DataRobot, you can use the CLI to test your deployed agent. You will need the
deployment ID which is shown after the deployment process is complete. You can find the deployment ID in the terminal.
You can also find the deployment ID in the DataRobot UI under the "Deployments" section under "Console". 

If you have not already done so, you will need to deploy your agent using the `task deploy` command.

```bash
# Run the deployed agent with a string sent as the user prompt
> task agent:cli -- execute-deployment --user_prompt "Artificial Intelligence" --deployment_id 680a77a9a3
```

```bash
# Run the deployed agent with a JSON sent as the user prompt
> task agent:cli -- execute-deployment --user_prompt '{"topic": "Artificial Intelligence"}' --deployment_id 680a77a9a3
``` 

```bash
# Run the deployed agent with a JSON file containing the full chat completion json
> task agent:cli -- execute-deployment --completion_json example-completion.json --deployment_id 680a77a9a3
```

If you are using the `completion_json` option, the JSON file should contain a full chat completion request, the same
as when testing locally. An example json is provided in the `example-completion.json` file.


## Using the CLI to test your agent with the DataRobot Playground
You can also test your agent using the DataRobot LLM Playground. This allows you to interactively examine queries and
traces sent to your agent. To use the playground, you will need to deploy your agent using the `task build` command.
Because the playground is a text based interface, your agent will only respond to text-based prompts in this
environment.

After running the `task build` command, your custom model will be available to use in the DataRobot LLM Playground,
and you can find the model ID in the terminal output.

```bash
# Run the agent with a string sent as the user prompt
> task agent:cli -- execute --user_prompt "Artificial Intelligence" --model_id <model_id>
```
