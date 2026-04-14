"""
Real LLM Code Executor - Production-Ready Implementation

Actually calls LLM APIs for code generation (not mocked).
Supports: Ollama, Dashscope, OpenAI, Anthropic
Features: Cost tracking, retry logic, response validation
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "qwen2.5-coder:7b"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 120
    max_tokens: int = 4096
    temperature: float = 0.3
    track_cost: bool = True
    cost_limit_usd: float = 10.0
    
    def to_dict(self) -> Dict:
        return {
            'provider': self.provider.value,
            'model': self.model,
            'api_key': '***' if self.api_key else None,
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'track_cost': self.track_cost,
            'cost_limit_usd': self.cost_limit_usd
        }


@dataclass
class CodeGenerationResult:
    """Result from LLM code generation."""
    success: bool
    code: str
    original_file: str
    target_file: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'code': self.code[:200] + '...' if len(self.code) > 200 else self.code,
            'original_file': self.original_file,
            'target_file': self.target_file,
            'tokens_used': self.tokens_used,
            'cost_usd': self.cost_usd,
            'latency_ms': self.latency_ms,
            'error': self.error,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


# Pricing per 1K tokens (approximate, update as needed)
MODEL_PRICING = {
    'ollama': {'prompt': 0.0, 'completion': 0.0},
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


class LLMCodeExecutor:
    """
    Execute real LLM calls for code generation.
    
    Production-ready implementation with:
    - Real API calls to multiple providers
    - Cost tracking and limits
    - Retry logic with backoff
    - Response validation
    - Session statistics
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session_id = f"session_{int(time.time())}"
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.failed_requests = 0
        
        # Pricing for current model
        self.pricing = MODEL_PRICING.get(
            config.model,
            MODEL_PRICING.get('gpt-3.5-turbo')
        )
    
    def generate_code(self,
                     prompt: str,
                     system_prompt: str,
                     context: Optional[Dict] = None,
                     retry_count: int = 3) -> CodeGenerationResult:
        """
        Generate code using real LLM call with retry logic.
        
        Args:
            prompt: Main prompt for code generation
            system_prompt: System instructions
            context: Additional context (file info, skills, etc.)
            retry_count: Number of retries on failure
        
        Returns:
            CodeGenerationResult with generated code or error
        """
        last_error = None
        
        for attempt in range(retry_count + 1):
            if attempt > 0:
                # Exponential backoff
                backoff = min(2 ** attempt, 30)
                logger.info(f"Retry {attempt + 1}/{retry_count} after {backoff}s")
                time.sleep(backoff)
            
            try:
                result = self._generate_code_internal(prompt, system_prompt, context)
                
                if result.success:
                    # Track metrics
                    self.total_tokens += result.tokens_used
                    self.total_cost += result.cost_usd
                    self.request_count += 1
                    
                    logger.info(
                        f"Code generation success: {result.original_file}, "
                        f"tokens: {result.tokens_used}, "
                        f"cost: ${result.cost_usd:.4f}, "
                        f"latency: {result.latency_ms}ms"
                    )
                
                return result
                
            except Exception as e:
                last_error = str(e)
                self.failed_requests += 1
                logger.error(f"Code generation failed (attempt {attempt + 1}): {e}")
        
        # All retries failed
        return CodeGenerationResult(
            success=False,
            code="",
            original_file=context.get('file', 'unknown') if context else 'unknown',
            target_file="",
            error=f"All {retry_count + 1} attempts failed: {last_error}"
        )
    
    def _generate_code_internal(self,
                               prompt: str,
                               system_prompt: str,
                               context: Optional[Dict]) -> CodeGenerationResult:
        """Internal code generation without retry."""
        start_time = time.time()
        
        # Check cost limit
        if self.config.track_cost:
            remaining = self.config.cost_limit_usd - self.total_cost
            if remaining <= 0:
                return CodeGenerationResult(
                    success=False,
                    code="",
                    original_file=context.get('file', 'unknown') if context else 'unknown',
                    target_file="",
                    error=f"Cost limit exceeded: ${self.total_cost:.2f}/${self.config.cost_limit_usd:.2f}"
                )
            elif remaining < 0.50:
                logger.warning(f"Low cost balance: ${remaining:.2f} remaining")
        
        # Build messages
        messages = self._build_messages(prompt, system_prompt, context)
        
        # Call LLM based on provider
        if self.config.provider == LLMProvider.OLLAMA:
            response = self._call_ollama(messages)
        elif self.config.provider == LLMProvider.DASHSCOPE:
            response = self._call_dashscope(messages)
        elif self.config.provider == LLMProvider.OPENAI:
            response = self._call_openai(messages)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            response = self._call_anthropic(messages)
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
        
        # Parse response
        result = self._parse_response(response, context, start_time)
        
        return result
    
    def _build_messages(self,
                       prompt: str,
                       system_prompt: str,
                       context: Optional[Dict]) -> List[Dict]:
        """Build message list for LLM API."""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add context if provided
        if context:
            context_text = "## Context\n"
            for key, value in context.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                context_text += f"- **{key}:** {value}\n"
            messages.append({"role": "user", "content": context_text})
        
        # Add main prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _call_ollama(self, messages: List[Dict]) -> Dict:
        """Call Ollama API (local, free)."""
        try:
            import requests
        except ImportError:
            raise ImportError("Install requests: pip install requests")
        
        url = self.config.base_url or "http://localhost:11434/api/chat"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Ollama not running. Start with: ollama serve\n"
                "Or install: curl -fsSL https://ollama.com/install.sh | sh"
            )
        
        data = response.json()
        
        return {
            "content": data.get("message", {}).get("content", ""),
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "provider": "ollama"
        }
    
    def _call_dashscope(self, messages: List[Dict]) -> Dict:
        """Call Dashscope API (Alibaba Cloud)."""
        try:
            import dashscope
        except ImportError:
            raise ImportError("Install dashscope: pip install dashscope")
        
        if not self.config.api_key:
            raise ValueError("Dashscope API key required. Set DASHSCOPE_API_KEY env var.")
        
        dashscope.api_key = self.config.api_key
        
        response = dashscope.Generation.call(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            result_format="message"
        )
        
        if response.status_code != 200:
            raise Exception(f"Dashscope error {response.status_code}: {response.message}")
        
        return {
            "content": response.output.choices[0].message.content,
            "prompt_tokens": response.usage.get("input_tokens", 0),
            "completion_tokens": response.usage.get("output_tokens", 0),
            "provider": "dashscope"
        }
    
    def _call_openai(self, messages: List[Dict]) -> Dict:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        
        if not self.config.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var.")
        
        client = OpenAI(api_key=self.config.api_key, timeout=self.config.timeout)
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return {
            "content": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "provider": "openai"
        }
    
    def _call_anthropic(self, messages: List[Dict]) -> Dict:
        """Call Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")
        
        if not self.config.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var.")
        
        client = anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )
        
        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system_message,
            messages=anthropic_messages
        )
        
        return {
            "content": response.content[0].text,
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "provider": "anthropic"
        }
    
    def _parse_response(self,
                       response: Dict,
                       context: Optional[Dict],
                       start_time: float) -> CodeGenerationResult:
        """Parse LLM response into structured result."""
        content = response.get("content", "")
        
        # Extract code from response
        code = self._extract_code(content)
        
        # Calculate tokens and cost
        prompt_tokens = response.get("prompt_tokens", 0)
        completion_tokens = response.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        cost = self._calculate_cost(prompt_tokens, completion_tokens)
        
        # Validate code
        warnings = self._validate_code(code)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        return CodeGenerationResult(
            success=len(code.strip()) > 0,
            code=code,
            original_file=context.get('file', 'unknown') if context else 'unknown',
            target_file=context.get('target', 'shared/src/commonMain/kotlin') if context else 'unknown',
            tokens_used=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            warnings=warnings,
            metadata={
                'provider': response.get("provider"),
                'model': self.config.model,
                'temperature': self.config.temperature
            }
        )
    
    def _extract_code(self, content: str) -> str:
        """Extract code from LLM response."""
        # Try to parse as JSON first (if we requested JSON)
        try:
            data = json.loads(content)
            if 'code' in data:
                return data['code']
            elif 'migrated_code' in data:
                return data['migrated_code']
        except json.JSONDecodeError:
            pass
        
        # Extract from markdown code blocks
        code_blocks = re.findall(r'```kotlin\s*([\s\S]*?)```', content)
        if code_blocks:
            return code_blocks[0].strip()
        
        # Try other common code block formats
        code_blocks = re.findall(r'```\s*([\s\S]*?)```', content)
        if code_blocks:
            return code_blocks[0].strip()
        
        # Return entire content as last resort
        return content.strip()
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on token usage."""
        cost = (
            prompt_tokens * self.pricing['prompt'] +
            completion_tokens * self.pricing['completion']
        ) / 1000
        
        return cost
    
    def _validate_code(self, code: str) -> List[str]:
        """Validate generated code and return warnings."""
        warnings = []
        
        if not code.strip():
            warnings.append("Generated code is empty")
            return warnings
        
        # Check for common issues
        if 'TODO' in code or 'FIXME' in code:
            warnings.append("Contains TODO/FIXME comments")
        
        # Check for Android-specific imports that should be migrated
        android_imports = [
            'androidx.appcompat',
            'androidx.lifecycle.ViewModel',
            'android.arch.lifecycle',
        ]
        
        for imp in android_imports:
            if imp in code:
                warnings.append(f"Contains Android-specific import: {imp}")
        
        # Check for basic Kotlin syntax
        if 'public class' in code and 'class' not in code.split('public class')[1].split('\n')[0]:
            warnings.append("Possible syntax issue detected")
        
        return warnings
    
    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        return {
            'session_id': self.session_id,
            'request_count': self.request_count,
            'failed_requests': self.failed_requests,
            'total_tokens': self.total_tokens,
            'total_cost_usd': self.total_cost,
            'cost_limit': self.config.cost_limit_usd,
            'cost_remaining': self.config.cost_limit_usd - self.total_cost,
            'success_rate': (self.request_count / (self.request_count + self.failed_requests) * 100)
                           if (self.request_count + self.failed_requests) > 0 else 0
        }
    
    def reset_session(self):
        """Reset session statistics."""
        self.session_id = f"session_{int(time.time())}"
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.failed_requests = 0
        logger.info("Session statistics reset")


def create_llm_executor(provider: str = "ollama",
                       model: str = "qwen2.5-coder:7b",
                       cost_limit: float = 10.0) -> LLMCodeExecutor:
    """
    Create LLM executor with common configurations.
    
    Args:
        provider: Provider name (ollama, dashscope, openai, anthropic)
        model: Model name
        cost_limit: Cost limit in USD
    
    Returns:
        Configured LLMCodeExecutor
    """
    provider_map = {
        'ollama': LLMProvider.OLLAMA,
        'dashscope': LLMProvider.DASHSCOPE,
        'openai': LLMProvider.OPENAI,
        'anthropic': LLMProvider.ANTHROPIC,
    }
    
    config = LLMConfig(
        provider=provider_map.get(provider, LLMProvider.OLLAMA),
        model=model,
        cost_limit_usd=cost_limit
    )
    
    return LLMCodeExecutor(config)
