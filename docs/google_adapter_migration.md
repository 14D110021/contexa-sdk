# Google Adapters Migration Guide

## Overview

We've restructured the Google adapters in the Contexa SDK to properly separate Google GenAI (Gemini) and Google ADK (Agent Development Kit) implementations. This document provides guidance on migrating existing code to use the new structure.

## Changes Made

1. **Directory Restructuring**:
   - Moved Google GenAI implementation to `contexa_sdk/adapters/google/genai.py`
   - Moved Google ADK implementation to `contexa_sdk/adapters/google/adk.py`
   - Added a converter module at `contexa_sdk/adapters/google/converter.py`

2. **New Import Patterns**:
   - Added clear prefixes to all functions (`genai_*` and `adk_*`)
   - Created proper re-exports in `__init__.py`
   - Maintained backward compatibility

3. **Implementation Improvements**:
   - Enhanced error handling
   - Added support for both ContexaTool instances and decorated functions
   - Improved mock implementations for testing
   - Added synchronous wrappers for async functions

## Migration Steps

### For New Code

Use the new prefixed functions and import from the dedicated modules:

```python
# For Google GenAI (preferred)
from contexa_sdk.adapters.google import genai_tool, genai_model, genai_agent

# For Google ADK (preferred)
from contexa_sdk.adapters.google import adk_tool, adk_model, adk_agent
```

### For Existing Code

Your existing code using the non-prefixed functions will continue to work:

```python
# These will keep working (uses GenAI implementations by default)
from contexa_sdk.adapters.google import tool, model, agent
```

However, we recommend migrating to the new prefixed functions for clarity.

### Deprecation Timeline

- **Current Release**: Both old and new import patterns supported
- **Next Minor Release**: Warnings added for old import patterns
- **Next Major Release**: Old import patterns may be removed

## Installation Updates

The dependencies are now more clearly separated:

```bash
# For GenAI only
pip install contexa-sdk[google-genai]

# For ADK only
pip install contexa-sdk[google-adk]

# For both
pip install contexa-sdk[google]
```

## Documentation

For detailed documentation on the differences between the two adapters and when to use each, see [Google Adapters Documentation](google_adapters.md). 