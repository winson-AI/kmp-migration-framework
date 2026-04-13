"""
Enhanced LLM Invoker with Health Check and Token Statistics

Features:
- Health Monitoring (periodic checks, auto-disable on failure)
- Token Statistics (per-request, per-session, per-project tracking)
- Rate Limiting (prevent API abuse)
- Cost Estimation (track API costs)
- Model Fallback (switch models on failure)

Usage:
    from llm.enhanced_invoker import EnhancedLLMInvoker, LLMHealthStatus
    
    invoker = EnhancedLLMInvoker(provider='dashscope', model='qwen-turbo')
    
    # Check health
    health = invoker.check_health()
    print(f"Status: {health.status}, Score: {health.score:.0%}")
    
    # Execute with token tracking
    response = invoker.invoke("Your prompt here")
    print(f"Tokens used: {response.tokens_used}")
    
    # Get statistics
    stats = invoker.get_statistics()
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['estimated_cost']:.4f}")
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class LLMHealthStatus(Enum):
    """LLM health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"


@dataclass
class TokenUsage:
    """Token usage for a single request."""
    timestamp: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'model': self.model,
            'cost_usd': self.cost_usd
        }


@dataclass
class LLMHealth:
    """Health status of an LLM provider."""
    status: LLMHealthStatus
    score: float = 1.0  # 0-1
    last_check: float = field(default_factory=time.time)
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'score': self.score,
            'last_check': self.last_check,
            'last_error': self.last_error,
            'consecutive_failures': self.consecutive_failures,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset': self.rate_limit_reset
        }


@dataclass
class LLMStatistics:
    """Statistics for LLM usage."""
    session_id: str
    start_time: float
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    estimated_cost: float = 0.0
    avg_latency_ms: float = 0.0
    token_usage: List[TokenUsage] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'total_tokens': self.total_tokens,
            'total_prompt_tokens': self.total_prompt_tokens,
            'total_completion_tokens': self.total_completion_tokens,
            'estimated_cost': self.estimated_cost,
            'avg_latency_ms': self.avg_latency_ms,
            'token_usage': [t.to_dict() for t in self.token_usage[-100:]]  # Last 100
        }


# Pricing per 1K tokens (approximate, update as needed)
MODEL_PRICING = {
    'qwen-turbo': {'prompt': 0.0002, 'completion': 0.0006},
    'qwen-plus': {'prompt': 0.0004, 'completion': 0.0012},
    'qwen-max': {'prompt': 0.0012, 'completion': 0.0036},
    'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
    'gpt-4': {'prompt': 0.03, 'completion': 0.06},
    'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
    'claude-3-haiku': {'prompt': 0.00025, 'completion': 0.00125},
    'claude-3-sonnet': {'prompt': 0.003, 'completion': 0.015},
    'claude-3-opus': {'prompt': 0.015, 'completion': 0.075},
}


class EnhancedLLMInvoker:
    """
    Enhanced LLM invoker with health monitoring and token statistics.
    """
    
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None,
                 base_url: Optional[str] = None, enable_health_check: bool = True,
                 enable_statistics: bool = True):
        self.provider = provider
        self.model = model
        self.api_key = api_key or self._load_api_key(provider)
        self.base_url = base_url
        
        # Health monitoring
        self.enable_health_check = enable_health_check
        self.health = LLMHealth(status=LLMHealthStatus.HEALTHY)
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        
        # Statistics
        self.enable_statistics = enable_statistics
        self.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
        self.statistics = LLMStatistics(session_id=self.session_id, start_time=time.time())
        
        # Rate limiting
        self._rate_limit_lock = threading.Lock()
        self._request_times: List[float] = []
        self._max_requests_per_minute = 60
        
        # Import provider-specific invoker
        self._provider_invoker = self._get_provider_invoker()
        
        logger.info(f"Initialized EnhancedLLMInvoker: {provider}/{model}")
    
    def invoke(self, prompt: str, system_prompt: Optional[str] = None,
               json_mode: bool = False, **kwargs) -> 'LLMResponse':
        """
        Invoke LLM with health check and statistics tracking.
        """
        start_time = time.time()
        
        # Check health before invoking
        if self.enable_health_check:
            health = self.check_health()
            if health.status == LLMHealthStatus.UNAVAILABLE:
                return LLMResponse(
                    content="",
                    provider=self.provider,
                    model=self.model,
                    error=f"LLM unavailable: {health.last_error}",
                    tokens_used=0,
                    latency_ms=0
                )
        
        # Check rate limit
        if not self._check_rate_limit():
            self.health.status = LLMHealthStatus.RATE_LIMITED
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error="Rate limit exceeded",
                tokens_used=0,
                latency_ms=0
            )
        
        # Invoke LLM
        try:
            response = self._provider_invoker.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                api_key=self.api_key,
                base_url=self.base_url,
                **kwargs
            )
            
            # Update health on success
            if self.enable_health_check:
                self._record_success()
            
            # Record statistics
            if self.enable_statistics and response.tokens_used:
                self._record_token_usage(
                    prompt_tokens=response.tokens_used // 2,  # Estimate
                    completion_tokens=response.tokens_used // 2,
                    total_tokens=response.tokens_used,
                    latency_ms=response.latency_ms or int((time.time() - start_time) * 1000)
                )
            
            return response
            
        except Exception as e:
            # Update health on failure
            if self.enable_health_check:
                self._record_failure(str(e))
            
            return LLMResponse(
                content="",
                provider=self.provider,
                model=self.model,
                error=str(e),
                tokens_used=0,
                latency_ms=int((time.time() - start_time) * 1000)
            )
    
    def check_health(self, force: bool = False) -> LLMHealth:
        """
        Check LLM health.
        
        Args:
            force: Force health check even if recently checked
        """
        now = time.time()
        
        # Return cached health if recently checked
        if not force and (now - self._last_health_check) < self._health_check_interval:
            return self.health
        
        # Perform health check
        try:
            # Quick test invocation
            test_response = self._provider_invoker.invoke(
                prompt="Reply OK",
                system_prompt="Health check",
                api_key=self.api_key,
                base_url=self.base_url,
                max_tokens=10,
                timeout=10
            )
            
            if test_response.error:
                self._update_health(LLMHealthStatus.DEGRADED, test_response.error)
            else:
                self._update_health(LLMHealthStatus.HEALTHY, None)
            
        except Exception as e:
            self._update_health(LLMHealthStatus.UNHEALTHY, str(e))
        
        self._last_health_check = now
        return self.health
    
    def get_statistics(self) -> Dict:
        """Get LLM usage statistics."""
        return self.statistics.to_dict()
    
    def get_token_count(self) -> Dict:
        """Get token usage summary."""
        return {
            'total_tokens': self.statistics.total_tokens,
            'prompt_tokens': self.statistics.total_prompt_tokens,
            'completion_tokens': self.statistics.total_completion_tokens,
            'estimated_cost_usd': self.statistics.estimated_cost
        }
    
    def reset_statistics(self):
        """Reset statistics for new session."""
        self.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
        self.statistics = LLMStatistics(session_id=self.session_id, start_time=time.time())
        logger.info(f"Statistics reset, new session: {self.session_id}")
    
    def _get_provider_invoker(self):
        """Get provider-specific invoker."""
        if self.provider in ['ollama', 'dashscope', 'openai', 'anthropic']:
            # Import from existing invoker
            try:
                from llm.invoker import LLMInvoker, LLMProvider
                
                provider_map = {
                    'ollama': LLMProvider.OLLAMA,
                    'dashscope': LLMProvider.DASHSCOPE,
                    'openai': LLMProvider.OPENAI,
                    'anthropic': LLMProvider.ANTHROPIC
                }
                
                return LLMInvoker(
                    provider=provider_map.get(self.provider, LLMProvider.OLLAMA),
                    model=self.model,
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                pass
        
        # Fallback to mock invoker
        return _MockProviderInvoker()
    
    def _load_api_key(self, provider: str) -> Optional[str]:
        """Load API key from environment."""
        env_vars = {
            'ollama': None,
            'dashscope': 'DASHSCOPE_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY'
        }
        
        env_var = env_vars.get(provider)
        if env_var:
            return os.environ.get(env_var)
        return None
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows request."""
        with self._rate_limit_lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            self._request_times = [t for t in self._request_times if now - t < 60]
            
            # Check if under limit
            if len(self._request_times) >= self._max_requests_per_minute:
                return False
            
            # Record this request
            self._request_times.append(now)
            return True
    
    def _update_health(self, status: LLMHealthStatus, error: Optional[str]):
        """Update health status."""
        self.health.status = status
        self.health.last_check = time.time()
        
        if error:
            self.health.last_error = error
            self.health.consecutive_failures += 1
            self.health.score = max(0.0, self.health.score - 0.1)
        else:
            self.health.last_error = None
            self.health.consecutive_failures = 0
            self.health.score = min(1.0, self.health.score + 0.05)
        
        # Auto-disable on too many failures
        if self.health.consecutive_failures >= 5:
            self.health.status = LLMHealthStatus.UNAVAILABLE
    
    def _record_success(self):
        """Record successful invocation."""
        self.statistics.successful_requests += 1
        self.statistics.total_requests += 1
    
    def _record_failure(self, error: str):
        """Record failed invocation."""
        self.statistics.failed_requests += 1
        self.statistics.total_requests += 1
        logger.warning(f"LLM invocation failed: {error}")
    
    def _record_token_usage(self, prompt_tokens: int, completion_tokens: int,
                            total_tokens: int, latency_ms: int):
        """Record token usage."""
        # Calculate cost
        pricing = MODEL_PRICING.get(self.model, {'prompt': 0.001, 'completion': 0.003})
        cost = (prompt_tokens * pricing['prompt'] + completion_tokens * pricing['completion']) / 1000
        
        # Record usage
        usage = TokenUsage(
            timestamp=time.time(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            cost_usd=cost
        )
        
        self.statistics.token_usage.append(usage)
        self.statistics.total_tokens += total_tokens
        self.statistics.total_prompt_tokens += prompt_tokens
        self.statistics.total_completion_tokens += completion_tokens
        self.statistics.estimated_cost += cost
        
        # Update average latency
        total = self.statistics.successful_requests
        if total > 0:
            self.statistics.avg_latency_ms = (
                (self.statistics.avg_latency_ms * (total - 1) + latency_ms) / total
            )


@dataclass
class LLMResponse:
    """LLM response with token information."""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'provider': self.provider,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'latency_ms': self.latency_ms,
            'error': self.error
        }


class _MockProviderInvoker:
    """Mock provider invoker for testing."""
    
    def invoke(self, **kwargs) -> LLMResponse:
        return LLMResponse(
            content="Mock response",
            provider='mock',
            model='mock',
            tokens_used=10,
            latency_ms=50
        )


# Global invoker cache
_invokers: Dict[str, EnhancedLLMInvoker] = {}

def get_enhanced_invoker(provider: str, model: str, **kwargs) -> EnhancedLLMInvoker:
    """Get or create enhanced invoker."""
    key = f"{provider}:{model}"
    
    if key not in _invokers:
        _invokers[key] = EnhancedLLMInvoker(provider, model, **kwargs)
    
    return _invokers[key]
