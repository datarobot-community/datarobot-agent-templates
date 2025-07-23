# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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
