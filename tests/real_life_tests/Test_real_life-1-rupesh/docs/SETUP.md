# Setup Instructions for Test_real_life-1-rupesh

## Overview

This document provides step-by-step instructions for setting up the test environment for the first real-life validation of the Contexa SDK.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: At least 4GB RAM available
- **Network**: Stable internet connection for API calls

### Required API Keys
- **OpenAI API Key**: For GPT-4.1 model access
- **MCP Server Access**: Endpoint URL provided
- **Optional**: Context7 and Exa API keys (if separate authentication required)

## Installation Steps

### 1. Environment Setup

```bash
# Navigate to the test directory
cd tests/real_life_tests/Test_real_life-1-rupesh

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify Contexa SDK installation
python -c "import contexa_sdk; print(f'Contexa SDK version: {contexa_sdk.__version__}')"

# Verify OpenAI installation
python -c "import openai; print(f'OpenAI version: {openai.__version__}')"
```

### 3. Configure API Keys

```bash
# Copy the template configuration file
cp config/api_keys.env.template config/api_keys.env

# Edit the configuration file with your actual API keys
# Use your preferred text editor
nano config/api_keys.env
```

**Required Configuration:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4.1

# MCP Server Configuration  
MCP_SERVER_URL=https://api.toolrouter.ai/u/c8b0ceae-6a25-445d-a8fe-4cf4327cc70a/sse
MCP_SERVER_AUTH_TOKEN=your-mcp-auth-token-if-required

# Test Configuration
TEST_ENVIRONMENT=development
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_MONITORING=true
```

### 4. Verify Installation

```bash
# Test tool imports
python -c "
from src.tools.context7_tool import Context7Tool
from src.tools.exa_search_tool import ExaSearchTool
print('✅ Tools imported successfully')
"

# Test Contexa SDK imports
python -c "
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
print('✅ Contexa SDK imported successfully')
"
```

### 5. Run Basic Tests

```bash
# Test Context7 tool
python src/tools/context7_tool.py

# Test Exa search tool
python src/tools/exa_search_tool.py

# Test OpenAI agent (requires API key)
python src/openai_agent/codemaster_openai.py

# Test Contexa agent (requires API key)
python src/contexa_agent/codemaster_contexa.py
```

## Configuration Details

### Environment Variables

The test uses the following environment variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4.1 | Yes | None |
| `OPENAI_MODEL` | Model to use | No | gpt-4.1 |
| `MCP_SERVER_URL` | MCP server endpoint | Yes | Provided URL |
| `MCP_SERVER_AUTH_TOKEN` | MCP authentication token | No | None |
| `TEST_ENVIRONMENT` | Environment identifier | No | development |
| `LOG_LEVEL` | Logging level | No | INFO |
| `ENABLE_PERFORMANCE_MONITORING` | Enable metrics collection | No | true |

### MCP Configuration

The MCP server configuration is defined in `config/mcp_config.json`:

```json
{
  "mcp_server": {
    "url": "https://api.toolrouter.ai/u/c8b0ceae-6a25-445d-a8fe-4cf4327cc70a/sse",
    "protocol": "sse",
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1.0
  },
  "tools": {
    "context7": {
      "name": "context7_docs",
      "description": "Retrieve up-to-date documentation for libraries and frameworks",
      "enabled": true,
      "max_tokens": 5000,
      "cache_ttl": 3600
    },
    "exa_search": {
      "name": "exa_web_search", 
      "description": "Search the web for technical content and solutions",
      "enabled": true,
      "max_results": 5,
      "cache_ttl": 1800
    }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If you get import errors, ensure the virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### 2. API Key Issues
```bash
# Verify API key is loaded
python -c "
import os
from dotenv import load_dotenv
load_dotenv('config/api_keys.env')
print('OpenAI Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'Not found')
"
```

#### 3. Network Connectivity
```bash
# Test MCP server connectivity
curl -I https://api.toolrouter.ai/u/c8b0ceae-6a25-445d-a8fe-4cf4327cc70a/sse

# Test OpenAI API connectivity
python -c "
import openai
import os
from dotenv import load_dotenv
load_dotenv('config/api_keys.env')
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
try:
    models = client.models.list()
    print('✅ OpenAI API connection successful')
except Exception as e:
    print(f'❌ OpenAI API connection failed: {e}')
"
```

#### 4. Permission Issues
```bash
# Ensure proper file permissions
chmod +x src/tools/*.py
chmod +x src/openai_agent/*.py
chmod +x src/contexa_agent/*.py
```

### Performance Optimization

#### Memory Usage
```bash
# Monitor memory usage during tests
pip install psutil
python -c "
import psutil
print(f'Available memory: {psutil.virtual_memory().available / 1024**3:.2f} GB')
print(f'CPU count: {psutil.cpu_count()}')
"
```

#### Logging Configuration
```bash
# Adjust logging level for debugging
export LOG_LEVEL=DEBUG

# Or modify in config/api_keys.env
echo "LOG_LEVEL=DEBUG" >> config/api_keys.env
```

## Validation Checklist

Before running the full test suite, ensure:

- [ ] Virtual environment is activated
- [ ] All dependencies are installed
- [ ] API keys are configured correctly
- [ ] MCP server is accessible
- [ ] Basic tool tests pass
- [ ] OpenAI API connection works
- [ ] Contexa SDK imports successfully
- [ ] Log files are writable
- [ ] Performance monitoring is enabled

## Next Steps

Once setup is complete:

1. **Run Unit Tests**: `python -m pytest tests/unit/`
2. **Run Integration Tests**: `python -m pytest tests/integration/`
3. **Execute Test Scenarios**: `python tests/scenarios/basic_usage.py`
4. **Review Results**: Check `docs/RESULTS.md` for analysis

## Support

If you encounter issues during setup:

1. Check the troubleshooting section above
2. Review the main Contexa SDK documentation
3. Verify all prerequisites are met
4. Check the GitHub issues for similar problems

## Security Notes

- **Never commit `config/api_keys.env`** to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage and costs
- Use least-privilege access principles

---

**Setup Complete!** 🎉

You're now ready to run the Test_real_life-1-rupesh validation suite. 