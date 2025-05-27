Adapters
========

The adapters module provides converters between Contexa SDK core objects and various agent framework objects.

.. toctree::
   :maxdepth: 2
   :caption: Available Adapters:
   
   langchain
   crewai
   openai
   google

Overview
--------

Contexa SDK adapters allow tools, models, agents, and prompts defined with the SDK to be used in different agent frameworks.
Each adapter provides functions to convert between Contexa objects and the corresponding objects in the target framework.

Common Interface
---------------

All adapters implement a common interface:

- ``tool``: Convert a Contexa tool to a framework-specific tool
- ``model``: Convert a Contexa model to a framework-specific model
- ``agent``: Convert a Contexa agent to a framework-specific agent
- ``prompt``: Convert a Contexa prompt to a framework-specific prompt
- ``handoff``: Enable handoffs between agents in the framework

Google Adapters
--------------

The Google adapters are special because they provide two separate implementations:

1. ``genai_*`` functions for working with Google's Generative AI SDK (Gemini models)
2. ``adk_*`` functions for working with Google's Agent Development Kit

See :doc:`google` for detailed documentation about these adapters. 