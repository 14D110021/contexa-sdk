from setuptools import setup, find_packages

setup(
    name="contexa_sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
    ],
    extras_require={
        "langchain": [
            "langchain>=0.1.0",
            "langchain-openai>=0.0.1",
            "langgraph>=0.0.15",
        ],
        "crewai": [
            "crewai>=0.110.0",
        ],
        "openai": [
            "openai>=1.2.0",
            "openai-agents>=0.0.3",
        ],
        "google-genai": [
            "google-generativeai>=0.3.0",
        ],
        "google-adk": [
            "google-adk>=0.5.0",
        ],
        "google": [
            "google-generativeai>=0.3.0",
            "google-adk>=0.5.0",
        ],
        "viz": [
            "graphviz>=0.20.1",
        ],
        "all": [
            "langchain>=0.1.0",
            "langchain-openai>=0.0.1",
            "langgraph>=0.0.15",
            "crewai>=0.110.0",
            "openai>=1.2.0",
            "openai-agents>=0.0.3",
            "google-generativeai>=0.3.0",
            "google-adk>=0.5.0",
            "graphviz>=0.20.1",
        ],
    },
    python_requires=">=3.8",
    author="Rupesh Raj",
    author_email="contact@rupeshraj.dev",
    description="SDK for building context-aware multi-agent systems with framework interoperability",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rupeshrajdev/contexa_sdk",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 