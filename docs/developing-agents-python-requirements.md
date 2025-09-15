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

# Adding Python Packages to Your Agent Environment
To add additional Python packages to your agent environment, you will add them to the base docker execution
environment used by your agent. For local development purposes, you can also add packages to the local
uv environment used by your agent.

> **Note:** It is recommended that you do not remove any packages from the `pyproject.toml` or `requirements.in` files
> unless you are absolutely sure they are no longer needed. Removing packages may lead to unexpected behavior with
> playground or deployment interactions, even if the local execution environment works correctly.

## Updating the Local Development Environment
1. Navigate to your agent and use uv to add the new package to the agent project environment:
```bash
  cd agent_generic_base  # or your chosen agent directory
  uv add <package_name>
```

## Updating the Docker Execution Environment
1. In your `.env` file ensure that `DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT` is unset, or you can delete it completely.
2. Navigate to the `docker_context` directory in your agent and open the `requirements.in` file:
```bash
 # The full path is `agent_generic_base/docker_context`, `agent_crewai/docker_context`, etc.
 cd docker_context  # or your chosen agent directory
 open requirements.in  # or use your preferred editor (code, nano, vim, etc.)
```
3. Add your new package to the `requirements.in` file. For example, if you added `requests` in step 2:
```plaintext
requests  # You can optionally specify a minimum version here, e.g., requests>=2.25.1
```
4. Save the `requirements.in` file and run the following command to update the `requirements.txt`:
```bash
  uv pip compile --no-annotate --no-emit-index-url --output-file=requirements.txt requirements.in
````

You can manually test building your agent image by running the following, this will help you ensure the new dependency
has no conflicts with existing packages:
```bash
  docker build -f Dockerfile . -t docker_context_test
```

After completing these steps, when you run `task build` or `task deploy`, the new environment will be automatically
built the first time. Subsequent builds will use the cached environment if the requirements have not changed. The new
environment will be automatically linked and used for all your agent components, models, and deployments.
