<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-templates">
    <img src="docs/img/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">DataRobot Agentic Workflow Templates</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/gen-ai/genai-agents/index.html">Agentic Workflows</a>
  ·
  <a href="/docs/getting-started.md">Getting Started</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/datarobot-agent-templates/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/datarobot-agent-templates?label=version" alt="Latest Release">
  </a>
  <a href="LICENSE.txt">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-templates" alt="License">
  </a>
</p>

This repository provides ready-to-use templates for building and deploying AI agents with multi-agent frameworks. 
These templates streamline the process of setting up your own agents with minimal configuration requirements. These 
templates support local development and testing, as well as deployment to production environments within DataRobot.

If you are new to developing agentic workflows in DataRobot, we recommend starting with the
[Getting Started](/docs/getting-started.md) guide which will help you create a simple document creation agentic workflow example.

---
### DataRobot Agent Templates Navigation
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

## Available templates

This repository includes templates for three popular agent frameworks and a generic base template that can 
be adapted to any framework of your choice. Each template includes a simple example agentic workflow with 3 agents and 
3 tasks.

| Framework        | Description                                              | GitHub Repo | Docs  |
|------------------|----------------------------------------------------------|-------------|-------|
| **CrewAI**       | A multi-agent framework with focus on role-based agents. | [GitHub](https://github.com/crewAIInc/crewAI)       | [Docs](https://docs.crewai.com/)|
| **Generic Base** | A flexible template for any custom framework.            | -           | -     |
| **LangGraph**    | Multi-agent orchestration with state graphs.             | [GitHub](https://github.com/langchain-ai/langgraph) | [Docs](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)|
| **Llama-Index**  | A framework for building RAG systems.                    | [GitHub](https://github.com/run-llama/llama_index)  | [Docs](https://gpt-index.readthedocs.io/en/latest/)|

## Cloning the repository
#### For cloud users:
_Clone the repository to your local machine using Git or you can 
[download it as a ZIP file](https://github.com/datarobot-community/datarobot-agent-templates/archive/refs/heads/main.zip)._
```bash
git clone https://github.com/datarobot-community/datarobot-agent-templates.git
```

#### For on-premise users:
_Clone the release branch for your installation using Git:_
```bash
git clone -b release/11.1 https://github.com/datarobot-community/datarobot-agent-templates.git
```

## Get help

If you encounter issues or have questions, use one of the following options:
- Check that your template is up to date by following the [Updating Agentic Templates](/docs/getting-started-updating.md) guide.
- Check the documentation for your chosen framework.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-templates).
