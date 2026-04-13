"""
Agent System - Separation of Prompt, Tools, and Author

Each agent has:
- Prompts: Prompt templates (in prompts/ directory)
- Tools: Tool capabilities (from tool_registry)
- Author: Agent metadata (version, creator, description)

Usage:
    from agents.base import Agent, AgentConfig
    
    agent = Agent(
        id='planner',
        prompts='agents/planner_prompts.json',
        tools=['file_read', 'code_analysis'],
        author={'name': 'KMP Team', 'version': '1.0.0'}
    )
    
    result = agent.execute(input_data={'project_path': '...'})
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentAuthor:
    """Agent authorship information."""
    name: str
    email: Optional[str] = None
    organization: Optional[str] = None
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    license: Optional[str] = "MIT"
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'email': self.email,
            'organization': self.organization,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'license': self.license
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentAuthor':
        return cls(**data)


@dataclass
class AgentPrompt:
    """Agent prompt template."""
    id: str
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    language: str = "en"
    tags: List[str] = field(default_factory=list)
    
    def render(self, **kwargs) -> str:
        """Render prompt with variables."""
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))
        return result
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'template': self.template,
            'variables': self.variables,
            'version': self.version,
            'language': self.language,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentPrompt':
        return cls(**data)


@dataclass
class AgentTool:
    """Tool capability for an agent."""
    tool_id: str
    capability: str
    required: bool = True
    fallback: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'tool_id': self.tool_id,
            'capability': self.capability,
            'required': self.required,
            'fallback': self.fallback,
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentTool':
        return cls(**data)


@dataclass
class AgentConfig:
    """Agent configuration."""
    id: str
    name: str
    description: str
    prompts: Dict[str, AgentPrompt]  # prompt_id -> AgentPrompt
    tools: Dict[str, AgentTool]  # tool_id -> AgentTool
    author: AgentAuthor
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'prompts': {k: v.to_dict() for k, v in self.prompts.items()},
            'tools': {k: v.to_dict() for k, v in self.tools.items()},
            'author': self.author.to_dict(),
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentConfig':
        prompts = {
            k: AgentPrompt.from_dict(v) 
            for k, v in data.get('prompts', {}).items()
        }
        tools = {
            k: AgentTool.from_dict(v) 
            for k, v in data.get('tools', {}).items()
        }
        author = AgentAuthor.from_dict(data.get('author', {}))
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            prompts=prompts,
            tools=tools,
            author=author,
            input_schema=data.get('input_schema', {}),
            output_schema=data.get('output_schema', {}),
            settings=data.get('settings', {})
        )


class Agent:
    """
    Agent with separated prompt, tools, and author.
    
    Components:
    - Prompts: Loaded from JSON files or defined inline
    - Tools: Registered capabilities from tool registry
    - Author: Metadata about agent creation
    """
    
    def __init__(self, config: AgentConfig, tool_registry=None, llm_invoker=None):
        self.config = config
        self.tool_registry = tool_registry
        self.llm_invoker = llm_invoker
        self.execution_history: List[Dict] = []
        self._prompt_cache: Dict[str, str] = {}
    
    def execute(self, input_data: Dict, prompt_id: str = 'default', **kwargs) -> Dict:
        """
        Execute agent with input data.
        
        Args:
            input_data: Input data for the agent
            prompt_id: Which prompt template to use
            **kwargs: Additional prompt variables
        
        Returns:
            Agent execution result
        """
        start_time = time.time()
        
        # Validate input
        self._validate_input(input_data)
        
        # Get prompt
        prompt = self.config.prompts.get(prompt_id)
        if not prompt:
            return {
                'success': False,
                'error': f'Prompt not found: {prompt_id}',
                'agent_id': self.config.id
            }
        
        # Render prompt
        prompt_text = self._render_prompt(prompt, input_data, **kwargs)
        
        # Get tools
        available_tools = self._get_available_tools()
        
        # Execute with LLM
        result = self._execute_with_llm(prompt_text, available_tools, input_data)
        
        # Record execution
        execution_record = {
            'timestamp': time.time(),
            'prompt_id': prompt_id,
            'input_size': len(str(input_data)),
            'output_size': len(str(result)),
            'duration_ms': int((time.time() - start_time) * 1000),
            'success': result.get('success', False)
        }
        self.execution_history.append(execution_record)
        
        return result
    
    def _validate_input(self, input_data: Dict):
        """Validate input against schema."""
        schema = self.config.input_schema
        if not schema:
            return  # No schema to validate against
        
        # Simple validation - check required fields
        required = schema.get('required', [])
        for field in required:
            if field not in input_data:
                raise ValueError(f"Missing required input field: {field}")
    
    def _render_prompt(self, prompt: AgentPrompt, input_data: Dict, **kwargs) -> str:
        """Render prompt with input data and cache."""
        cache_key = f"{prompt.id}:{hash(str(input_data))}"
        
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Merge input data with kwargs
        variables = {**input_data, **kwargs}
        
        # Render
        rendered = prompt.render(**variables)
        
        # Cache
        self._prompt_cache[cache_key] = rendered
        
        return rendered
    
    def _get_available_tools(self) -> List[AgentTool]:
        """Get available tools for this agent."""
        available = []
        
        for tool_id, agent_tool in self.config.tools.items():
            if self.tool_registry:
                tool = self.tool_registry.get_tool(tool_id)
                if tool and tool.status.value == 'available':
                    available.append(agent_tool)
                elif not agent_tool.required:
                    # Optional tool not available - skip
                    pass
                else:
                    # Required tool not available - try fallback
                    if agent_tool.fallback:
                        fallback_tool = self.tool_registry.get_tool(agent_tool.fallback)
                        if fallback_tool:
                            available.append(agent_tool)
            else:
                available.append(agent_tool)
        
        return available
    
    def _execute_with_llm(self, prompt_text: str, tools: List[AgentTool], 
                          input_data: Dict) -> Dict:
        """Execute prompt with LLM."""
        if not self.llm_invoker:
            return {
                'success': False,
                'error': 'No LLM invoker configured',
                'agent_id': self.config.id
            }
        
        try:
            # Build messages
            messages = [
                {'role': 'system', 'content': self._get_system_prompt()},
                {'role': 'user', 'content': prompt_text}
            ]
            
            # Add tool descriptions if available
            if tools:
                tool_descriptions = self._get_tool_descriptions(tools)
                messages[0]['content'] += f"\n\nAvailable tools:\n{tool_descriptions}"
            
            # Invoke LLM
            response = self.llm_invoker.invoke(
                prompt=messages[1]['content'],
                system_prompt=messages[0]['content'],
                json_mode=self.config.settings.get('json_mode', False)
            )
            
            if response.error:
                return {
                    'success': False,
                    'error': response.error,
                    'agent_id': self.config.id
                }
            
            # Parse response
            return {
                'success': True,
                'output': response.content,
                'agent_id': self.config.id,
                'tokens_used': response.tokens_used,
                'latency_ms': response.latency_ms
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.config.id
            }
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for agent."""
        return f"""You are {self.config.name}.

{self.config.description}

Author: {self.config.author.name} v{self.config.author.version}

Follow instructions carefully and provide accurate, helpful responses.
"""
    
    def _get_tool_descriptions(self, tools: List[AgentTool]) -> str:
        """Get descriptions of available tools."""
        if not self.tool_registry:
            return "No tools available"
        
        descriptions = []
        for agent_tool in tools:
            tool = self.tool_registry.get_tool(agent_tool.tool_id)
            if tool:
                descriptions.append(f"- {tool.name}: {tool.description}")
        
        return '\n'.join(descriptions)
    
    def get_stats(self) -> Dict:
        """Get agent execution statistics."""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'avg_duration_ms': 0
            }
        
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e['success'])
        avg_duration = sum(e['duration_ms'] for e in self.execution_history) / total
        
        return {
            'total_executions': total,
            'success_rate': successful / total if total > 0 else 0.0,
            'avg_duration_ms': avg_duration,
            'last_execution': self.execution_history[-1]['timestamp'] if self.execution_history else None
        }
    
    def clear_cache(self):
        """Clear prompt cache."""
        self._prompt_cache.clear()


class AgentFactory:
    """Factory for creating agents from configuration files."""
    
    def __init__(self, agents_dir: Optional[str] = None, 
                 tool_registry=None, llm_invoker=None):
        self.agents_dir = agents_dir or os.path.expanduser('~/.hermes/kmp-migration/agents')
        self.tool_registry = tool_registry
        self.llm_invoker = llm_invoker
        os.makedirs(self.agents_dir, exist_ok=True)
    
    def create_agent(self, agent_id: str) -> Optional[Agent]:
        """Create agent from configuration file."""
        config_file = os.path.join(self.agents_dir, f'{agent_id}.json')
        
        if not os.path.exists(config_file):
            logger.warning(f"Agent config not found: {config_file}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            config = AgentConfig.from_dict(data)
            return Agent(config, self.tool_registry, self.llm_invoker)
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            return None
    
    def list_agents(self) -> List[Dict]:
        """List available agents."""
        agents = []
        
        for filename in os.listdir(self.agents_dir):
            if filename.endswith('.json'):
                agent_id = filename[:-5]  # Remove .json
                config_file = os.path.join(self.agents_dir, filename)
                
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                    
                    agents.append({
                        'id': data.get('id', agent_id),
                        'name': data.get('name', 'Unknown'),
                        'description': data.get('description', ''),
                        'version': data.get('author', {}).get('version', '1.0.0'),
                        'prompts': len(data.get('prompts', {})),
                        'tools': len(data.get('tools', {}))
                    })
                except:
                    pass
        
        return agents
    
    def save_agent(self, config: AgentConfig):
        """Save agent configuration."""
        config_file = os.path.join(self.agents_dir, f'{config.id}.json')
        
        with open(config_file, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"Saved agent config: {config_file}")


def load_agent(agent_id: str, tool_registry=None, llm_invoker=None) -> Optional[Agent]:
    """Load agent from configuration."""
    factory = AgentFactory(tool_registry=tool_registry, llm_invoker=llm_invoker)
    return factory.create_agent(agent_id)
