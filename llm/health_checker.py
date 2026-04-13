"""
LLM Health Checker

Checks if LLM providers are available and working before running migration.

Usage:
    from llm.health_checker import check_llm_health, LLMHealthStatus
    
    # Check all providers
    status = check_llm_health()
    
    # Check specific provider
    status = check_llm_health(provider='dashscope')
    
    # Check before migration
    if not status.is_healthy:
        print("LLM not available, using mock mode")
"""

import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMHealthStatus(Enum):
    """LLM health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"
    TIMEOUT = "timeout"
    AUTH_ERROR = "auth_error"


@dataclass
class ProviderHealth:
    """Health status of a single provider."""
    provider: str
    model: str
    status: LLMHealthStatus
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    configured: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'provider': self.provider,
            'model': self.model,
            'status': self.status.value,
            'latency_ms': self.latency_ms,
            'error_message': self.error_message,
            'configured': self.configured
        }


@dataclass
class HealthCheckResult:
    """Overall health check result."""
    timestamp: float
    providers: List[ProviderHealth]
    recommended_provider: Optional[str] = None
    recommended_model: Optional[str] = None
    is_healthy: bool = False
    message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'providers': [p.to_dict() for p in self.providers],
            'recommended_provider': self.recommended_provider,
            'recommended_model': self.recommended_model,
            'is_healthy': self.is_healthy,
            'message': self.message
        }


class LLMHealthChecker:
    """Check LLM provider health."""
    
    def __init__(self):
        self.providers = {
            'ollama': {
                'default_model': 'qwen2.5-coder:7b',
                'default_url': 'http://localhost:11434',
                'env_var': 'OLLAMA_HOST'
            },
            'dashscope': {
                'default_model': 'qwen-turbo',
                'env_var': 'DASHSCOPE_API_KEY'
            },
            'openai': {
                'default_model': 'gpt-3.5-turbo',
                'env_var': 'OPENAI_API_KEY'
            },
            'anthropic': {
                'default_model': 'claude-3-haiku-20240307',
                'env_var': 'ANTHROPIC_API_KEY'
            }
        }
    
    def check_all(self, timeout_seconds: int = 10) -> HealthCheckResult:
        """Check health of all configured providers."""
        logger.info("Starting LLM health check...")
        
        providers_health = []
        healthy_providers = []
        
        for provider_name in self.providers.keys():
            health = self._check_provider(provider_name, timeout_seconds)
            providers_health.append(health)
            
            if health.status == LLMHealthStatus.HEALTHY:
                healthy_providers.append((provider_name, health.model, health.latency_ms))
        
        # Sort by latency (fastest first)
        healthy_providers.sort(key=lambda x: x[2] if x[2] else float('inf'))
        
        # Determine recommended provider
        recommended = None
        recommended_model = None
        if healthy_providers:
            recommended = healthy_providers[0][0]
            recommended_model = healthy_providers[0][1]
        
        # Overall health
        is_healthy = len(healthy_providers) > 0
        
        # Message
        if is_healthy:
            message = f"Found {len(healthy_providers)} healthy provider(s). Recommended: {recommended}"
        else:
            message = "No healthy LLM providers found. Will use mock mode."
        
        return HealthCheckResult(
            timestamp=time.time(),
            providers=providers_health,
            recommended_provider=recommended,
            recommended_model=recommended_model,
            is_healthy=is_healthy,
            message=message
        )
    
    def _check_provider(self, provider_name: str, timeout_seconds: int) -> ProviderHealth:
        """Check health of a single provider."""
        logger.debug(f"Checking provider: {provider_name}")
        
        provider_config = self.providers[provider_name]
        default_model = provider_config['default_model']
        
        # Check if configured
        configured = self._is_configured(provider_name)
        
        if not configured:
            return ProviderHealth(
                provider=provider_name,
                model=default_model,
                status=LLMHealthStatus.NOT_CONFIGURED,
                configured=False,
                error_message=f"Environment variable {provider_config.get('env_var', 'N/A')} not set"
            )
        
        # Try to invoke
        start_time = time.time()
        try:
            if provider_name == 'ollama':
                return self._check_ollama(provider_config, timeout_seconds)
            elif provider_name == 'dashscope':
                return self._check_dashscope(provider_config, timeout_seconds)
            elif provider_name == 'openai':
                return self._check_openai(provider_config, timeout_seconds)
            elif provider_name == 'anthropic':
                return self._check_anthropic(provider_config, timeout_seconds)
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Determine error type
            if 'timeout' in error_msg.lower():
                status = LLMHealthStatus.TIMEOUT
            elif 'auth' in error_msg.lower() or '401' in error_msg.lower() or 'key' in error_msg.lower():
                status = LLMHealthStatus.AUTH_ERROR
            else:
                status = LLMHealthStatus.UNHEALTHY
            
            return ProviderHealth(
                provider=provider_name,
                model=default_model,
                status=status,
                latency_ms=latency_ms,
                configured=True,
                error_message=error_msg
            )
    
    def _is_configured(self, provider_name: str) -> bool:
        """Check if provider is configured."""
        provider_config = self.providers[provider_name]
        env_var = provider_config.get('env_var')
        
        if not env_var:
            return True  # Ollama doesn't need API key
        
        return bool(os.environ.get(env_var))
    
    def _check_ollama(self, config: Dict, timeout_seconds: int) -> ProviderHealth:
        """Check Ollama health."""
        import requests
        
        base_url = os.environ.get('OLLAMA_HOST', config.get('default_url', 'http://localhost:11434'))
        model = config['default_model']
        
        start_time = time.time()
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=timeout_seconds)
            response.raise_for_status()
            
            # Check if model is available
            models_data = response.json()
            available_models = [m.get('name', '') for m in models_data.get('models', [])]
            
            # Try to use default model or any available model
            if not any(model in m for m in available_models):
                if available_models:
                    model = available_models[0]  # Use first available model
                else:
                    return ProviderHealth(
                        provider='ollama',
                        model=model,
                        status=LLMHealthStatus.UNHEALTHY,
                        configured=True,
                        error_message="No models available in Ollama"
                    )
            
            # Quick test invocation
            test_response = requests.post(
                f"{base_url}/api/generate",
                json={
                    'model': model,
                    'prompt': 'Reply OK',
                    'stream': False
                },
                timeout=timeout_seconds
            )
            test_response.raise_for_status()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ProviderHealth(
                provider='ollama',
                model=model,
                status=LLMHealthStatus.HEALTHY,
                latency_ms=latency_ms,
                configured=True
            )
            
        except requests.exceptions.ConnectionError:
            return ProviderHealth(
                provider='ollama',
                model=model,
                status=LLMHealthStatus.UNHEALTHY,
                configured=True,
                error_message="Ollama is not running. Start with: ollama serve"
            )
        except requests.exceptions.Timeout:
            return ProviderHealth(
                provider='ollama',
                model=model,
                status=LLMHealthStatus.TIMEOUT,
                configured=True,
                error_message=f"Ollama request timed out after {timeout_seconds}s"
            )
        except Exception as e:
            return ProviderHealth(
                provider='ollama',
                model=model,
                status=LLMHealthStatus.UNHEALTHY,
                configured=True,
                error_message=str(e)
            )
    
    def _check_dashscope(self, config: Dict, timeout_seconds: int) -> ProviderHealth:
        """Check Dashscope/Qwen health."""
        try:
            import dashscope
        except ImportError:
            return ProviderHealth(
                provider='dashscope',
                model=config['default_model'],
                status=LLMHealthStatus.UNHEALTHY,
                configured=True,
                error_message="dashscope package not installed. Run: pip install dashscope"
            )
        
        api_key = os.environ.get('DASHSCOPE_API_KEY')
        if not api_key:
            return ProviderHealth(
                provider='dashscope',
                model=config['default_model'],
                status=LLMHealthStatus.NOT_CONFIGURED,
                configured=False,
                error_message="DASHSCOPE_API_KEY not set"
            )
        
        dashscope.api_key = api_key
        model = config['default_model']
        
        start_time = time.time()
        
        try:
            response = dashscope.Generation.call(
                model=model,
                messages=[{'role': 'user', 'content': 'Reply OK'}],
                timeout=timeout_seconds
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return ProviderHealth(
                    provider='dashscope',
                    model=model,
                    status=LLMHealthStatus.HEALTHY,
                    latency_ms=latency_ms,
                    configured=True
                )
            else:
                return ProviderHealth(
                    provider='dashscope',
                    model=model,
                    status=LLMHealthStatus.AUTH_ERROR if response.status_code == 401 else LLMHealthStatus.UNHEALTHY,
                    latency_ms=latency_ms,
                    configured=True,
                    error_message=f"Dashscope error {response.status_code}: {response.message}"
                )
                
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderHealth(
                provider='dashscope',
                model=model,
                status=LLMHealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                configured=True,
                error_message=str(e)
            )
    
    def _check_openai(self, config: Dict, timeout_seconds: int) -> ProviderHealth:
        """Check OpenAI health."""
        try:
            from openai import OpenAI
        except ImportError:
            return ProviderHealth(
                provider='openai',
                model=config['default_model'],
                status=LLMHealthStatus.UNHEALTHY,
                configured=True,
                error_message="openai package not installed. Run: pip install openai"
            )
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return ProviderHealth(
                provider='openai',
                model=config['default_model'],
                status=LLMHealthStatus.NOT_CONFIGURED,
                configured=False,
                error_message="OPENAI_API_KEY not set"
            )
        
        client = OpenAI(api_key=api_key, timeout=timeout_seconds)
        model = config['default_model']
        
        start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': 'Reply OK'}],
                max_tokens=10
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ProviderHealth(
                provider='openai',
                model=model,
                status=LLMHealthStatus.HEALTHY,
                latency_ms=latency_ms,
                configured=True
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            if '401' in error_msg or 'api key' in error_msg.lower():
                status = LLMHealthStatus.AUTH_ERROR
            elif 'timeout' in error_msg.lower():
                status = LLMHealthStatus.TIMEOUT
            else:
                status = LLMHealthStatus.UNHEALTHY
            
            return ProviderHealth(
                provider='openai',
                model=model,
                status=status,
                latency_ms=latency_ms,
                configured=True,
                error_message=error_msg
            )
    
    def _check_anthropic(self, config: Dict, timeout_seconds: int) -> ProviderHealth:
        """Check Anthropic health."""
        try:
            import anthropic
        except ImportError:
            return ProviderHealth(
                provider='anthropic',
                model=config['default_model'],
                status=LLMHealthStatus.UNHEALTHY,
                configured=True,
                error_message="anthropic package not installed. Run: pip install anthropic"
            )
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return ProviderHealth(
                provider='anthropic',
                model=config['default_model'],
                status=LLMHealthStatus.NOT_CONFIGURED,
                configured=False,
                error_message="ANTHROPIC_API_KEY not set"
            )
        
        client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds)
        model = config['default_model']
        
        start_time = time.time()
        
        try:
            response = client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{'role': 'user', 'content': 'Reply OK'}]
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return ProviderHealth(
                provider='anthropic',
                model=model,
                status=LLMHealthStatus.HEALTHY,
                latency_ms=latency_ms,
                configured=True
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            if '401' in error_msg or 'api key' in error_msg.lower():
                status = LLMHealthStatus.AUTH_ERROR
            elif 'timeout' in error_msg.lower():
                status = LLMHealthStatus.TIMEOUT
            else:
                status = LLMHealthStatus.UNHEALTHY
            
            return ProviderHealth(
                provider='anthropic',
                model=model,
                status=status,
                latency_ms=latency_ms,
                configured=True,
                error_message=error_msg
            )
    
    def print_report(self, result: HealthCheckResult):
        """Print health check report."""
        print("\n" + "="*60)
        print("LLM HEALTH CHECK REPORT")
        print("="*60)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.timestamp))}")
        print(f"Overall Status: {'✓ HEALTHY' if result.is_healthy else '✗ UNHEALTHY'}")
        print(f"Message: {result.message}")
        print()
        
        print("PROVIDERS:")
        print("-"*60)
        
        for provider in result.providers:
            status_icon = {
                LLMHealthStatus.HEALTHY: '✓',
                LLMHealthStatus.UNHEALTHY: '✗',
                LLMHealthStatus.NOT_CONFIGURED: '○',
                LLMHealthStatus.TIMEOUT: '⏱',
                LLMHealthStatus.AUTH_ERROR: '🔑'
            }.get(provider.status, '?')
            
            print(f"\n{status_icon} {provider.provider.upper()} ({provider.model})")
            print(f"   Status: {provider.status.value}")
            print(f"   Configured: {'Yes' if provider.configured else 'No'}")
            
            if provider.latency_ms:
                print(f"   Latency: {provider.latency_ms}ms")
            
            if provider.error_message:
                print(f"   Error: {provider.error_message[:100]}")
        
        if result.recommended_provider:
            print("\n" + "-"*60)
            print(f"RECOMMENDED: {result.recommended_provider} ({result.recommended_model})")
            print("="*60)
        else:
            print("\n" + "-"*60)
            print("RECOMMENDATION: No LLM available. Using mock mode.")
            print("="*60)


def check_llm_health(timeout_seconds: int = 10, print_report: bool = True) -> HealthCheckResult:
    """
    Check LLM health and return result.
    
    Args:
        timeout_seconds: Timeout for each provider check
        print_report: Whether to print the report
    
    Returns:
        HealthCheckResult object
    """
    checker = LLMHealthChecker()
    result = checker.check_all(timeout_seconds)
    
    if print_report:
        checker.print_report(result)
    
    return result


def get_recommended_invoker(result: Optional[HealthCheckResult] = None):
    """
    Get recommended LLM invoker based on health check.
    
    Args:
        result: Health check result (will run check if not provided)
    
    Returns:
        LLMInvoker instance or None (for mock mode)
    """
    if result is None:
        result = check_llm_health(print_report=False)
    
    if not result.is_healthy:
        logger.info("No healthy LLM providers. Using mock mode.")
        return None
    
    try:
        from llm.invoker import LLMInvoker, LLMProvider
        
        provider_name = result.recommended_provider
        model = result.recommended_model
        
        if provider_name == 'ollama':
            return LLMInvoker(provider=LLMProvider.OLLAMA, model=model)
        elif provider_name == 'dashscope':
            return LLMInvoker(provider=LLMProvider.DASHSCOPE, model=model)
        elif provider_name == 'openai':
            return LLMInvoker(provider=LLMProvider.OPENAI, model=model)
        elif provider_name == 'anthropic':
            return LLMInvoker(provider=LLMProvider.ANTHROPIC, model=model)
        
    except Exception as e:
        logger.warning(f"Failed to create invoker: {e}. Using mock mode.")
        return None
    
    return None
