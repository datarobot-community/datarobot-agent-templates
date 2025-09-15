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

# Updating Agentic Templates

Agentic workflows and frameworks are actively developed and improved. We regularly update base images to support
the latest versions of the frameworks, libraries, and tools used in these templates. Frameworks may introduce
breaking changes, deprecate features, or add new capabilities that can enhance your agents. To take advantage of the
latest features, and ensure compatibility with the latest versions of DataRobot you should periodically update your
agentic templates to include the latest changes.

**It is only necessary to regularly update templates being used to actively develop a new agentic workflow.**

> **IMPORTANT**: Pre-built agent docker images are updated regularly to include the latest bug fixes and improvements.
> It is highly recommended to update your agentic templates to use the latest code to ensure compatibility with
> these base images. Out of date templates may lead to unexpected behavior and errors.

> **NOTE**: Deployed agents and agentic workflows always use fixed docker base images. These are never automatically 
> updated when you update your local templates. You will need to **rebuild** and **redeploy** your agents to upgrade
> them to the latest base images. **You can also leave these deployments as-is if you do not wish to update them.**

## Steps to Update
1. Navigate to your local copy of the agentic-templates repository.
2. Ensure you are on the branch you want to update (e.g., `main`).
3. Pull the latest changes from the remote repository:
   ```bash
   git pull origin main
   # If you are using a different release, replace 'main' with your release branch name
   # e.g., git pull origin release/11.1 for on-premise users
   ```
4. Review the changes and updates made to the templates. You can use `git log` and `git diff` to see what has changed.
5. If you have made custom modifications to your templates, you may need to manually merge these changes with the latest updates.
6. Run the following command to update your local dependencies and refresh your development environment:
   ```bash
   task install
   ```
7. Test your updated templates to ensure they work as expected with the latest version of DataRobot.

If you are working on a different branch you may need to rebase your branch onto the latest `main` branch:
   ```bash
   git checkout your-branch
   git fetch origin
   git rebase origin/main
   # If you are using a different release, replace 'origin/main' with your release branch name
   # e.g., git rebase origin/release/11.1 for on-premise users
   ```

## Troubleshooting
Templates are developed such that modifications to the user facing files (e.g., `custom.py`, `agent.py`,  
`Dockerfile`, etc.)  are minimized. Most updates will be in the underlying framework code, image dependencies and
helper classes. If you have modified these files you may need to manually merge changes.
 
- If you encounter merge conflicts during the update process, carefully resolve them by reviewing the conflicting files
  and deciding which changes to keep.
- You **can always use a custom-built image** if you need to indefinitely maintain specific dependencies or
  configurations. The simplest way to do this is to use the `docker_context` as your agent base image. For more
  details about using the provided `docker_context` see the 
  [Adding Python Packages to Your Agent Environment](/docs/developing-agents-python-requirements.md) documentation
  and follow the `Updating the Docker Execution Environment` section as needed. **You do not need to add additional
  packages if you do not need to.**
- Make sure to run `task install` to refresh your local development environment after updating the templates.
- If you experience issues after updating, consider reaching out to the DataRobot community or support for assistance.
