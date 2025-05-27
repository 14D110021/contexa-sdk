"""CLI module for Contexa SDK.

This module provides command-line utilities for working with the Contexa SDK,
including:

- Main CLI commands for project initialization, building, and deployment
- Version checking and compatibility tools
- Framework compatibility reporting

The CLI tools enable a complete workflow for Contexa agent development,
from project initialization through local testing, building, and deployment
to production environments.

Example usage:
    # Initialize a new project
    $ ctx init my_project
    
    # Build an agent
    $ ctx build
    
    # Check version compatibility
    $ python -m contexa_sdk.cli.version_check --full
"""

from contexa_sdk.cli import version_check

__all__ = ['version_check'] 