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
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/datarobot-agent-templates" alt="License">
  </a>
</p>

This repository provides ready-to-use templates for building and deploying agentic workflows with multi-agent frameworks.
Agentic templates streamline the process of setting up new workflows with minimal configuration requirements.
They support local development and testing, as well as deployment to production environments within DataRobot.

The full table of contents is available below, but you can also go directly to the [Quick Start](#quick-start) section to get started.

---
# DataRobot Agent Templates Navigation
- [Installing prerequisites](/docs/getting-started-prerequisites.md)
- [Getting started](/docs/getting-started.md)
- [Updating Agentic Templates](/docs/getting-started-updating.md)
- Developing Agents
  - [Developing your agent](/docs/developing-agents.md)
  - [Using the agent CLI](/docs/developing-agents-cli.md)
  - [Adding python requirements](/docs/developing-agents-python-requirements.md)
  - [Configuring LLM providers](/docs/developing-agents-llm-providers.md)
  - [Adding tools to your agent](/docs/developing-agents-tools.md)
---

# Available templates

This repository includes templates for three popular agent frameworks and a generic base template that can be adapted to any framework of your choice.
Each template includes a simple example agentic workflow with 3 agents and 3 tasks.

| Framework        | Description                                                | GitHub Repo | Docs  |
|------------------|------------------------------------------------------------|-------------|-------|
| **CrewAI**       | A multi-agent framework with focus on role-based agents.   | [GitHub](https://github.com/crewAIInc/crewAI)       | [Docs](https://docs.crewai.com/)|
| **Generic Base** | A barebones template that can be adapted to any framework. | -           | -     |
| **LangGraph**    | Multi-agent orchestration with state graphs.               | [GitHub](https://github.com/langchain-ai/langgraph) | [Docs](https://langchain-ai.github.io/langgraph/concepts/why-langgraph/)|
| **Llama-Index**  | A framework for building RAG systems.                      | [GitHub](https://github.com/run-llama/llama_index)  | [Docs](https://gpt-index.readthedocs.io/en/latest/)|

# Quick Start

This documentation demonstrates how to set up and deploy an agentic workflow using one of the available templates.
The process consists of the following steps:

1. [Installing prerequisites](/docs/getting-started-prerequisites.md)
2. [Get started](/docs/getting-started.md)
3. [Developing your agent](/docs/developing-agents.md)

From here, proceed to [Installing prerequisites](/docs/getting-started-prerequisites.md).

# Get help

If you encounter issues or have questions, use one of the following options:
- Check that your template is up to date by following the [Updating Agentic Templates](/docs/getting-started-updating.md) guide.
- Check the documentation for your chosen framework.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/datarobot-agent-templates).
