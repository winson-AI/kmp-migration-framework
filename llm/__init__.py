"""
LLM Package for KMP Migration Framework

Provides:
- LLMInvoker: Unified multi-provider LLM interface
- PromptManager: Template management and optimization
- Pre-configured templates for KMP migration tasks

Usage:
    from llm import LLMInvoker, PromptManager
    
    # Initialize
    invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')
    prompts = PromptManager()
    
    # Use built-in template
    result = prompts.invoke('code_migration', invoker,
        file_path='MainActivity.kt',
        source_code=code,
        target_module='shared/src/commonMain/kotlin'
    )
    
    print(result.content)
"""

from .invoker import LLMInvoker, LLMConfig, LLMProvider, LLMResponse
from .prompts import PromptManager, PromptTemplate, PromptResult

__all__ = [
    'LLMInvoker',
    'LLMConfig', 
    'LLMProvider',
    'LLMResponse',
    'PromptManager',
    'PromptTemplate',
    'PromptResult',
]

__version__ = '1.0.0'
