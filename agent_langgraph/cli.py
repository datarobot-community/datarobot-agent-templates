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
from typing import Any

import click

from agent_cli.environment import Environment

pass_environment = click.make_pass_decorator(Environment)


@click.group()
@click.option("--api_token", default=None, help="API token for authentication.")
@click.option("--base_url", default=None, help="Base URL for the API.")
@click.pass_context
def cli(
    ctx: Any,
    api_token: str | None,
    base_url: str | None,
) -> None:
    """A CLI for interacting executing agent custom models using the chat endpoint and OpenAI completions.

    For more information on the main CLI commands and all available options, run the help command:
    > task cli -- execute --help
    > task cli -- execute-deployment --help

    Common examples:

    # Run the agent with a string user prompt
    > task cli -- execute --user_prompt "Artificial Intelligence"

    # Run the agent with a JSON user prompt
    > task cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'

    # Run the agent with a JSON file containing the full chat completion json
    > task cli -- execute --completion_json "example-completion.json"

    # Run the deployed agent with a string user prompt [Other prompt methods are also supported similar to execute]
    > task cli -- execute-deployment --user_prompt "Artificial Intelligence" --deployment_id 680a77a9a3

    """
    ctx.obj = Environment(api_token, base_url)


@cli.command()
@pass_environment
@click.option("--user_prompt", default="", help="Input to use for chat.")
@click.option("--completion_json", default="", help="Path to json to use for chat.")
def execute(environment: Any, user_prompt: str, completion_json: str) -> None:
    """Execute agent code locally using OpenAI completions.

    Examples:

    # Run the agent with a string user prompt
    > task cli -- execute --user_prompt "Artificial Intelligence"

    # Run the agent with a JSON user prompt
    > task cli -- execute --user_prompt '{"topic": "Artificial Intelligence"}'

    # Run the agent with a JSON file containing the full chat completion json
    > task cli -- execute --completion_json "example-completion.json"
    """
    if len(user_prompt) == 0 and len(completion_json) == 0:
        raise click.UsageError("User prompt message or completion json must provided.")

    click.echo("Running agent...")
    response = environment.interface.local(
        user_prompt=user_prompt,
        completion_json=completion_json,
    )
    click.echo("\nStored Execution Result:")
    click.echo(response)


@cli.command()
@pass_environment
@click.option("--user_prompt", default="", help="Input to use for predict.")
@click.option("--custom_model_id", default="", help="ID for the deployment.")
def execute_custom_model(
    environment: Any, user_prompt: str, custom_model_id: str
) -> None:
    """Query a custom model using the command line for OpenAI completions. Custom models will execute inside an
    ephemeral CodeSpace environment. This can also be done through the DataRobot Playground UI.

    Example:

    # Run the agent with a string user prompt
    > task cli -- execute-custom-model --user_prompt "Artificial Intelligence" --custom_model_id 680a77a9a3

    # Run the agent with a JSON user prompt
    > task cli -- execute-custom-model --user_prompt '{"topic": "Artificial Intelligence"}' --custom_model_id 680a77a9a3
    """
    if len(user_prompt) == 0:
        raise click.UsageError("User prompt message must be provided.")
    if len(custom_model_id) == 0:
        raise click.UsageError("Custom Model ID must be provided.")

    click.echo("Querying deployment...")
    response = environment.interface.custom_model(
        custom_model_id=custom_model_id,
        user_prompt=user_prompt,
    )
    click.echo(response)


@cli.command()
@pass_environment
@click.option("--user_prompt", default="", help="Input to use for predict.")
@click.option("--completion_json", default="", help="Path to json to use for chat.")
@click.option("--deployment_id", default="", help="ID for the deployment.")
def execute_deployment(
    environment: Any, user_prompt: str, completion_json: str, deployment_id: str
) -> None:
    """Query a deployed model using the command line for OpenAI completions.

    Example:

    # Run the agent with a string user prompt
    > task cli -- execute-deployment --user_prompt "Artificial Intelligence" --deployment_id 680a77a9a3

    # Run the agent with a JSON user prompt
    > task cli -- execute-deployment --user_prompt '{"topic": "Artificial Intelligence"}' --deployment_id 680a77a9a3

    # Run the agent with a JSON file containing the full chat completion json
    > task cli -- execute-deployment --completion_json "example-completion.json" --deployment_id 680a77a9a3
    """
    if len(user_prompt) == 0 and len(completion_json) == 0:
        raise click.UsageError("User prompt message or completion json must provided.")
    if len(deployment_id) == 0:
        raise click.UsageError("Deployment ID must be provided.")

    click.echo("Querying deployment...")
    response = environment.interface.deployment(
        deployment_id=deployment_id,
        user_prompt=user_prompt,
        completion_json=completion_json,
    )
    click.echo(response)


if __name__ == "__main__":
    cli()
