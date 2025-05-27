Google Adapters
==============

The Google adapters provide integration with Google's AI technologies through two separate implementations:

1. **Google GenAI**: For working with Gemini models through Google's Generative AI SDK
2. **Google ADK**: For working with Google's Agent Development Kit

Module: ``contexa_sdk.adapters.google``
---------------------------------------

.. automodule:: contexa_sdk.adapters.google
   :members:
   :undoc-members:
   :show-inheritance:

Google GenAI Adapter
-------------------

The GenAI adapter provides integration with Google's Generative AI SDK for Gemini models.

Module: ``contexa_sdk.adapters.google.genai``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: contexa_sdk.adapters.google.genai
   :members:
   :undoc-members:
   :show-inheritance:

GenAI Functions
~~~~~~~~~~~~~~

.. function:: genai_tool(tool)

   Convert a Contexa tool to a Google GenAI function declaration.

   :param tool: The Contexa tool to convert
   :type tool: ContexaTool or callable
   :return: A function declaration compatible with Google GenAI
   :rtype: callable

.. function:: genai_model(model)

   Convert a Contexa model to a Google GenAI model.

   :param model: The Contexa model to convert
   :type model: ContexaModel
   :return: A Google GenAI model
   :rtype: GenerativeModel

.. function:: genai_agent(agent)

   Convert a Contexa agent to a Google GenAI agent.

   :param agent: The Contexa agent to convert
   :type agent: ContexaAgent
   :return: A Google GenAI agent
   :rtype: object with run() method

.. function:: genai_prompt(prompt)

   Convert a Contexa prompt to a string for Google GenAI.

   :param prompt: The Contexa prompt to convert
   :type prompt: ContexaPrompt
   :return: A string prompt
   :rtype: str

.. function:: genai_handoff(from_agent, to_agent, message)

   Hand off from one Google GenAI agent to another.

   :param from_agent: The agent handing off
   :type from_agent: GenAI agent
   :param to_agent: The agent receiving the handoff
   :type to_agent: GenAI agent
   :param message: The message to pass to the receiving agent
   :type message: str
   :return: The result from the receiving agent
   :rtype: str

Google ADK Adapter
----------------

The ADK adapter provides integration with Google's Agent Development Kit.

Module: ``contexa_sdk.adapters.google.adk``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: contexa_sdk.adapters.google.adk
   :members:
   :undoc-members:
   :show-inheritance:

ADK Functions
~~~~~~~~~~~

.. function:: adk_tool(tool)

   Convert a Contexa tool to a Google ADK tool.

   :param tool: The Contexa tool to convert
   :type tool: ContexaTool or callable
   :return: A Google ADK tool
   :rtype: google.adk.Tool

.. function:: adk_model(model)

   Convert a Contexa model to a Google ADK model configuration.

   :param model: The Contexa model to convert
   :type model: ContexaModel
   :return: A Google ADK model configuration
   :rtype: dict

.. function:: adk_agent(agent)

   Convert a Contexa agent to a Google ADK agent.

   :param agent: The Contexa agent to convert
   :type agent: ContexaAgent
   :return: A Google ADK agent
   :rtype: google.adk.Agent

.. function:: adk_prompt(prompt)

   Convert a Contexa prompt for use with Google ADK.

   :param prompt: The Contexa prompt to convert
   :type prompt: ContexaPrompt
   :return: A string prompt
   :rtype: str

.. function:: adk_handoff(from_agent, to_agent, message)

   Hand off from one Google ADK agent to another.

   :param from_agent: The agent handing off
   :type from_agent: ADK agent
   :param to_agent: The agent receiving the handoff
   :type to_agent: ADK agent
   :param message: The message to pass to the receiving agent
   :type message: str
   :return: The result from the receiving agent
   :rtype: str

Google Adapter Converter
----------------------

Module: ``contexa_sdk.adapters.google.converter``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: contexa_sdk.adapters.google.converter
   :members:
   :undoc-members:
   :show-inheritance:

Examples
-------

GenAI Example
~~~~~~~~~~~

.. code-block:: python

   from contexa_sdk.core.tool import ContexaTool
   from contexa_sdk.core.model import ContexaModel
   from contexa_sdk.core.agent import ContexaAgent
   from contexa_sdk.adapters.google import genai_tool, genai_model, genai_agent

   # Define a tool
   @ContexaTool.register(
       name="search",
       description="Search for information"
   )
   async def search(query: str) -> str:
       return f"Results for {query}"

   # Create a model and agent
   model = ContexaModel(provider="google", model_name="gemini-pro")
   agent = ContexaAgent(name="Assistant", model=model, tools=[search])

   # Convert to Google GenAI
   genai_assistant = genai_agent(agent)
   result = await genai_assistant.run("Tell me about AI")

ADK Example
~~~~~~~~~

.. code-block:: python

   from contexa_sdk.core.tool import ContexaTool
   from contexa_sdk.core.model import ContexaModel
   from contexa_sdk.core.agent import ContexaAgent
   from contexa_sdk.adapters.google import adk_tool, adk_model, adk_agent

   # Define a tool
   @ContexaTool.register(
       name="search",
       description="Search for information"
   )
   async def search(query: str) -> str:
       return f"Results for {query}"

   # Create a model and agent
   model = ContexaModel(provider="google", model_name="gemini-pro")
   agent = ContexaAgent(name="Assistant", model=model, tools=[search])

   # Convert to Google ADK
   adk_assistant = adk_agent(agent)
   result = await adk_assistant.run("Tell me about AI")

Installation
-----------

.. code-block:: bash

   # Install GenAI support
   pip install contexa-sdk[google-genai]

   # Install ADK support
   pip install contexa-sdk[google-adk]

   # Install both
   pip install contexa-sdk[google] 