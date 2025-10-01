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
To add additional Python packages to your agent environment, you'll add them to your `pyproject.toml` file
using uv, a modern Python package and environment manager.

**We recommend keeping existing packages in `pyproject.toml` to ensure consistent behavior across playground 
and deployment environments.**

> **IMPORTANT:** During a `task deploy` or `task build`, the `pyproject.toml` file is automatically synchronized with 
> the agentic workflow code and the `docker_context` directory. You don't need to manually update
> the `pyproject.toml` file in these directories.

1. Navigate to your agent directory and use uv to add the new package:
    ```bash
      cd agent_generic_base  # or your chosen agent directory
      uv add <package_name>
    ```
2. Create a custom execution environment to test your agent in the playground:
   - Open the `.env` file.
   - Set `DATAROBOT_DEFAULT_EXECUTION_ENVIRONMENT=` to empty or delete the line completely.
3. **[Optional]** Test your agent image locally to ensure the new package works correctly:
    ```bash
      cd agent_generic_base/docker_context  # or your chosen agent directory
      docker build -f Dockerfile . -t docker_context_test
    ```

After completing these steps, when you run `task build` or `task deploy`, the new environment will be automatically
built the first time. Subsequent builds will use the cached environment if the requirements have not changed. The new
environment will be automatically linked and used for all your agent components, models, and deployments.
