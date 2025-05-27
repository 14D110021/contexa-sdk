"""CLI command for checking version information and compatibility.

This module provides a command-line interface for checking version information
for the Contexa SDK and its adapters, as well as compatibility with installed
frameworks.
"""

import sys
import argparse
from typing import Dict, List, Optional

from contexa_sdk import version


def print_sdk_version():
    """Print the SDK version information."""
    sdk_version = version.get_version()
    print(f"\nContexa SDK Version: {sdk_version}")


def print_adapter_versions():
    """Print version information for all adapters."""
    print("\nAdapter Versions:")
    
    adapters = [
        "base", 
        "langchain", 
        "crewai", 
        "openai", 
        "google.genai", 
        "google.adk"
    ]
    
    for adapter in adapters:
        adapter_version = version.get_adapter_version(adapter)
        if adapter_version:
            print(f"  - {adapter:<15}: {adapter_version}")
        else:
            print(f"  - {adapter:<15}: Not available")


def check_framework_compatibility():
    """Check compatibility with installed frameworks."""
    print("\nFramework Compatibility:")
    
    dependencies = version.check_all_dependencies()
    
    for framework, info in dependencies.items():
        installed = info["installed"]
        framework_version = info["version"]
        compatible = info["compatible"]
        min_version = info["min_version"]
        max_version = info["max_version"] or "None (no upper limit)"
        
        if installed:
            status = "Compatible" if compatible else "Incompatible"
            print(f"  - {framework:<15}: {framework_version} - {status}")
            print(f"    Min required: {min_version}, Max tested: {max_version}")
        else:
            print(f"  - {framework:<15}: Not installed")
            print(f"    Min required: {min_version}, Max tested: {max_version}")


def check_feature_support():
    """Check feature support for installed frameworks."""
    print("\nFeature Support:")
    
    feature_checks = [
        ("langchain", ["agent", "tool", "handoff"]),
        ("crewai", ["agent", "tool", "handoff"]),
        ("openai", ["agent", "tool", "assistants"]),
        ("google-genai", ["model", "tool", "streaming"]),
        ("google-adk", ["agent", "tool", "reasoning"])
    ]
    
    for framework, features in feature_checks:
        framework_version = version.get_framework_version(framework)
        
        if framework_version:
            print(f"  - {framework} {framework_version}:")
            for feature in features:
                min_version = version.get_feature_version(framework, feature)
                supported = version.check_feature_compatibility(
                    framework, framework_version, feature
                )
                status = "Supported" if supported else "Not supported"
                print(f"    - {feature:<10}: {status} (requires {min_version}+)")
        else:
            print(f"  - {framework}: Not installed")


def main():
    """Run the version check CLI command."""
    parser = argparse.ArgumentParser(
        description="Contexa SDK Version and Compatibility Check"
    )
    parser.add_argument(
        "--full", "-f", 
        action="store_true",
        help="Show full compatibility information"
    )
    parser.add_argument(
        "--adapters", "-a", 
        action="store_true",
        help="Show adapter versions"
    )
    parser.add_argument(
        "--compatibility", "-c", 
        action="store_true",
        help="Check framework compatibility"
    )
    parser.add_argument(
        "--features", 
        action="store_true",
        help="Check feature support"
    )
    
    args = parser.parse_args()
    
    # If no specific flags are provided, show all information
    show_all = not (args.adapters or args.compatibility or args.features)
    
    # Print SDK version
    print_sdk_version()
    
    # Print adapter versions if requested
    if args.adapters or args.full or show_all:
        print_adapter_versions()
    
    # Check framework compatibility if requested
    if args.compatibility or args.full or show_all:
        check_framework_compatibility()
    
    # Check feature support if requested
    if args.features or args.full:
        check_feature_support()
    
    print("\nFor more information, see docs/versioning_strategy.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 