# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased Changes

## 11.3.3

- Do not run dev server in autoreload mode when running CLI
- Streamlined integration of agent with MCP server
- Langgraph MCP integration
- Always create the session secret in agent

## 11.3.2

- Documentations updates.
- `NatAgent` is now a part of `datarobot-genai`.
- Pin execution environment version.

## 11.3.1

- Documentations updates.
- Hotfix for datarobot-moderations.

## 11.3.0
- Comprehensive LLM Provider Support - Added complete support for multiple LLM configurations with streamlined switching between providers.
- Now supports LLM Gateway Direct, LLM Blueprint with LLM Gateway, LLM Blueprint with External LLMs (Azure OpenAI, Amazon Bedrock, Google Vertex AI, Anthropic), Registered Models (NVIDIA NIMs), and Already Deployed Models.
- Automatic credential management through DataRobot's secure credential system, flexible model selection, and simplified configuration through environment variables and symlinks.
- See the updated [Configuring LLM Providers documentation](/docs/developing-agents-llm-providers.md) for setup instructions and examples.
- Add built-in support for connecting agents to MCP servers
- Rename `api_tests` root folder to `tests` for clarity
- Add .env helper instead of raising error if a `.env` is not found
- If `PULUMI_STACK_NAME` is in the environment, then the stack will be automatically passed to pulumi
- Update `datarobot` package to include latest functionality
- Fix an issue where stream=true on an agent that didn't support streaming would raise an error
- Add support for `datarobot_genai` package to streamline development
- Remove docker_context by default. Replace with `task create-docker-context` if needed.
- All package installation auto-synchronized with `uv` by default
- Support for full streaming in langgraph
- Initial support for `async` invoke capabilities inside servers
- Support for development server execution for faster iteration. Can optionally use `task agent:cli START_DEV=1 -- ` to automatically start and stop a dev server to use legacy dev flow.

## 11.2.4
- Add support for streaming in agentic workflows
- Add support for streaming to the agent:cli tools
- Update CLI documentation to include streaming and non-streaming commands
- Add built-in streaming support to langgraph template
- Fix issue with URLs related to deployments not always previously working
- Rename `def run` in agents to `def invoke` to conform better with other frameworks
- Refactor agents to use a unified return response from `invoke`
- Reduce confusing response formatting and remove unneeded helper functions
- Update package versions
- Add initial NAT package support to framework
- Add example documentation for calling deployed agents and using streaming


## 11.2.3
- Fix connecting to llm documentation
- Optimize agent startup time
- Resolve llama-index issues
- Sync local uv.lock file to docker images during deployments

## 11.2.2
- Remove Taskfile_development.yml to avoid confusion
- Reduce local environment imports
- Add support for Nvidia-NAT local environment
- Add initial local dockerfile for Nvidia-NAT
- Remove hidden docker imports from base image
- Update packages to address CVEs and vulnerabilities
- Upgrade core agentic framework packages to latest versions
- Remove some unnecessary uv.lock entries to improve compatibility
- Improve the readability of Taskfile commands by reducing unnecessary commands
- Fix cli commands to all be agent:cli
- Resolve CVE issues in latest releases
- Remove dependence on requirements.txt in dockerfile in preparation for moving everything to pyproject.toml
- Migrate all infra and build logic to pyproject.toml and uv
- Streamline CLI code to improve readability of the agent directory

## 11.2.1
- Place github repo heath files inside .github
- Fix uv brew installation command in docs
- Improve some wording in the docs around pulumi and clean up some wordy areas
- Do not ship dev-only tests in the published package to avoid confusion
- Suppress response output logging during CLI execution and display link to output file
- Improve quickstart script to handle invalid inputs better
- Reorder functions and methods in agents to make them more discoverable
- Redo docstrings in agents to make them more direct and concise
- Fix SC3046 error in dockerfile
- Remove agent feature flag warnings in pulumi
- Fix CVEs in multiple packages

## 11.2.0
- List Windows as unsupported OS in docs
- Add new pre-requisite installation docs with better links and more clarity
- Rename AI Catalog Tool to Data Registry tool
- Improve global tools documentation examples
- Improve the documentation around repositories and updating templates
- Fix emoji handling during quickstart for Windows environments
- Bump moderation library version
- Remove telemetry helper files completely to improve readability
- Remove auth.py and merge it into tools_client.py to improve readability
- Corrected type errors in command line args
- Catch crewai import errors
- Update langchain to latest release to address CVEs
- Fix broken env variable in Taskfile for windows environments
- Add pydantic-ai to base image

## 0.2.9
- Add initial docs for adding basic tools to agents.
- Add Datarobot Global Tools examples to docs.

## 0.2.8
- Fix broken documentation links.
- Improve sections of documentation and add more links to related DataRobot tutorials.
- Add CODE_OF_CONDUCT and CONTRIBUTING files to the repository.
- Update release pipeline to properly inherit SHA from the configurations.

## 0.2.7
- Add documentation and examples for connecting to different LLM providers.

## 0.2.6
- Deploy an agentic playground and show / export a link to it

## 0.2.5
- Bump agent component to 1.2.4
- Split up and refactor documentation into multiple files for easier navigation.
- Add instructions for using the CLI to test agents locally and deployed.
- Fix quickstart script to properly remove all unused files.
- Make quickstart script less verbose in the terminal.
- Fix inconsistent wording in quickstart prompts.
- Add tasks to run tests locally on rendered templates
- Add tasks to test the CLI on the base agent locally
- Bump request timeout to 20 min
- Fix agent env setup in notebook
- Remove af-component-agent embedded docs and replace with a link to public docs

## 0.2.4
- Improvements to release process.
- Minor fixes to task environment.

## 0.2.3
- Critical fix to custom.py to fix issue with using the LLM gateway when no variable is set.

## 0.2.2
- Fix and simplify using an external deployment as an LLM instead of LLM gateway.

## 0.2.1
- Update pulumi to follow naming convention in created assets: `[$stack_name] $agent_name`
- Restore usage of Auth SDK

## 0.2.0
- Minor fixes to templates.
- Ensure pyarrow is pinned to < 21.0.0 to prevent potential ragas issues in some cases.
- Update datarobot package to latest release.
- Update datarobot-drum package to the latest release, brings support for kwargs and headers.
- Update datarobot-moderations to the latest release.
- Other select packages updated.

## 0.1.13
- Add pipeline for automating the template repository update process when a new component is released.
- Add pipeline for performing fully tested release to `datarobot-community` org
- Fix avd-ds-0002 in `api test` dockerfile
- Remove unusable requirements.txt
- Add 90 second default timeout for LLM calls to code templates
- Add instructions how to reduce the size of the responses to the template code
- Resolve starlette vulnerability in docker_context containers
- Do not raise an error in the `llm` component if llm gateway is enabled.

## 0.1.12
- Add pipeline for bumping release version automatically and updating changelog versions.
- Add end to end testing automations

## 0.1.11
- Revert inline runner execution logic

## 0.1.10
- Use `uv run pulumi` to run pulumi commands in the CLI instead of `pulumi` directly.
- Add support for using `docker_image` in addition to the `docker_context` for building environments.
- Pin newest datarobot package.
- Use `datarobot[auth]` for tool authentication.
- Add support for `mcp` to the base environments.
- Documentation updates.

## 0.1.9
- Raise informative error instead of exit to make pulumi more stable on linux distributions.

## 0.1.8
- Critical fix to public repo when files are missing during quickstart. Should raise warnings instead of errors now.

## 0.1.7
- Critical bug fix to remove asyncio from docker containers due to new python versions being incompatible with outdated packages.

## 0.1.6
- Update documentation to explain adding packages to the execution environment and custom models.
- Update moderations-lib to the latest revision.
- Add `ENABLE_LLM_GATEWAY_INFERENCE` default runtime param to custom models.
- Cleanup quickstart.py after running repo quickstart.
- Disable hidden remote tracing for all frameworks by default.
- Remove overrides for litellm version and update crewai to use the latest version.
- Add CLI support for running custom models with `execute-custom-model` command.
- Remove `RELEASE.yaml` with quickstart.py.
- Show a more condensed error on output file missing in CLI to reduce confusion.

## 0.1.5
- Update agent component with dependency fixes and pin packages.
- Add DRUM serverless execution support using `--use_serverless` with the CLI.
- Add UV lock files to the repo to prevent environment regressions by malformed packages
- Fix toolmessage
- Address critical CVE vulnerabilities in docker images
- Add httpx tracing support to all frameworks

## 0.1.4
- Update packages to address issues in moderations and tracing.

## 0.1.3
- Add testing for pulumi infrastructure
- Address protobuf CVE
- Update function `api_base_litellm` with regex to handle different API base URLs

## 0.1.2
- Add ability to send chat completion to CLI as complete json file
- A default environment is now provided in the `.env.sample` and building from context is now optional, not required
- Ignore temporary or build files when creating the `custom_model`
- Renamed pulumi variables to be more concise and uniform
- Remove deprecated clientId parameter everywhere from chat endpoints
- Make DRUM server port retrieval dynamic
- Switched target for dev server to `agenticworkflow`
- Unpin chainguard base image to allow for latest updates
- Ensure Llamaindex has a `GPT` model or tools don't work
- Bump requests to fix the CVE

## 0.1.1
- Add support for `AgenticWorkflow` agent target type
- Remove unused runtime parameter
- Re-introduce moderation library
- Add stdout log handling in ipykernel environments
- Use UV override for correct LiteLLM version
- Add end-to-end tests for agent execution
- Fixes to tools
- Address jupyter-core CVE
- Support tracing
- Improvements and fixes to environments
- Documentation improvements

## 0.1.0
- Changes to `run_agent.py`
- Improve component testing
- Add basic support for moderations helpers for agents
- Ensure all taskfile commands are properly inherited from the `taskfile` template
- Add descriptions and inheritance to all taskfile commands
- Add quickstart functionality to the repository
- Upgrade LiteLLM
- Add datarobot-moderations package to requirements
- Bump `datarobot-pulumi-utils`
- Add `pyproject.toml` to the root to assist with quickstart and development
- Allow agents to receive string or json gracefully
- Ensure that environment variables are properly passed to LiteLLM with helper functions

## 0.0.6
- Documentation and getting started rewritten and improved.
- Add Taskfile improvements for development.
- Support `requirements.txt` integration in `custom_model` folder.
- Add `build` and `deploy` commands to the `taskfile` for `pulumi` integration.
- Add feature flag verification during `pulumi` operations.
- Allow dynamically passing model name to agents.
- Pin ipykernel to resolve issues.
- Bump requirements to resolve CVEs.
- Improve repository test coverage and refine execution testing scripts.

## 0.0.5
- Finalize support for open telemetry to all frameworks.
- Update execution environments to resolve CVEs.
- Revert target types to `textgeneration` to resolve deployment issues.

## 0.0.4
- Add initial support for open telemetry.

## 0.0.3
- Bug fixes
- Allow sending OpenAI complete dictionary to run_agent.
- Add support for integrating agent tooling.

## 0.0.2
- Add support for `LlamaIndex` agents.

## 0.0.1
- Add `af-component-agent` template to the repository.
- Update the `agent_crewai` agent with a simple flow.
- Added `agent_cli` and `taskfile` to the `agent_crewai` agent.
- Add support for `CrewAI` agents.
- Add support for `Langgraph` agents.
- Complete development of `run_agent.py` concept.
