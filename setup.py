from setuptools import setup, find_packages

setup(
    name="contexa_sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "httpx>=0.24.0",  # For MCP client
        "aiohttp>=3.8.0",  # For async HTTP
    ],
    extras_require={
        "langchain": [
            "langchain>=0.1.0",
            "langchain-community>=0.0.1",
        ],
        "crewai": [
            "crewai>=0.28.0",  # Use realistic version
        ],
        "openai": [
            "openai>=1.0.0",
            "openai-agents>=0.1.0",  # Real OpenAI Agents SDK
        ],
        "google-genai": [
            "google-generativeai>=0.3.0",
        ],
        "google": [
            "google-generativeai>=0.3.0",
        ],
        "viz": [
            "graphviz>=0.20.1",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "pydocstyle>=6.0.0",
            "safety>=2.0.0",
            "bandit>=1.7.0",
        ],
        "all": [
            "langchain>=0.1.0",
            "langchain-community>=0.0.1",
            "crewai>=0.28.0",
            "openai>=1.0.0",
            "openai-agents>=0.1.0",
            "google-generativeai>=0.3.0",
            "graphviz>=0.20.1",
            "httpx>=0.24.0",
            "aiohttp>=3.8.0",
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