"""Version utilities for Contexa SDK.

This module provides utilities for checking version information and compatibility
for the Contexa SDK and its adapters. It supports version querying, comparison,
and framework compatibility checking.
"""

import re
import warnings
from typing import Dict, List, Optional, Tuple, Union, cast

# Import the version from the package
from contexa_sdk import __version__

# Framework compatibility information
# This should match with FRAMEWORK_COMPATIBILITY.md
FRAMEWORK_COMPATIBILITY = {
    "langchain": {
        "min_version": "0.1.0",
        "max_version": None,  # None means no upper limit
        "features": {
            "agent": "0.1.0",
            "tool": "0.1.0",
            "handoff": "0.1.0"
        }
    },
    "crewai": {
        "min_version": "0.110.0",
        "max_version": None,
        "features": {
            "agent": "0.110.0",
            "tool": "0.110.0",
            "handoff": "0.110.0"
        }
    },
    "openai": {
        "min_version": "1.2.0",
        "max_version": None,
        "features": {
            "agent": "1.2.0",
            "tool": "1.2.0",
            "assistants": "1.2.0"
        }
    },
    "google-genai": {
        "min_version": "0.3.0",
        "max_version": None,
        "features": {
            "model": "0.3.0",
            "tool": "0.3.0",
            "streaming": "0.3.0"
        }
    },
    "google-adk": {
        "min_version": "0.5.0",
        "max_version": None,
        "features": {
            "agent": "0.5.0",
            "tool": "0.5.0",
            "reasoning": "0.5.0"
        }
    }
}

# Dictionary to map adapter modules to their framework dependencies
ADAPTER_DEPENDENCIES = {
    "langchain": ["langchain"],
    "crewai": ["crewai"],
    "openai": ["openai"],
    "google.genai": ["google-genai"],
    "google.adk": ["google-adk"]
}


def get_version() -> str:
    """Get the current version of the Contexa SDK.
    
    Returns:
        The version string of the SDK.
    """
    return __version__


def get_adapter_version(adapter_name: str) -> Optional[str]:
    """Get the version of a specific adapter.
    
    Args:
        adapter_name: The name of the adapter to get the version for.
            Can be one of: 'langchain', 'crewai', 'openai', 'google.genai', 'google.adk'
            
    Returns:
        The version string of the adapter, or None if the adapter doesn't exist
        or doesn't have a version defined.
        
    Example:
        ```python
        # Get version of the LangChain adapter
        langchain_version = get_adapter_version('langchain')
        ```
    """
    try:
        if adapter_name == "langchain":
            from contexa_sdk.adapters.langchain import __adapter_version__
            return __adapter_version__
        elif adapter_name == "crewai":
            from contexa_sdk.adapters.crewai import __adapter_version__
            return __adapter_version__
        elif adapter_name == "openai":
            from contexa_sdk.adapters.openai import __adapter_version__
            return __adapter_version__
        elif adapter_name == "google.genai":
            from contexa_sdk.adapters.google.genai import __adapter_version__
            return __adapter_version__
        elif adapter_name == "google.adk":
            from contexa_sdk.adapters.google.adk import __adapter_version__
            return __adapter_version__
        else:
            return None
    except (ImportError, AttributeError):
        return None


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse a version string into a tuple of (major, minor, patch).
    
    Args:
        version_str: Version string in the format "X.Y.Z"
        
    Returns:
        A tuple of (major, minor, patch) version numbers
        
    Raises:
        ValueError: If the version string doesn't match the expected format
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
        
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
         
    Raises:
        ValueError: If either version string is invalid
    """
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)
    
    for v1, v2 in zip(v1_parts, v2_parts):
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
            
    return 0


def check_compatibility(framework_name: str, framework_version: str) -> bool:
    """Check if a framework version is compatible with Contexa SDK.
    
    Args:
        framework_name: Name of the framework (e.g., 'langchain', 'openai')
        framework_version: Version string of the framework
        
    Returns:
        True if compatible, False otherwise
        
    Example:
        ```python
        # Check if LangChain 0.2.0 is compatible
        is_compatible = check_compatibility('langchain', '0.2.0')
        ```
    """
    if framework_name not in FRAMEWORK_COMPATIBILITY:
        warnings.warn(
            f"Unknown framework: {framework_name}. Cannot verify compatibility.",
            UserWarning
        )
        return False
        
    compat_info = FRAMEWORK_COMPATIBILITY[framework_name]
    min_version = compat_info["min_version"]
    max_version = compat_info["max_version"]
    
    # Check minimum version
    if min_version and compare_versions(framework_version, min_version) < 0:
        warnings.warn(
            f"{framework_name} version {framework_version} is below the minimum "
            f"supported version {min_version}.",
            UserWarning
        )
        return False
        
    # Check maximum version (if specified)
    if max_version and compare_versions(framework_version, max_version) > 0:
        warnings.warn(
            f"{framework_name} version {framework_version} is above the maximum "
            f"tested version {max_version}. Some features may not work correctly.",
            UserWarning
        )
        return True  # Still return True, but with a warning
        
    return True


def get_feature_version(framework_name: str, feature_name: str) -> Optional[str]:
    """Get the minimum version required for a specific feature.
    
    Args:
        framework_name: Name of the framework
        feature_name: Name of the feature
        
    Returns:
        The minimum version string required for the feature, or None if
        the feature or framework is unknown
        
    Example:
        ```python
        # Get the minimum version for the 'handoff' feature in LangChain
        min_version = get_feature_version('langchain', 'handoff')
        ```
    """
    if framework_name not in FRAMEWORK_COMPATIBILITY:
        return None
        
    compat_info = FRAMEWORK_COMPATIBILITY[framework_name]
    features = compat_info.get("features", {})
    
    return features.get(feature_name)


def check_feature_compatibility(
    framework_name: str, 
    framework_version: str, 
    feature_name: str
) -> bool:
    """Check if a specific feature is supported in the given framework version.
    
    Args:
        framework_name: Name of the framework
        framework_version: Version string of the framework
        feature_name: Name of the feature to check
        
    Returns:
        True if the feature is supported, False otherwise
        
    Example:
        ```python
        # Check if the 'handoff' feature is supported in LangChain 0.2.0
        is_supported = check_feature_compatibility('langchain', '0.2.0', 'handoff')
        ```
    """
    feature_min_version = get_feature_version(framework_name, feature_name)
    
    if not feature_min_version:
        warnings.warn(
            f"Unknown feature '{feature_name}' for framework '{framework_name}'.",
            UserWarning
        )
        return False
        
    return compare_versions(framework_version, feature_min_version) >= 0


def get_framework_version(framework_name: str) -> Optional[str]:
    """Get the installed version of a framework.
    
    Args:
        framework_name: Name of the framework
        
    Returns:
        The version string of the installed framework, or None if not installed
        
    Example:
        ```python
        # Get the installed version of LangChain
        langchain_version = get_framework_version('langchain')
        ```
    """
    try:
        if framework_name == "langchain":
            import langchain
            return getattr(langchain, "__version__", None)
        elif framework_name == "crewai":
            import crewai
            return getattr(crewai, "__version__", None)
        elif framework_name == "openai":
            import openai
            return getattr(openai, "__version__", None)
        elif framework_name == "google-genai":
            import google.generativeai
            return getattr(google.generativeai, "__version__", None)
        elif framework_name == "google-adk":
            import google.adk
            return getattr(google.adk, "__version__", None)
        else:
            return None
    except ImportError:
        return None


def check_all_dependencies() -> Dict[str, Dict[str, Union[bool, str, None]]]:
    """Check compatibility for all framework dependencies.
    
    Returns:
        A dictionary with framework names as keys and compatibility information as values.
        Each value is a dictionary with keys:
        - 'installed': True if the framework is installed, False otherwise
        - 'version': The installed version, or None if not installed
        - 'compatible': True if compatible, False otherwise, None if not installed
        - 'min_version': The minimum supported version
        - 'max_version': The maximum tested version, or None if no upper limit
        
    Example:
        ```python
        # Check all dependencies
        dependencies = check_all_dependencies()
        for name, info in dependencies.items():
            if info['installed']:
                print(f"{name} {info['version']} is {'compatible' if info['compatible'] else 'incompatible'}")
            else:
                print(f"{name} is not installed")
        ```
    """
    results = {}
    
    for framework_name in FRAMEWORK_COMPATIBILITY:
        version = get_framework_version(framework_name)
        compat_info = FRAMEWORK_COMPATIBILITY[framework_name]
        
        result = {
            "installed": version is not None,
            "version": version,
            "compatible": None,
            "min_version": compat_info["min_version"],
            "max_version": compat_info["max_version"]
        }
        
        if version:
            result["compatible"] = check_compatibility(framework_name, version)
            
        results[framework_name] = cast(Dict[str, Union[bool, str, None]], result)
        
    return results


def get_adapter_dependencies(adapter_name: str) -> List[str]:
    """Get the dependencies for a specific adapter.
    
    Args:
        adapter_name: Name of the adapter
        
    Returns:
        A list of framework dependencies for the adapter
        
    Example:
        ```python
        # Get the dependencies for the Google GenAI adapter
        dependencies = get_adapter_dependencies('google.genai')
        ```
    """
    return ADAPTER_DEPENDENCIES.get(adapter_name, []) 