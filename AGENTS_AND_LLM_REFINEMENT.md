# Agent & LLM Refinement - v3.1

## Overview

This refinement adds two critical improvements:

1. **Agent System**: Clear separation of Prompt, Tools, and Author
2. **Enhanced LLM Invoker**: Health monitoring and token statistics

---

## 1. Agent System - Separation of Concerns

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      AGENT                               │
├─────────────────────────────────────────────────────────┤
│  PROMPTS (What to say)                                  │
│  - Template files (.json)                               │
│  - Variable substitution                                │
│  - Version controlled                                   │
│  - Multi-language support                               │
│                                                         │
│  TOOLS (What can do)                                    │
│  - Tool registry integration                            │
│  - Fallback chains                                      │
│  - Capability-based selection                           │
│  - Health-aware                                         │
│                                                         │
│  AUTHOR (Who made it)                                   │
│  - Name, email, organization                            │
│  - Version tracking                                     │
│  - License information                                  │
│  - Creation/update timestamps                           │
└─────────────────────────────────────────────────────────┘
```

### Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Prompt Updates** | Code change required | Edit JSON file |
| **Tool Changes** | Hardcoded | Configuration |
| **Versioning** | None | Per-agent versioning |
| **Attribution** | None | Full author metadata |
| **Reusability** | Low | High (configurable) |

### Usage Example

```python
from agents.base import Agent, AgentConfig, AgentFactory
from llm import get_enhanced_invoker
from core import get_registry

# Setup
invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')
registry = get_registry()
factory = AgentFactory(tool_registry=registry, llm_invoker=invoker)

# Load agent from config
planner = factory.create_agent('planner')

# Execute
result = planner.execute(
    input_data={
        'spec_content': '...',
        'available_skills': '...'
    },
    prompt_id='default'  # or 'detailed'
)

# Get stats
stats = planner.get_stats()
print(f"Executions: {stats['total_executions']}")
print(f"Success rate: {stats['success_rate']:.0%}")
```

### Agent Configuration File

```json
{
  "id": "planner",
  "name": "KMP Migration Planner",
  "description": "Analyzes Android projects and creates migration plans",
  "prompts": {
    "default": {
      "id": "planner_default",
      "template": "You are an expert... {{variable}}",
      "variables": ["variable"]
    }
  },
  "tools": {
    "file_read": {
      "tool_id": "file_read",
      "capability": "file_read",
      "required": true
    }
  },
  "author": {
    "name": "KMP Team",
    "version": "1.0.0",
    "license": "MIT"
  }
}
```

---

## 2. Enhanced LLM Invoker

### Features

| Feature | Description |
|---------|-------------|
| **Health Monitoring** | Automatic health checks, auto-disable on failure |
| **Token Statistics** | Track tokens per request, session, project |
| **Cost Estimation** | Calculate API costs based on token usage |
| **Rate Limiting** | Prevent API abuse with request throttling |
| **Model Fallback** | Switch models on failure |

### Health Monitoring

```python
from llm import get_enhanced_invoker, LLMHealthStatus

invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')

# Check health
health = invoker.check_health()
print(f"Status: {health.status.value}")  # healthy, degraded, unhealthy
print(f"Score: {health.score:.0%}")       # 0-100%
print(f"Failures: {health.consecutive_failures}")

# Health is automatically updated on each invocation
# Auto-disables after 5 consecutive failures
```

### Token Statistics

```python
from llm import get_enhanced_invoker

invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')

# Execute with token tracking
response = invoker.invoke("Your prompt here")
print(f"Tokens used: {response.tokens_used}")

# Get statistics
stats = invoker.get_statistics()
print(f"Total requests: {stats['total_requests']}")
print(f"Successful: {stats['successful_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
print(f"Avg latency: {stats['avg_latency_ms']:.0f}ms")

# Get token breakdown
tokens = invoker.get_token_count()
print(f"Prompt tokens: {tokens['prompt_tokens']}")
print(f"Completion tokens: {tokens['completion_tokens']}")

# Reset for new session
invoker.reset_statistics()
```

### Cost Tracking

Built-in pricing for common models:

| Model | Prompt (per 1K) | Completion (per 1K) |
|-------|-----------------|---------------------|
| qwen-turbo | $0.0002 | $0.0006 |
| qwen-max | $0.0012 | $0.0036 |
| gpt-3.5-turbo | $0.0005 | $0.0015 |
| gpt-4 | $0.03 | $0.06 |
| claude-3-haiku | $0.00025 | $0.00125 |
| claude-3-opus | $0.015 | $0.075 |

```python
from llm import MODEL_PRICING

print(MODEL_PRICING['qwen-turbo'])
# {'prompt': 0.0002, 'completion': 0.0006}
```

### Rate Limiting

```python
from llm import EnhancedLLMInvoker

invoker = EnhancedLLMInvoker(
    provider='dashscope',
    model='qwen-turbo',
    enable_health_check=True,
    enable_statistics=True
)

# Automatically rate limits to 60 requests/minute
# Configurable via _max_requests_per_minute
```

---

## New Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `agents/base.py` | 400+ | Agent system with prompt/tools/author separation |
| `llm/enhanced_invoker.py` | 450+ | Enhanced LLM with health & statistics |
| `agents/planner.json` | 80 | Example agent configuration |
| `AGENTS_AND_LLM_REFINEMENT.md` | This file | Documentation |

**Total New Code: ~930 lines**

---

## Integration Examples

### Complete Example with Agent + Enhanced LLM

```python
from agents.base import AgentFactory
from llm import get_enhanced_invoker
from core import get_registry

# Initialize components
invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')
registry = get_registry()
factory = AgentFactory(tool_registry=registry, llm_invoker=invoker)

# Check LLM health before using
health = invoker.check_health()
if health.status.value != 'healthy':
    print(f"⚠️ LLM health: {health.status.value} ({health.score:.0%})")

# Load and execute agent
planner = factory.create_agent('planner')
result = planner.execute({
    'spec_content': '...',
    'available_skills': '...'
})

# Check results
if result['success']:
    print(f"✓ Agent executed successfully")
    print(f"  Output: {result['output'][:200]}...")
    print(f"  Tokens: {result['tokens_used']}")
    print(f"  Latency: {result['latency_ms']}ms")
else:
    print(f"✗ Agent failed: {result['error']}")

# Get statistics
agent_stats = planner.get_stats()
llm_stats = invoker.get_statistics()

print(f"\nAgent Stats:")
print(f"  Executions: {agent_stats['total_executions']}")
print(f"  Success rate: {agent_stats['success_rate']:.0%}")

print(f"\nLLM Stats:")
print(f"  Total tokens: {llm_stats['total_tokens']}")
print(f"  Estimated cost: ${llm_stats['estimated_cost']:.4f}")
```

### Multi-Agent Workflow

```python
from agents.base import AgentFactory

factory = AgentFactory(tool_registry=registry, llm_invoker=invoker)

# Load multiple agents
planner = factory.create_agent('planner')
generator = factory.create_agent('generator')
evaluator = factory.create_agent('evaluator')

# Execute in sequence
plan_result = planner.execute({'spec_content': '...'})
if plan_result['success']:
    gen_result = generator.execute({
        'plan': plan_result['output'],
        'source_code': '...'
    })
    if gen_result['success']:
        eval_result = evaluator.execute({
            'generated_code': gen_result['output']
        })

# Get combined statistics
total_tokens = (
    plan_result.get('tokens_used', 0) +
    gen_result.get('tokens_used', 0) +
    eval_result.get('tokens_used', 0)
)
print(f"Total tokens for workflow: {total_tokens}")
```

---

## Testing Results

### Agent System Test

```
✓ Agent configuration loaded
✓ Prompts rendered correctly
✓ Tools resolved from registry
✓ Execution history tracked
✓ Statistics accurate
```

### Enhanced LLM Test

```
✓ Health check works
✓ Token tracking accurate
✓ Cost estimation correct
✓ Rate limiting functional
✓ Statistics reset works
```

---

## Migration Guide

### For Existing Code

```python
# Old way (still works)
from llm import LLMInvoker
invoker = LLMInvoker(provider='dashscope', model='qwen-turbo')

# New way (with health & stats)
from llm import get_enhanced_invoker
invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')

# Use the same way
response = invoker.invoke("Your prompt")
print(f"Tokens: {response.tokens_used}")

# Plus new features
health = invoker.check_health()
stats = invoker.get_statistics()
```

### For New Code

```python
from agents.base import AgentFactory
from llm import get_enhanced_invoker
from core import get_registry

# Full setup with all features
invoker = get_enhanced_invoker('dashscope', 'qwen-turbo')
registry = get_registry()
factory = AgentFactory(tool_registry=registry, llm_invoker=invoker)

# Use agents
agent = factory.create_agent('planner')
result = agent.execute({'input': '...'})

# Monitor everything
print(f"LLM Health: {invoker.check_health().status.value}")
print(f"Agent Stats: {agent.get_stats()}")
print(f"Token Cost: ${invoker.get_statistics()['estimated_cost']:.4f}")
```

---

## Summary

### Before v3.1

| Feature | Status |
|---------|--------|
| Agent Prompts | Hardcoded in Python |
| Agent Tools | Hardcoded |
| Agent Versioning | None |
| LLM Health | Basic check only |
| Token Tracking | Per-request only |
| Cost Tracking | None |
| Rate Limiting | None |

### After v3.1

| Feature | Status |
|---------|--------|
| Agent Prompts | JSON config files |
| Agent Tools | Registry-based |
| Agent Versioning | Full metadata |
| LLM Health | Continuous monitoring |
| Token Tracking | Per-session + project |
| Cost Tracking | Real-time estimation |
| Rate Limiting | Automatic |

**Framework Version: 3.1.0**

---

*Agent & LLM Refinement v3.1 - Separation of Concerns + Enhanced Monitoring*
