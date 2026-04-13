# LLM Health Checker

Automatically checks if LLM providers are available before running migration.

## Features

- ✓ Checks 4 providers (Ollama, Dashscope, OpenAI, Anthropic)
- ✓ Measures latency for each provider
- ✓ Recommends fastest healthy provider
- ✓ Auto-configures invoker based on health check
- ✓ Graceful fallback to mock mode

## Usage

### Check All Providers

```python
from llm import check_llm_health

result = check_llm_health()
```

### Check Specific Provider

```python
from llm import LLMHealthChecker

checker = LLMHealthChecker()
result = checker.check_all()
```

### Get Recommended Invoker

```python
from llm import get_recommended_invoker

invoker = get_recommended_invoker()
# Returns None if no LLM available (use mock mode)
```

## Health Status

| Status | Icon | Meaning |
|--------|------|---------|
| `healthy` | ✓ | Provider is working |
| `unhealthy` | ✗ | Provider has errors |
| `not_configured` | ○ | API key not set |
| `timeout` | ⏱ | Request timed out |
| `auth_error` | 🔑 | Invalid API key |

## Example Output

```
============================================================
LLM HEALTH CHECK REPORT
============================================================
Timestamp: 2026-04-13 20:54:18
Overall Status: ✓ HEALTHY
Message: Found 2 healthy provider(s). Recommended: ollama

PROVIDERS:
------------------------------------------------------------

✓ OLLAMA (qwen2.5-coder:7b)
   Status: healthy
   Configured: Yes
   Latency: 245ms

✓ DASHSCOPE (qwen-turbo)
   Status: healthy
   Configured: Yes
   Latency: 892ms

○ OPENAI (gpt-3.5-turbo)
   Status: not_configured
   Configured: No
   Error: OPENAI_API_KEY not set

------------------------------------------------------------
RECOMMENDED: ollama (qwen2.5-coder:7b)
============================================================
```

## Integration with Pipeline

The health checker runs automatically before migration:

```python
from orchestrator import run_orchestrator

# Health check runs automatically
run_orchestrator('/path/to/project')

# Disable health check
run_orchestrator('/path/to/project', check_health=False)
```

## Configure Providers

### Ollama (Local, Free)

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5-coder:7b

# Start server
ollama serve

# No API key needed!
```

### Dashscope/Qwen (Cloud, Paid)

```bash
# Get API key from https://dashscope.aliyun.com/
export DASHSCOPE_API_KEY="sk-your-key-here"

# Install package
pip install dashscope
```

### OpenAI (Cloud, Paid)

```bash
# Get API key from https://platform.openai.com/
export OPENAI_API_KEY="sk-your-key-here"

# Install package
pip install openai
```

### Anthropic (Cloud, Paid)

```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Install package
pip install anthropic
```

## Health Check Timeout

Default timeout is 10 seconds per provider. Customize:

```python
result = check_llm_health(timeout_seconds=5)  # 5 seconds
```

## Programmatic Access

```python
from llm import LLMHealthChecker, LLMHealthStatus

checker = LLMHealthChecker()
result = checker.check_all()

# Check overall health
if result.is_healthy:
    print(f"Recommended: {result.recommended_provider}")
else:
    print("No LLM available, using mock mode")

# Check individual providers
for provider in result.providers:
    if provider.status == LLMHealthStatus.HEALTHY:
        print(f"✓ {provider.provider}: {provider.latency_ms}ms")
```

## Mock Mode

When no LLM is available, the framework uses **mock mode**:

- ✓ Migration still works
- ✓ All features available
- ⚠ Code is not actually migrated (placeholder)
- ⚠ Quality scores are simulated

Mock mode is useful for:
- Testing the pipeline
- Development without API costs
- Offline work

---

*LLM Health Checker v1.0 - Automatic LLM Detection*
