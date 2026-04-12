# LLM System Improvements

## Overview

The KMP Migration Framework has been enhanced with a robust LLM invocation and prompt management system that provides:

- **Multi-provider support** (Ollama, Dashscope/Qwen, OpenAI, Anthropic)
- **Prompt templating** with variable substitution
- **Prompt optimization** and token management
- **Retry logic** and error handling
- **Response parsing** and validation
- **A/B testing** for prompt optimization

## New Files

| File | Size | Purpose |
|------|------|---------|
| `llm/invoker.py` | 13KB | Unified LLM provider interface |
| `llm/prompts.py` | 19KB | Prompt template management |
| `llm/__init__.py` | 1KB | Package exports |
| `LLM_IMPROVEMENTS.md` | This file | Documentation |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Code                             │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │    LLMInvoker           │
        │  - Multi-provider       │
        │  - Retry logic          │
        │  - Error handling       │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   PromptManager         │
        │  - Templates            │
        │  - Optimization         │
        │  - A/B testing          │
        └────────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌──────▼──────┐   ┌─────▼────┐
│Ollama │    │  Dashscope  │   │  OpenAI  │
│(local)│    │  (Qwen)     │   │          │
└───────┘    └─────────────┘   └──────────┘
```

## Usage Examples

### Basic Usage

```python
from llm import LLMInvoker, PromptManager

# Initialize
invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')
prompts = PromptManager()

# Use built-in template
response = prompts.invoke(
    'code_migration',
    invoker,
    file_path='MainActivity.kt',
    source_code=code,
    target_module='shared/src/commonMain/kotlin'
)

print(response.content)
```

### Multi-Provider Setup

```python
from llm import LLMInvoker, LLMConfig, LLMProvider

# Ollama (local, free)
ollama = LLMInvoker(
    provider=LLMProvider.OLLAMA,
    model='qwen2.5-coder:7b',
    base_url='http://localhost:11434'
)

# Dashscope/Qwen (cloud, paid)
qwen = LLMInvoker(
    provider=LLMProvider.DASHSCOPE,
    model='qwen-max',
    api_key='sk-xxx'
)

# OpenAI (cloud, paid)
gpt = LLMInvoker(
    provider=LLMProvider.OPENAI,
    model='gpt-4',
    api_key='sk-xxx'
)
```

### Custom Prompts

```python
from llm import PromptTemplate, PromptManager

prompts = PromptManager()

# Create custom template
template = PromptTemplate(
    id='kmp_review',
    name='KMP Code Review',
    description='Review KMP code for best practices',
    template='''Review this KMP code:

```kotlin
{{source_code}}
```

Provide feedback on:
1. KMP best practices
2. Platform separation
3. Code quality

Score: 1-10''',
    tags=['review', 'kmp', 'quality']
)

prompts.save_template(template)

# Use custom template
result = prompts.render('kmp_review', source_code=my_code)
print(result.rendered_prompt)
```

### Prompt Optimization

```python
from llm import PromptManager

prompts = PromptManager()

# Optimize long prompt
long_prompt = "..."  # 10000+ chars
optimized = prompts.optimize_prompt(long_prompt, max_tokens=2000)
print(f"Reduced from {len(long_prompt)} to {len(optimized)} chars")

# A/B test templates
template_a = prompts.get('code_migration')
template_b = prompts.get('code_migration_v2')

test_cases = [
    {'file_path': 'test1.kt', 'source_code': '...'},
    {'file_path': 'test2.kt', 'source_code': '...'},
]

results = prompts.ab_test(template_a, template_b, test_cases, invoker)
print(f"Winner: Template {results['winner']}")
print(f"Score A: {results['template_a']['avg_score']}")
print(f"Score B: {results['template_b']['avg_score']}")
```

### Response Handling

```python
from llm import LLMInvoker

invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')

# JSON mode for structured output
response = invoker.invoke(
    "Return user data as JSON",
    json_mode=True
)

if response.error:
    print(f"Error: {response.error}")
else:
    data = json.loads(response.content)
    print(f"Tokens used: {response.tokens_used}")
    print(f"Latency: {response.latency_ms}ms")
```

## Built-in Templates

| Template ID | Purpose | Variables |
|-------------|---------|-----------|
| `code_migration` | Migrate Android to KMP | file_path, source_code, target_module |
| `code_review` | Review KMP code quality | file_path, source_code |
| `architecture_analysis` | Analyze project structure | project_structure, file_list |
| `dependency_mapping` | Map dependencies | dependencies |
| `test_generation` | Generate tests | source_code |
| `skill_improvement` | Improve skills | file_path, original_code, migrated_code, feedback |

## Configuration

### Environment Variables

```bash
# Ollama
export OLLAMA_HOST=localhost:11434

# Dashscope
export DASHSCOPE_API_KEY=sk-xxx

# OpenAI
export OPENAI_API_KEY=sk-xxx

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-xxx
```

### Advanced Config

```python
from llm import LLMConfig, LLMProvider

config = LLMConfig(
    provider=LLMProvider.OLLAMA,
    model='qwen2.5-coder:7b',
    base_url='http://localhost:11434',
    temperature=0.3,      # Lower = more deterministic
    max_tokens=8192,       # Max output tokens
    timeout_seconds=120,   # Request timeout
    retry_count=3,         # Retry on failure
    retry_delay_seconds=2  # Delay between retries
)

invoker = LLMInvoker(config=config)
```

## Migration Guide

### Old Code (deprecated)

```python
# Old way - direct delegate_task
generated_code = delegate_task(goal=prompt)
```

### New Code (recommended)

```python
from llm import LLMInvoker, PromptManager

invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')
prompts = PromptManager()

# Use template
response = prompts.invoke('code_migration', invoker,
    file_path=file_path,
    source_code=content,
    target_module='shared/src/commonMain/kotlin'
)
generated_code = response.content
```

## Performance

| Metric | Value |
|--------|-------|
| Template rendering | <1ms |
| LLM invocation (local) | 500-2000ms |
| LLM invocation (cloud) | 1000-5000ms |
| Retry overhead | 2-6 seconds |
| Token estimation accuracy | ~90% |

## Error Handling

```python
from llm import LLMInvoker

invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')

response = invoker.invoke("Your prompt")

if response.error:
    # Handle error gracefully
    print(f"LLM failed: {response.error}")
    # Fallback to mock/default behavior
    generated_code = "// Fallback code"
else:
    # Success
    generated_code = response.content
    print(f"Success in {response.latency_ms}ms")
```

## Best Practices

1. **Use templates** for consistent prompting
2. **Enable JSON mode** for structured output
3. **Set appropriate temperature** (0.3 for code, 0.7 for creative)
4. **Implement retries** for production use
5. **Monitor token usage** to avoid limits
6. **Cache responses** for repeated prompts
7. **A/B test templates** for optimization

## Future Enhancements

- [ ] Response caching layer
- [ ] Streaming support for long responses
- [ ] Multi-modal support (images + text)
- [ ] Prompt versioning and rollback
- [ ] Usage analytics and cost tracking
- [ ] Batch processing for multiple files

---

*LLM System v1.0 - KMP Migration Framework*
