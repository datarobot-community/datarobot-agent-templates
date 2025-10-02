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

# LLM Providers
One of the key components of an LLM agent is the underlying LLM provider. DataRobot allows users to connect to
virtually any LLM backend for their agentic workflows. LLM connections can be simplified by using the DataRobot
LLM Gateway or a DataRobot deployment (including NIM deployments). Alternatively, you can connect to any external
LLM provider that supports the OpenAI API standard.

To help you successfully connect to your desired LLM provider, the following sections provide example code snippets for
connecting to various LLM providers using the CrewAI, LangGraph, and LlamaIndex frameworks. You can use these snippets
as a starting point and modify them as needed to fit your specific use case.

### Providers and Examples
- [DataRobot LLM Gateway](#datarobot-llm-gateway)
- [DataRobot Hosted LLM Deployments](#datarobot-hosted-llm-deployments)
- [DataRobot NIM Deployments](#datarobot-nim-deployments)
- [OpenAI API](#openai-api-configuration)
- [Anthropic API](#anthropic-api-configuration)
- [Gemini API](#gemini-api-configuration)
- [Other Providers](#other-providers)

## DataRobot

### DataRobot LLM Gateway
The LLM gateway provides a streamlined way to access LLMs proxied via DataRobot. The gateway is available for both
cloud and on-premise users.

You can retrieve a list of available models for you account by running the following `CURL` command:

`curl -X GET -H "Authorization: Bearer $DATAROBOT_API_TOKEN" "$DATAROBOT_ENDPOINT/genai/llmgw/catalog/" | jq | grep 'model":'`

#### CrewAI
```python
    from crewai import LLM
    
    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use DataRobot's LLM Gateway."""
        return LLM(
            # Note: The `datarobot/` prefix is required for LiteLLM to properly route requests
            # through the LLM Gateway
            model="datarobot/azure/gpt-4o-mini", # Define the model name you want to use
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base="https://app.datarobot.com", # DataRobot endpoint
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_community.chat_models import ChatLiteLLM
    
    def llm(self) -> ChatLiteLLM:
        """Returns a ChatLiteLLM instance configured to use DataRobot's LLM Gateway."""
        return ChatLiteLLM(
            # Note: The `datarobot/` prefix is required for LiteLLM to properly route requests
            # through the LLM Gateway
            model="datarobot/azure/gpt-4o-mini", # Define the model name you want to use
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base="https://app.datarobot.com", # DataRobot endpoint
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    # DataRobotLiteLLM class is included in the `agent.py` file
    
    def llm(self) -> DataRobotLiteLLM:
        """Returns a DataRobotLiteLLM instance configured to use DataRobot's LLM Gateway."""
        return DataRobotLiteLLM(
            # Note: The `datarobot/` prefix is required for LiteLLM to properly route requests
            # through the LLM Gateway
            model="datarobot/azure/gpt-4o-mini", # Define the matching openai model name
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base="https://app.datarobot.com", # DataRobot endpoint
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

[Back to top](#llm-providers)

## DataRobot Hosted LLM Deployments

You can easily connect to DataRobot-hosted LLM deployments as an LLM provider for your agents. The template provides
one example for creating and deploying a DataRobot playground model as an LLM provider. Additionally you can
[Deploy an LLM from the DataRobot Playground](https://docs.datarobot.com/en/docs/gen-ai/playground-tools/deploy-llm.html)
or even host
[Hugging Face models as LLM deployments on DataRobot](https://docs.datarobot.com/en/docs/workbench/nxt-registry/nxt-model-workshop/nxt-open-source-textgen-template.html#deploy-llms-from-the-hugging-face-hub).
DataRobot hosted LLMs can also provide you with access to many **moderations and guardrails** to help you manage
and govern your models.

#### Template Example
The template provides example pulumi for automatically creating an LLM deployment and using this custom deployment
in your agents. A sample Playground Model is provided in the `infra/infra/llm_datarobot.py` pulumi file. You can use 
the example by doing the following:

1. Edit your `.env` file:
   ```bash
   USE_DATAROBOT_LLM_GATEWAY=false
   ```
2. If you wish to use an existing LLM deployment, set in `.env`:
   ```bash
   LLM_DATAROBOT_DEPLOYMENT_ID=<your_deployment_id>
   ```
> For local testing you must run `task build` once, to create the deployment, and then set the generated deployment ID
> in your `.env` file. This allows your local agent to connect to the deployment created in DataRobot.

#### CrewAI
```python
    from crewai import LLM
    
    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use a DataRobot Deployment."""
        return LLM(
            # Note: For DataRobot deployments, some models require removing the `datarobot/` prefix
            # from the model field. Test with and without the prefix if you encounter issues.
            model="datarobot/azure/gpt-4o-mini", # Define the matching model name
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}/", # Deployment URL
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_community.chat_models import ChatLiteLLM
    
    def llm(self) -> ChatLiteLLM:
        """Returns a ChatLiteLLM instance configured to use a DataRobot Deployment."""
        return ChatLiteLLM(
            # Note: For DataRobot deployments, some models require removing the `datarobot/` prefix
            # from the model field. Test with and without the prefix if you encounter issues.
            model="datarobot/azure/gpt-4o-mini", # Define the matching model name
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}/", # Deployment URL
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    # DataRobotLiteLLM class is included in the `agent.py` file
    
    def llm(self) -> DataRobotLiteLLM:
        """Returns a DataRobotLiteLLM instance configured to use a DataRobot Deployment."""
        return DataRobotLiteLLM(
            # Note: For DataRobot deployments, some models require removing the `datarobot/` prefix
            # from the model field. Test with and without the prefix if you encounter issues.
            model="datarobot/azure/gpt-4o-mini", # Define the matching model name
            # Note: The `/chat/completions` endpoint will be automatically appended by LiteLLM
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}/", # Deployment URL
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

[Back to top](#llm-providers)

## DataRobot NIM Deployments
The template supports using NIM deployments as an LLM provider. This allows you to use any NIM deployment hosted on
DataRobot as an LLM provider for your agent. You must make sure that the `model` field in your LLM definition matches the
NIM expected model name for the deployment.

To create a new NIM deployment, you can follow the instructions in the
[DataRobot NIM documentation](https://docs.datarobot.com/en/docs/gen-ai/genai-integrations/genai-nvidia-integration.html).

#### CrewAI
```python
    from crewai import LLM
    
    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use a NIM deployed on DataRobot."""
        return LLM(
            model="meta/llama3-8b-instruct", # Define the matching model name, not the provider model name
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}", # NIM Deployment URL
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_openai import ChatOpenAI
    
    def llm(self) -> ChatOpenAI:
        """Returns a ChatOpenAI instance configured to use a NIM deployed on DataRobot."""
        return ChatOpenAI(
            model="meta/llama3-8b-instruct", # Define the matching model name, not the provider model name
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}", # NIM Deployment URL
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    from llama_index.llms.openai_like import OpenAILike
    
    def llm(self) -> OpenAILike:
        """Returns an OpenAILike instance configured to use a NIM deployed on DataRobot."""
        return OpenAILike(
            model="meta/llama3-8b-instruct", # Define the matching model name, not the provider model name
            api_base=f"https://app.datarobot.com/api/v2/deployments/{DEPLOYMENT_ID}/v1", # NIM Deployment URL with /v1 endpoint
            api_key=self.api_key, # Your DataRobot API key
            timeout=self.timeout, # Optional timeout for requests
            is_chat_model=True, # Enable chat model mode for NIM endpoints
        )
```

[Back to top](#llm-providers)

## OpenAI API Configuration
There are cases where you may want to use an external LLM provider that supports the OpenAI API standard, such as
OpenAI itself. The template supports connecting to any OpenAI-compatible LLM provider. Here are examples for directly
connecting to OpenAI using the CrewAI and LangGraph frameworks.
   
#### CrewAI
```python
    from crewai import LLM
    
    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use OpenAI."""
        return LLM(
            model="gpt-4o-mini", # Define the OpenAI model name
            api_key="YOUR_OPENAI_API_KEY", # Your OpenAI API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_openai import ChatOpenAI
    
    def llm(self) -> ChatOpenAI:
        """Returns a ChatOpenAI instance configured to use OpenAI."""
        return ChatOpenAI(
            model="gpt-4o-mini", # Define the OpenAI model name
            api_key="YOUR_OPENAI_API_KEY", # Your OpenAI API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    from llama_index.llms.openai import OpenAI
    
    def llm(self) -> OpenAI:
        """Returns an OpenAI instance configured to use OpenAI."""
        return OpenAI(
            model="gpt-4o-mini", # Define the OpenAI model name
            api_key="YOUR_OPENAI_API_KEY", # Your OpenAI API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

[Back to top](#llm-providers)

## Anthropic API Configuration
You can connect to Anthropic's Claude models using the Anthropic API. The template supports connecting to Anthropic models
through both CrewAI and LangGraph frameworks. You'll need an Anthropic API key to use these models.

#### CrewAI
```python
    from crewai import LLM

    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use Anthropic."""
        return LLM(
            model="claude-3-5-sonnet-20241022", # Define the Anthropic model name
            api_key="YOUR_ANTRHOPIC_API_KEY", # Your Anthropic API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_anthropic import ChatAnthropic
    
    def llm(self) -> ChatAnthropic:
        """Returns a ChatAnthropic instance configured to use Anthropic."""
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022", # Define the Anthropic model name
            anthropic_api_key="YOUR_ANTRHOPIC_API_KEY", # Your Anthropic API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    from llama_index.llms.anthropic import Anthropic
    
    def llm(self) -> Anthropic:
        """Returns an Anthropic instance configured to use Anthropic."""
        return Anthropic(
            model="claude-3-5-sonnet-20241022", # Define the Anthropic model name
            api_key="YOUR_ANTRHOPIC_API_KEY", # Your Anthropic API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

[Back to top](#llm-providers)

## Gemini API Configuration
You can also connect to Google's Gemini models using the Gemini API. The template supports connecting to Gemini models
through both CrewAI and LangGraph frameworks. You'll need a Google AI API key to use these models.

#### CrewAI
```python
    from crewai import LLM

    def llm(self) -> LLM:
        """Returns a CrewAI LLM instance configured to use Gemini."""
        return LLM(
            model="gemini/gemini-1.5-flash", # Define the Gemini model name
            api_key="YOUR_GEMINI_API_KEY", # Your Google AI API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LangGraph
```python
    from langchain_google_genai import ChatGoogleGenerativeAI

    def llm(self) -> ChatGoogleGenerativeAI:
        """Returns a ChatGoogleGenerativeAI instance configured to use Gemini."""
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", # Define the Gemini model name
            google_api_key="YOUR_GEMINI_API_KEY", # Your Google AI API key
            timeout=self.timeout, # Optional timeout for requests
        )
```

#### LlamaIndex
```python
    from llama_index.llms.gemini import Gemini
    
    def llm(self) -> Gemini:
        """Returns a Gemini instance configured to use Google's Gemini."""
        return Gemini(
            model="gemini-1.5-flash", # Define the Gemini model name
            api_key="YOUR_GEMINI_API_KEY", # Your Google AI api key
            timeout=self.timeout, # Optional timeout for requests
        )
```

[Back to top](#llm-providers)

## Other Providers
You can connect to any other LLM provider that supports the OpenAI API standard by following the
patterns shown in the examples above. For providers that don't natively support the OpenAI API format,
you have several options to help bridge the connection:

### Framework Documentation
Each framework provides comprehensive documentation for connecting to various LLM providers:

- **CrewAI**: Visit the [CrewAI LLM documentation](https://docs.crewai.com/en/concepts/llms) for detailed examples of connecting to different providers
- **LangGraph**: Check the [LangChain LLM integrations](https://python.langchain.com/docs/integrations/llms/) for extensive provider support
- **LlamaIndex**: Refer to the [LlamaIndex LLM modules](https://docs.llamaindex.ai/en/stable/module_guides/models/llms/) for various LLM integrations

### Using LiteLLM for Universal Connectivity
[LiteLLM](https://docs.litellm.ai/) is an excellent library that provides a unified interface for connecting to 100+ LLM providers. It translates requests to match each provider's specific API format, making it easier to connect to providers like:

- Azure OpenAI
- AWS Bedrock
- Google Vertex AI
- Cohere
- Hugging Face
- Ollama
- And many more

For the most up-to-date list of supported providers and configuration examples, visit the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).
