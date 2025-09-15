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

# Developing Agents

Developing an agent involves editing the `custom_model` source code, and a variety of tools and commands are provided 
to help you test and deploy your agent during the development process.

For agentic platform specific assistance beyond the scope of the demos provided in this repository,
please see the official documentation for each framework:
- [CrewAI Documentation](https://docs.crewai.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)
- [Llama-Index Documentation](https://gpt-index.readthedocs.io/en/latest/)

**You can use the `generic_base` template to build an agent using any framework of your choice. However, you will need 
to implement the agent logic and structure yourself, as this template does not include any pre-defined agent code.**

## Modify the agent code

The first step in developing your agent is to modify the agent code to implement your desired functionality.
The main agent code is located in the `custom_model` directory inside the framework-specific directory you selected when
you created the project. For example, if you selected the CrewAI framework, the path would be `agent_crewai/custom_model`.

| File | Purpose |
|------|---------|
| `agent.py` | The main agent implementation file. |
| `custom.py` | Handles execution of the agent in DataRobot. |
| `helpers.py` | Helper functions for the agent. |
| `tools_client.py` | Tool definitions for the agent. |

The main class you need to modify is in `agent.py`. See this class for details of the implementation
based on the framework for which you are developing.

The agent template provides you with a simple example that contains 3 agents and 3 tasks. You can modify this code
to add more agents, tasks, and tools as needed.  Each agent is connected to an LLM provider, which is specified by 
the `def llm` function in the `agent.py` file. You can modify this function to change the LLM provider or its 
configuration. See the [Configuring LLM providers](/docs/developing-agents-llm-providers.md) documentation for more 
details.

## Testing the agent during local development

You can test your agent locally using the development server provided in the template. This allows you to run and debug
your agent code without deploying it to DataRobot.

To submit a test query to your agent, use the following command from the root directory:

```bash
task agent:cli -- execute --user_prompt "Write a document about the history of AI."
```

This command will run the agent locally and print the output to the console. You can modify the query to test different
inputs and scenarios. For additional local CLI commands that are available, see the 
[Using the agent CLI](/docs/developing-agents-cli.md) documentation.

## Build an agent for testing in the DataRobot LLM Playground (Optional)

To create a custom model that can be refined using the DataRobot LLM Playground.

```bash
task build
```

This command runs the Pulumi infrastructure to create a custom model in DataRobot but does not create a full 
production deployment. This is significantly faster for iterative cloud development and testing.

For more examples on working with agents in the `DataRobot LLM Playground`, see the 
[DataRobot Agentic Playground Tutorial](https://docs.datarobot.com/en/docs/gen-ai/genai-agents/agentic-playground.html).

> **NOTE:** The `task build` command will remove any existing deployments. These can be recreated using `task deploy`
> if they are removed, but the new deployments will have different deployment IDs.

## Deploy an agent for production use

To create a full production-grade deployment:

```bash
task deploy
```

This command builds the custom model and creates a production deployment with the necessary infrastructure, 
which takes longer but provides a complete production environment. The deployment is a standard DataRobot deployment
which includes full monitoring, logging, and scaling capabilities. For more information about DataRobot deployments,
see the [DataRobot Deployment documentation](https://docs.datarobot.com/en/docs/mlops/deployment/index.html#deployment).

### Viewing tracing and logs for a deployed agent

Once your agent is deployed, you can view the logs and traces in the DataRobot UI. Navigate to the "Deployments" section
under "Console", select your deployment. Under the "Monitoring" tab, you can view logs, metrics, and traces for your 
agent. For more information on monitoring deployments and understanding agent traces please see the
[Deployment Monitoring and Data Exploration Documentation](
https://docs.datarobot.com/en/docs/workbench/nxt-console/nxt-monitoring/nxt-data-exploration.html).

### Manually Deploying an agent using pulumi terraform (for debugging or refining pulumi terraform code)

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

The `AGENT_DEPLOY` environment variable controls whether Pulumi creates only the custom model (`DEPLOY=0`) or both 
the custom model and a production deployment (`DEPLOY=1`). If not set, Pulumi defaults to full deployment mode.

Pulumi will prompt you to confirm the resources to be created or updated.

## Next steps

After deployment, your agent will be available in your DataRobot environment. You can:

1. Test your deployed agent using `task cli -- execute-deployment`.
2. Integrate your agent with other DataRobot services.
3. Monitor usage and performance in the DataRobot dashboard.

You can also find more examples and documentation from specific frameworks to help you build more complex agents,
add tools, and define workflows and tasks.
- [CrewAI GitHub Repository](https://github.com/crewAIInc/crewAI)
- [LangGraph GitHub Repository](https://github.com/langchain-ai/langgraph)
- [Llama-Index GitHub Repository](https://github.com/run-llama/llama_index)