Contexa SDK API Reference
======================

Welcome to the Contexa SDK API Reference documentation. This section provides detailed information about the classes, functions, and modules that make up the Contexa SDK.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   core
   adapters/index
   runtime
   observability
   deployment

Core Components
--------------

The core components provide the fundamental building blocks of the Contexa SDK:

- :doc:`core`: Core abstractions like tools, models, agents, and prompts

Framework Adapters
-----------------

The framework adapters allow Contexa components to be used with different agent frameworks:

- :doc:`adapters/index`: Overview of all framework adapters
- :doc:`adapters/langchain`: LangChain adapter
- :doc:`adapters/crewai`: CrewAI adapter
- :doc:`adapters/openai`: OpenAI Agents SDK adapter
- :doc:`adapters/google`: Google adapters (GenAI and ADK)

Runtime
-------

The runtime components handle the execution and lifecycle of agents:

- :doc:`runtime`: Agent execution, state management, and health monitoring

Observability
------------

The observability components provide insights into agent operations:

- :doc:`observability`: Logging, metrics, and tracing

Deployment
---------

The deployment components handle packaging and deploying agents:

- :doc:`deployment`: Containerization and service deployment

Indices and Tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 