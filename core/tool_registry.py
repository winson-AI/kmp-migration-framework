"""
Tool Registry System - Managed Tool Capabilities

Features:
- Tool Discovery (find available tools)
- Tool Versioning (track tool versions)
- Tool Composition (chain tools together)
- Tool Fallback (if one fails, try another)
- Tool Health Monitoring (check if tools are working)

Usage:
    from core.tool_registry import ToolRegistry, Tool
    
    registry = ToolRegistry()
    
    # Register a tool
    registry.register(FileWriteTool())
    
    # Get tool by capability
    tool = registry.get_tool('file_write')
    
    # Execute with fallback
    result = registry.execute_with_fallback(
        capability='llm_generate',
        input_data={'prompt': '...'},
        fallbacks=['mock_generator']
    )
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
import subprocess

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Status of a tool."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class ToolCapability(Enum):
    """Tool capability types."""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    LLM_GENERATE = "llm_generate"
    LLM_REVIEW = "llm_review"
    GIT_OPERATION = "git_operation"
    GRADLE_COMMAND = "gradle_command"
    CODE_ANALYSIS = "code_analysis"
    TEST_EXECUTION = "test_execution"


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    tool_name: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'duration_ms': self.duration_ms,
            'tool_name': self.tool_name
        }


@dataclass
class Tool:
    """A tool in the registry."""
    id: str
    name: str
    description: str
    capability: ToolCapability
    version: str
    status: ToolStatus = ToolStatus.AVAILABLE
    health_score: float = 1.0  # 0-1
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'capability': self.capability.value,
            'version': self.version,
            'status': self.status.value,
            'health_score': self.health_score,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_used': self.last_used,
            'metadata': self.metadata
        }
    
    def record_outcome(self, success: bool):
        """Record tool execution outcome."""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update health score
        if self.usage_count > 0:
            self.health_score = self.success_count / self.usage_count
        
        self.last_used = time.time()
        
        # Update status based on health
        if self.health_score < 0.5:
            self.status = ToolStatus.DEGRADED
        elif self.health_score > 0.8:
            self.status = ToolStatus.AVAILABLE


class ToolRegistry:
    """
    Registry for managing migration tools.
    
    Features:
    - Tool discovery
    - Health monitoring
    - Fallback execution
    - Tool composition
    """
    
    def __init__(self, registry_file: Optional[str] = None):
        self.registry_file = registry_file or os.path.expanduser('~/.hermes/kmp-migration/tools.json')
        self.tools: Dict[str, Tool] = {}
        self.tool_implementations: Dict[str, Callable] = {}
        
        # Load from disk
        self._load_registry()
        
        # Register built-in tools
        self._register_builtin_tools()
    
    def register(self, tool: Tool, implementation: Optional[Callable] = None):
        """
        Register a tool.
        
        Args:
            tool: Tool definition
            implementation: Tool implementation function
        """
        self.tools[tool.id] = tool
        
        if implementation:
            self.tool_implementations[tool.id] = implementation
        
        self._save_registry()
        logger.info(f"Registered tool: {tool.name} ({tool.id})")
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get tool by ID."""
        return self.tools.get(tool_id)
    
    def get_tools_by_capability(self, capability: ToolCapability) -> List[Tool]:
        """Get all tools with a capability."""
        return [
            tool for tool in self.tools.values()
            if tool.capability == capability and tool.status == ToolStatus.AVAILABLE
        ]
    
    def get_best_tool(self, capability: ToolCapability) -> Optional[Tool]:
        """Get best tool for a capability (highest health score)."""
        tools = self.get_tools_by_capability(capability)
        if not tools:
            return None
        
        # Sort by health score (highest first)
        tools.sort(key=lambda t: t.health_score, reverse=True)
        return tools[0]
    
    def execute(self, tool_id: str, **kwargs) -> ToolResult:
        """
        Execute a tool.
        
        Args:
            tool_id: Tool ID
            **kwargs: Tool arguments
        
        Returns:
            ToolResult
        """
        tool = self.get_tool(tool_id)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_id}",
                tool_name=tool_id
            )
        
        if tool.status == ToolStatus.UNAVAILABLE:
            return ToolResult(
                success=False,
                error=f"Tool unavailable: {tool_id}",
                tool_name=tool_id
            )
        
        implementation = self.tool_implementations.get(tool_id)
        if not implementation:
            return ToolResult(
                success=False,
                error=f"No implementation for tool: {tool_id}",
                tool_name=tool_id
            )
        
        start_time = time.time()
        
        try:
            output = implementation(**kwargs)
            duration_ms = int((time.time() - start_time) * 1000)
            
            tool.record_outcome(True)
            
            return ToolResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                tool_name=tool_id
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            tool.record_outcome(False)
            
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                tool_name=tool_id
            )
    
    def execute_with_fallback(self, capability: ToolCapability, 
                              fallbacks: Optional[List[str]] = None,
                              **kwargs) -> ToolResult:
        """
        Execute tool with fallback options.
        
        Args:
            capability: Required capability
            fallbacks: List of fallback tool IDs
            **kwargs: Tool arguments
        
        Returns:
            ToolResult from first successful tool
        """
        # Try best tool for capability
        tool = self.get_best_tool(capability)
        
        if tool:
            result = self.execute(tool.id, **kwargs)
            if result.success:
                return result
        
        # Try fallbacks
        if fallbacks:
            for fallback_id in fallbacks:
                result = self.execute(fallback_id, **kwargs)
                if result.success:
                    return result
        
        # All failed
        return ToolResult(
            success=False,
            error=f"All tools failed for capability: {capability.value}",
            tool_name=capability.value
        )
    
    def check_health(self, tool_id: str) -> ToolStatus:
        """Check health of a tool."""
        tool = self.get_tool(tool_id)
        if not tool:
            return ToolStatus.UNAVAILABLE
        
        # Run health check based on tool type
        try:
            if tool_id.startswith('file_'):
                # Check file system access
                test_file = os.path.join(os.path.dirname(self.registry_file), '.health_check')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    tool.status = ToolStatus.AVAILABLE
                except:
                    tool.status = ToolStatus.UNAVAILABLE
            
            elif tool_id.startswith('git_'):
                # Check git availability
                result = subprocess.run(['git', '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    tool.status = ToolStatus.AVAILABLE
                else:
                    tool.status = ToolStatus.UNAVAILABLE
            
            elif tool_id.startswith('gradle_'):
                # Check gradle availability
                result = subprocess.run(['./gradlew', '--version'], 
                                      capture_output=True, timeout=10,
                                      cwd=os.path.dirname(self.registry_file))
                if result.returncode == 0:
                    tool.status = ToolStatus.AVAILABLE
                else:
                    tool.status = ToolStatus.DEGRADED
            
            elif tool_id.startswith('llm_'):
                # LLM tools - check if configured
                if tool.metadata.get('configured', False):
                    tool.status = ToolStatus.AVAILABLE
                else:
                    tool.status = ToolStatus.DEGRADED
            
        except Exception as e:
            logger.warning(f"Health check failed for {tool_id}: {e}")
            tool.status = ToolStatus.DEGRADED
        
        return tool.status
    
    def check_all_health(self) -> Dict[str, ToolStatus]:
        """Check health of all tools."""
        results = {}
        for tool_id in self.tools.keys():
            results[tool_id] = self.check_health(tool_id)
        return results
    
    def compose_tools(self, tool_ids: List[str], **kwargs) -> List[ToolResult]:
        """
        Execute multiple tools in sequence (composition).
        
        Args:
            tool_ids: List of tool IDs to execute in order
            **kwargs: Arguments passed to all tools
        
        Returns:
            List of ToolResults
        """
        results = []
        
        for tool_id in tool_ids:
            result = self.execute(tool_id, **kwargs)
            results.append(result)
            
            # Stop on failure
            if not result.success:
                break
        
        return results
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        # File operations
        self.register(Tool(
            id='file_read',
            name='File Reader',
            description='Read files from filesystem',
            capability=ToolCapability.FILE_READ,
            version='1.0.0'
        ), self._file_read_impl)
        
        self.register(Tool(
            id='file_write',
            name='File Writer',
            description='Write files to filesystem',
            capability=ToolCapability.FILE_WRITE,
            version='1.0.0'
        ), self._file_write_impl)
        
        # Git operations
        self.register(Tool(
            id='git_status',
            name='Git Status',
            description='Check git repository status',
            capability=ToolCapability.GIT_OPERATION,
            version='1.0.0',
            metadata={'command': 'git status'}
        ), self._git_status_impl)
        
        # LLM operations (mock implementations)
        self.register(Tool(
            id='llm_generate_mock',
            name='LLM Generator (Mock)',
            description='Generate code (mock implementation)',
            capability=ToolCapability.LLM_GENERATE,
            version='1.0.0',
            status=ToolStatus.AVAILABLE,
            metadata={'configured': True}
        ), self._llm_generate_mock_impl)
        
        self.register(Tool(
            id='llm_review_mock',
            name='LLM Reviewer (Mock)',
            description='Review code (mock implementation)',
            capability=ToolCapability.LLM_REVIEW,
            version='1.0.0',
            status=ToolStatus.AVAILABLE,
            metadata={'configured': True}
        ), self._llm_review_mock_impl)
        
        logger.info(f"Registered {len(self.tools)} built-in tools")
    
    def _file_read_impl(self, path: str) -> str:
        """File read implementation."""
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _file_write_impl(self, path: str, content: str) -> bool:
        """File write implementation."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return True
    
    def _git_status_impl(self, cwd: Optional[str] = None) -> str:
        """Git status implementation."""
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10
        )
        return result.stdout
    
    def _llm_generate_mock_impl(self, prompt: str, **kwargs) -> str:
        """Mock LLM generate implementation."""
        return f"// Mock generated code for: {prompt[:50]}..."
    
    def _llm_review_mock_impl(self, code: str, **kwargs) -> Dict:
        """Mock LLM review implementation."""
        return {
            'score': 7.5,
            'feedback': 'Mock review - code looks good',
            'issues': [],
            'recommendations': []
        }
    
    def _load_registry(self):
        """Load tool registry from disk."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                    for tool_data in data:
                        tool = Tool(**tool_data)
                        tool.capability = ToolCapability(tool.capability)
                        tool.status = ToolStatus(tool.status)
                        self.tools[tool.id] = tool
                logger.info(f"Loaded {len(self.tools)} tools from registry")
            except Exception as e:
                logger.warning(f"Failed to load tool registry: {e}")
    
    def _save_registry(self):
        """Save tool registry to disk."""
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, 'w') as f:
            json.dump([t.to_dict() for t in self.tools.values()], f, indent=2)
    
    def list_tools(self) -> List[Dict]:
        """List all registered tools."""
        return [t.to_dict() for t in self.tools.values()]
    
    def get_stats(self) -> Dict:
        """Get tool registry statistics."""
        return {
            'total_tools': len(self.tools),
            'available': sum(1 for t in self.tools.values() if t.status == ToolStatus.AVAILABLE),
            'degraded': sum(1 for t in self.tools.values() if t.status == ToolStatus.DEGRADED),
            'unavailable': sum(1 for t in self.tools.values() if t.status == ToolStatus.UNAVAILABLE),
            'total_usage': sum(t.usage_count for t in self.tools.values()),
            'avg_health': sum(t.health_score for t in self.tools.values()) / max(len(self.tools), 1)
        }


# Global registry instance
_registry: Optional[ToolRegistry] = None

def get_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if not _registry:
        _registry = ToolRegistry()
    return _registry
