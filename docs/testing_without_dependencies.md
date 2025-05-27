# Testing Google Adapters Without Dependencies

This document explains how to test the Google adapters in the Contexa SDK without requiring the actual Google dependencies to be installed.

## Overview

The Contexa SDK provides two Google adapters:
1. Google GenAI adapter (`google-generativeai`)
2. Google ADK adapter (`google-adk`)

To facilitate testing without requiring these dependencies to be installed, we've implemented mock versions of the adapters that simulate their behavior.

## Mock Implementation Approach

### Mock Implementation Strategy

Our testing framework uses several strategies to mock the Google dependencies:

1. **Import Path Mocking**: We use `unittest.mock.patch` to intercept imports of Google libraries
2. **Mock Classes**: We create minimal mock versions of key Google classes
3. **Feature Simulation**: We simulate essential features needed for testing
4. **Behavior Verification**: We verify that our adapters call the expected functions with the right parameters

### Mock Implementation Code Location

The mock implementations are stored in:

- `tests/mocks/google_genai_mock.py`: Mock classes for Google GenAI
- `tests/mocks/google_adk_mock.py`: Mock classes for Google ADK

## Using the Mock Implementations

### In Test Classes

Here's how to use the mock implementations in your test classes:

```python
import unittest
from unittest.mock import patch, MagicMock

class TestGoogleGenAIAdapter(unittest.TestCase):
    @patch("google.generativeai", autospec=True)
    def test_genai_tool_conversion(self, mock_genai):
        # The mock_genai will be used instead of the actual library
        from contexa_sdk.adapters.google import genai_tool
        
        # Set up your mock behavior
        mock_genai.types.FunctionDeclaration = MagicMock
        
        # Test the adapter
        result = genai_tool(my_tool)
        
        # Assert expected behavior
        self.assertEqual(result.__name__, my_tool.name)
```

### For ADK Tests

```python
import unittest
from unittest.mock import patch, MagicMock

class TestGoogleADKAdapter(unittest.TestCase):
    @patch("google.adk", autospec=True)
    def test_adk_tool_conversion(self, mock_adk):
        # The mock_adk will be used instead of the actual library
        from contexa_sdk.adapters.google import adk_tool
        
        # Set up your mock behavior
        mock_adk.Tool = MagicMock
        
        # Test the adapter
        result = adk_tool(my_tool)
        
        # Assert expected behavior
        self.assertEqual(result.name, my_tool.name)
```

## Writing Tests that Work with Both Real and Mock Implementations

When writing tests, follow these principles to ensure they work with both real and mock implementations:

1. **Import Dependencies at Function Level**: Don't import Google dependencies at the module level
2. **Use Descriptive Assertions**: Assert behavior, not exact types
3. **Test for Interface Compatibility**: Test that the converted objects have the expected methods/properties
4. **Mock Key Functions**: Mock only the functions your test actually needs

## Example: Complete Test Function

```python
@patch("google.generativeai", autospec=True)
def test_genai_model_conversion(self, mock_genai):
    # Setup mock
    mock_genai.configure = MagicMock()
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Test with ContexaModel
    from contexa_sdk.core.model import ContexaModel
    from contexa_sdk.adapters.google import genai_model
    
    model = ContexaModel(
        provider="google", 
        model_name="gemini-pro",
        temperature=0.7
    )
    
    result = genai_model(model)
    
    # Verify behavior
    mock_genai.GenerativeModel.assert_called_once()
    call_args = mock_genai.GenerativeModel.call_args[1]
    self.assertEqual(call_args["model_name"], "gemini-pro")
    self.assertEqual(call_args["generation_config"]["temperature"], 0.7)
```

## Continuous Integration Considerations

In CI environments:

1. **Skip Real-Dependency Tests**: Use unittest's `@unittest.skipIf` decorator to skip tests that require real dependencies
2. **Verify Mocked Tests Run**: Ensure that tests with mocked dependencies always run
3. **Conditional Testing**: Configure tests to run with real dependencies when available

```python
import unittest
import importlib.util

has_genai = importlib.util.find_spec("google.generativeai") is not None

class TestGoogleAdapters(unittest.TestCase):
    @unittest.skipIf(not has_genai, "Google GenAI not installed")
    def test_with_real_genai(self):
        # This test only runs when the real library is available
        pass
        
    def test_with_mock_genai(self):
        # This test always runs, using the mock implementation
        with patch("google.generativeai", autospec=True):
            # Test code here
            pass
```

By following these guidelines, you can effectively test the Google adapters without requiring the actual dependencies to be installed. 