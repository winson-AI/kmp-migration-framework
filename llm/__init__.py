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
from .health_checker import (
    check_llm_health,
    get_recommended_invoker,
    LLMHealthChecker,
    LLMHealthStatus,
    ProviderHealth,
    HealthCheckResult
)
from .enhanced_invoker import (
    EnhancedLLMInvoker,
    LLMHealth,
    LLMStatistics,
    TokenUsage,
    get_enhanced_invoker,
    MODEL_PRICING
)

__all__ = [
    # Invoker
    'LLMInvoker',
    'LLMConfig', 
    'LLMProvider',
    'LLMResponse',
    'EnhancedLLMInvoker',
    'get_enhanced_invoker',
    
    # Health & Stats
    'LLMHealth',
    'LLMStatistics',
    'TokenUsage',
    'MODEL_PRICING',
    
    # Prompts
    'PromptManager',
    'PromptTemplate',
    'PromptResult',
    
    # Health Checker
    'check_llm_health',
    'get_recommended_invoker',
    'LLMHealthChecker',
    'LLMHealthStatus',
    'ProviderHealth',
    'HealthCheckResult',
]

__version__ = '2.0.0'
