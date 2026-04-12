"""
LLM Provider Abstraction Layer

Supports multiple LLM providers with a unified interface:
- Ollama (local models)
- Dashscope/Qwen (Alibaba Cloud)
- OpenAI
- Anthropic
- Generic HTTP endpoint

Usage:
    from llm.invoker import LLMInvoker
    
    invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')
    response = invoker.invoke("Your prompt here")
    print(response.content)
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OLLAMA = "ollama"
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GENERIC = "generic"


@dataclass
class LLMResponse:
    """Standardized LLM response structure."""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    raw_response: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMConfig:
    """LLM invocation configuration."""
    provider: LLMProvider
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 120
    retry_count: int = 3
    retry_delay_seconds: int = 2
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LLMConfig':
        data['provider'] = LLMProvider(data['provider'])
        return cls(**data)


class LLMInvoker:
    """Unified LLM invocation interface."""
    
    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        """
        Initialize LLM invoker.
        
        Args:
            config: LLMConfig object, or
            provider: Provider name (e.g., 'ollama', 'dashscope')
            model: Model name
            api_key: API key (if required)
            base_url: Custom base URL (for Ollama/generic)
        """
        if config:
            self.config = config
        else:
            self.config = LLMConfig(
                provider=LLMProvider(kwargs.get('provider', 'ollama')),
                model=kwargs.get('model', 'qwen2.5-coder'),
                base_url=kwargs.get('base_url'),
                api_key=kwargs.get('api_key'),
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4096),
            )
        
        self._load_api_keys()
        self._session_history: List[Dict] = []
    
    def _load_api_keys(self):
        """Load API keys from environment if not provided."""
        if not self.config.api_key:
            if self.config.provider == LLMProvider.DASHSCOPE:
                self.config.api_key = os.environ.get('DASHSCOPE_API_KEY')
            elif self.config.provider == LLMProvider.OPENAI:
                self.config.api_key = os.environ.get('OPENAI_API_KEY')
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self.config.api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    def invoke(self, prompt: str, system_prompt: Optional[str] = None, 
               json_mode: bool = False, **kwargs) -> LLMResponse:
        """
        Invoke LLM with the given prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            json_mode: If True, request JSON output
            **kwargs: Additional provider-specific parameters
        
        Returns:
            LLMResponse object
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.config.retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{self.config.retry_count + 1}")
                    time.sleep(self.config.retry_delay_seconds * attempt)
                
                response = self._invoke_provider(prompt, system_prompt, json_mode, **kwargs)
                
                # Record in session history
                self._session_history.append({
                    'timestamp': time.time(),
                    'prompt': prompt[:500],  # Truncate for history
                    'response': response.content[:500],
                    'provider': self.config.provider.value,
                    'model': self.config.model
                })
                
                response.latency_ms = int((time.time() - start_time) * 1000)
                return response
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM invocation failed: {e}")
        
        # All retries failed
        return LLMResponse(
            content="",
            provider=self.config.provider.value,
            model=self.config.model,
            error=f"All retries failed. Last error: {last_error}"
        )
    
    def _invoke_provider(self, prompt: str, system_prompt: Optional[str],
                         json_mode: bool, **kwargs) -> LLMResponse:
        """Route to appropriate provider implementation."""
        if self.config.provider == LLMProvider.OLLAMA:
            return self._invoke_ollama(prompt, system_prompt, json_mode, **kwargs)
        elif self.config.provider == LLMProvider.DASHSCOPE:
            return self._invoke_dashscope(prompt, system_prompt, json_mode, **kwargs)
        elif self.config.provider == LLMProvider.OPENAI:
            return self._invoke_openai(prompt, system_prompt, json_mode, **kwargs)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return self._invoke_anthropic(prompt, system_prompt, json_mode, **kwargs)
        elif self.config.provider == LLMProvider.GENERIC:
            return self._invoke_generic(prompt, system_prompt, json_mode, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
    
    def _invoke_ollama(self, prompt: str, system_prompt: Optional[str],
                       json_mode: bool, **kwargs) -> LLMResponse:
        """Invoke Ollama API."""
        import requests
        
        base_url = self.config.base_url or 'http://localhost:11434'
        url = f"{base_url}/api/generate"
        
        payload = {
            'model': self.config.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': self.config.temperature,
                'num_predict': self.config.max_tokens,
            }
        }
        
        if system_prompt:
            payload['system'] = system_prompt
        
        if json_mode:
            payload['format'] = 'json'
        
        response = requests.post(url, json=payload, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        
        data = response.json()
        return LLMResponse(
            content=data.get('response', ''),
            provider='ollama',
            model=self.config.model,
            tokens_used=data.get('prompt_eval_count', 0) + data.get('eval_count', 0),
            raw_response=data
        )
    
    def _invoke_dashscope(self, prompt: str, system_prompt: Optional[str],
                          json_mode: bool, **kwargs) -> LLMResponse:
        """Invoke Alibaba Dashscope (Qwen) API."""
        try:
            import dashscope
        except ImportError:
            raise ImportError("Please install dashscope: pip install dashscope")
        
        if not self.config.api_key:
            raise ValueError("Dashscope API key required. Set DASHSCOPE_API_KEY env var.")
        
        dashscope.api_key = self.config.api_key
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        response = dashscope.Generation.call(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            result_format='message',
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            return LLMResponse(
                content=content,
                provider='dashscope',
                model=self.config.model,
                tokens_used=response.usage.get('total_tokens', 0),
                raw_response=response.output
            )
        else:
            raise Exception(f"Dashscope error: {response.code} - {response.message}")
    
    def _invoke_openai(self, prompt: str, system_prompt: Optional[str],
                       json_mode: bool, **kwargs) -> LLMResponse:
        """Invoke OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        if not self.config.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var.")
        
        client = OpenAI(api_key=self.config.api_key)
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"} if json_mode else None,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            provider='openai',
            model=self.config.model,
            tokens_used=response.usage.total_tokens,
            raw_response=response.model_dump()
        )
    
    def _invoke_anthropic(self, prompt: str, system_prompt: Optional[str],
                          json_mode: bool, **kwargs) -> LLMResponse:
        """Invoke Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        if not self.config.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var.")
        
        client = anthropic.Anthropic(api_key=self.config.api_key)
        
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=system_prompt or "",
            messages=[{'role': 'user', 'content': prompt}],
        )
        
        return LLMResponse(
            content=response.content[0].text,
            provider='anthropic',
            model=self.config.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            raw_response=response.model_dump()
        )
    
    def _invoke_generic(self, prompt: str, system_prompt: Optional[str],
                        json_mode: bool, **kwargs) -> LLMResponse:
        """Invoke generic HTTP endpoint."""
        import requests
        
        if not self.config.base_url:
            raise ValueError("Generic provider requires base_url")
        
        payload = {
            'prompt': prompt,
            'model': self.config.model,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
        }
        
        if system_prompt:
            payload['system_prompt'] = system_prompt
        
        if json_mode:
            payload['json_mode'] = True
        
        response = requests.post(
            self.config.base_url,
            json=payload,
            headers={'Authorization': f'Bearer {self.config.api_key}'} if self.config.api_key else {},
            timeout=self.config.timeout_seconds
        )
        response.raise_for_status()
        
        data = response.json()
        return LLMResponse(
            content=data.get('content', data.get('response', '')),
            provider='generic',
            model=self.config.model,
            raw_response=data
        )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Multi-turn chat conversation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            LLMResponse object
        """
        # Convert messages to prompt format
        formatted_prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
        return self.invoke(formatted_prompt, **kwargs)
    
    def get_session_history(self, limit: int = 10) -> List[Dict]:
        """Get recent invocation history."""
        return self._session_history[-limit:]
    
    def clear_session_history(self):
        """Clear invocation history."""
        self._session_history = []
