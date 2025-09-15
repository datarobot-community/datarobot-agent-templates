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

# Getting started

> **NOTE:** Please ensure all [prerequisites](/docs/getting-started-prerequisites.md) are installed before proceeding with the following workflow.

This guide will help you get started with the DataRobot Agent Templates repository. It will walk you through the
steps to setup a simple document creation agentic workflow example using one of the provided templates. The example 
agentic workflow contains 3 agents and tasks. These are:
- Researcher Agent: Gathers information on a given topic using web search.
- Writer Agent: Writes a document based on the research provided.
- Editor Agent: Reviews and edits the document for clarity and correctness.

The agentic workflow will produce a Markdown document about the topic specified in the test queries.

### Step 1: Clone the repository

Clone the repository to your local machine using Git or you can download it as a ZIP file.

```bash
git clone https://github.com/datarobot-community/datarobot-agent-templates.git
cd datarobot-agent-templates
```

For on-premise users, please ensure you clone the correct branch for your release
(e.g. `git clone -b release/11.1 https://github.com/datarobot-community/datarobot-agent-templates.git`).

> **NOTE**: You may wish to [fork the repository](
> https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
> to your own GitHub account if you plan to make changes and develop your own
> agentic workflows. You may also wish to [change the remote repository url](
> https://docs.github.com/en/get-started/git-basics/managing-remote-repositories) to a different repositroy or
> [create a new repository](
> https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) to track
> your ongoing code changes.

### Step 2: Configure environment variables

Create an `.env` file in the root directory to store your configuration. This must be done before running any
additional commands.

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit the file with your preferred editor
nano .env  # or vim .env, code .env, etc.
```

Your `.env` file must contain, at minimum, the following variables. We recommend leaving all other variables at their
default values during the getting started process, and you can change them as needed during your development.

```bash
# DataRobot API keys and endpoint
DATAROBOT_API_TOKEN=<Your API Token>
DATAROBOT_ENDPOINT=https://app.datarobot.com/api/v2 # Or your datarobot endpoint
```

- You can generate an API token from the DataRobot UI by navigating to your user profile and selecting "API Tokens". For
more information on generating API tokens, please refer to the
[DataRobot API keys and tools](
https://docs.datarobot.com/en/docs/get-started/acct-mgmt/acct-settings/api-key-mgmt.html) documentation.
- **For cloud users** you should use a cloud endpoint (e.g. https://app.datarobot.com/api/v2, 
https://app.eu.datarobot.com/api/v2, or https://app.jp.datarobot.com/api/v2).
- **For on-premise users,** please use the appropriate endpoint for your environment or reach out to support for
more assistance.


### Step 3: Start and choose an agent framework

The templates provide a helper script to start the development process. Just run

```bash
task start
```

> **NOTE:** If you encounter an error running `task start` or `task install`, please ensure you have
> completed all the steps in the [Prerequisites](/docs/getting-started-prerequisites.md) guide.

This repository includes four templates to get started. They are selected during the `tast start` quickstart process.

| Directory | Framework | Description |
|-----------|-----------|-------------|
| `agent_crewai` | CrewAI | Role-based multi-agent collaboration framework |
| `agent_langgraph` | LangGraph | State-based orchestration framework |
| `agent_llamaindex` | Llama-Index | RAG-focused framework |
| `agent_generic_base` | Generic | Base template for any framework |

Answer the prompts to select your agent framework and configure the initial setup. After selecting a framework in 
the quickstart process, **all quickstart files and unused agentic workflow templates 
will be removed** from the repository. If you wish to switch frameworks later, you can re-clone the repository or 
copy the desired framework directory from a fresh clone.

After running `task start` you can run `task` from the root directory to see available commands.

> **IMPORTANT:** Before continuing to the next step, please ensure that you have run `task install`, as prompted
> during the quickstart, to install and set up the agent and infrastructure environments.

### Step 4: Test your agent is working for local development
You can use the CLI to test your agent locally. Local testing still requires a connection to DataRobot to
communicate with the LLM provider. You will need to ensure that your `.env` file is correctly configured with your
DataRobot API token and endpoint.

Run the following command from the root directory to test your agent:

```bash
task agent:cli -- execute --user_prompt 'Tell me about Generative AI'
```

At this point you are able to modify the agent code and test it locally. We recommend continuing 
on to the next step to deploy your agent to DataRobot and test it in a production-like environment.

### Step 5: Deploy your agent to the DataRobot cloud
When you are ready to deploy your agent to DataRobot, run the following command from the root directory:
```bash
task deploy
```

- After executing `task deploy` you will be met with the pulumi preview screen. This shows you what changes
will be made to your DataRobot environment. You will need to approve these changes before the deployment
process continues. Type `yes` or select the option with the arrow keys and press enter to continue.
- After selecting `yes` the deployment process will continue. This may take several minutes to complete as
it needs to build and deploy your agent code and all the required infrastructure. You will see logs in the terminal
as the process continues. When the process is complete you will see a summary of the deployed resources and a listing
of any important IDs and URLs.
- If this is your first time deploying, you will need to provide a **pulumi stack name**. This is appended to the
deployed resources in DataRobot to help you identify them. You can use any name you like, for 
example `myagent`, `test`, `dev` or `production`.

### Step 6: Test your production-ready deployed agent
You can also use the agent CLI to test your deployed agent. This process is similar to testing locally except you
will also need to provide the deployment ID of your deployed agent. The deployment ID which is shown after the
deployment process is complete.

```bash
task agent:cli -- execute-deployment --deployment_id %your_id% --user_prompt 'Tell me about Generative AI'
```
- You can find the deployment ID in the terminal after running `task deploy`.
- You can also find the deployment ID in the DataRobot UI under the "Deployments" section under "Console". After
selecting your deployment, the deployment ID is shown in the URL and under the "Details" section.
- For more information on DataRobot deployments in general, please refer to the [DataRobot Deployment documentation](
https://docs.datarobot.com/en/docs/mlops/deployment/index.html).

### Step 7: Develop your agent
You are now ready to start developing your agent! Please refer to the
[Developing Agents](/docs/developing-agents.md) documentation for the next steps on:
  - [Developing your agent](/docs/developing-agents.md)
  - [Using the agent CLI](/docs/developing-agents-cli.md)
  - [Adding python requirements](/docs/developing-agents-python-requirements.md)
  - [Configuring LLM providers](/docs/developing-agents-llm-providers.md)
  - [Adding tools to your agent](/docs/developing-agents-tools.md)
  - [Updating your template when new versions are released](/docs/getting-started-updating.md)
