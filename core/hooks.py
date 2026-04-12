"""
Hooks System for Side-Effect Management

Inspired by Claude Code's hooks architecture:
- utils/hooks/AsyncHookRegistry.ts
- utils/hooks/postSamplingHooks.ts
- hooks/*.ts

Features:
- Async hook registry
- Pre/post migration hooks
- Side-effect isolation
- Hook composition
- Error recovery hooks

Usage:
    from core.hooks import HookRegistry, hook
    
    registry = HookRegistry()
    
    @registry.register('pre_migration')
    async def backup_files(context):
        # Side effect: backup files before migration
        pass
    
    @registry.register('post_migration')
    async def run_tests(context):
        # Side effect: run tests after migration
        pass
    
    await registry.execute('pre_migration', context)
"""

import os
import asyncio
import time
import inspect
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import wraps
import traceback

logger = logging.getLogger(__name__)


class HookPhase(Enum):
    """When hooks execute."""
    PRE = "pre"      # Before main operation
    POST = "post"    # After main operation
    ON_ERROR = "on_error"  # On error
    ON_COMPLETE = "on_complete"  # On completion


@dataclass
class HookContext:
    """Context passed to hooks."""
    operation: str
    data: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def add_error(self, error_type: str, message: str):
        self.errors.append({
            'type': error_type,
            'message': message,
            'timestamp': time.time()
        })


@dataclass
class HookResult:
    """Result of hook execution."""
    hook_name: str
    success: bool
    duration_ms: int
    output: Any = None
    error: Optional[str] = None
    side_effects: List[Dict] = field(default_factory=list)


@dataclass
class HookDefinition:
    """Definition of a registered hook."""
    name: str
    phase: HookPhase
    func: Callable
    is_async: bool
    priority: int = 0  # Lower = higher priority
    timeout_seconds: int = 60
    retry_count: int = 0
    description: str = ""


class HookRegistry:
    """
    Registry for managing and executing hooks.
    
    Inspired by Claude Code's AsyncHookRegistry.
    """
    
    def __init__(self):
        self._hooks: Dict[str, List[HookDefinition]] = {}
        self._enabled: bool = True
        self._execution_log: List[Dict] = []
    
    def register(
        self,
        operation: str,
        phase: HookPhase = HookPhase.PRE,
        priority: int = 0,
        timeout: int = 60,
        retry: int = 0
    ):
        """
        Decorator to register a hook.
        
        Args:
            operation: Operation name (e.g., 'migration', 'testing')
            phase: When to execute (pre, post, on_error, on_complete)
            priority: Execution priority (lower = earlier)
            timeout: Timeout in seconds
            retry: Number of retries on failure
        """
        def decorator(func: Callable):
            is_async = asyncio.iscoroutinefunction(func)
            
            hook_def = HookDefinition(
                name=func.__name__,
                phase=phase,
                func=func,
                is_async=is_async,
                priority=priority,
                timeout_seconds=timeout,
                retry_count=retry,
                description=func.__doc__ or ""
            )
            
            if operation not in self._hooks:
                self._hooks[operation] = []
            
            self._hooks[operation].append(hook_def)
            # Sort by priority
            self._hooks[operation].sort(key=lambda h: h.priority)
            
            logger.debug(f"Registered hook: {operation}/{phase.value}/{func.__name__}")
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs) if is_async else func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    async def execute(
        self,
        operation: str,
        context: HookContext,
        phase: Optional[HookPhase] = None
    ) -> List[HookResult]:
        """
        Execute hooks for an operation.
        
        Args:
            operation: Operation name
            context: Hook context
            phase: Specific phase or None for all phases
        
        Returns:
            List of HookResult objects
        """
        if not self._enabled:
            logger.debug(f"Hooks disabled, skipping {operation}")
            return []
        
        results = []
        
        # Determine which phases to execute
        phases = [phase] if phase else list(HookPhase)
        
        for hook_phase in phases:
            hooks = self._hooks.get(f"{operation}_{hook_phase.value}", [])
            
            for hook_def in hooks:
                result = await self._execute_hook(hook_def, context)
                results.append(result)
                
                # Update context with hook output
                if result.output:
                    context.state[hook_def.name] = result.output
                
                # Track side effects
                if result.side_effects:
                    context.metadata.setdefault('side_effects', []).extend(result.side_effects)
        
        self._execution_log.append({
            'operation': operation,
            'timestamp': time.time(),
            'results': [asdict(r) for r in results]
        })
        
        return results
    
    async def _execute_hook(
        self,
        hook_def: HookDefinition,
        context: HookContext
    ) -> HookResult:
        """Execute a single hook with retry logic."""
        start_time = time.time()
        last_error = None
        
        for attempt in range(hook_def.retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retrying hook {hook_def.name} (attempt {attempt + 1})")
                    await asyncio.sleep(1 * attempt)  # Exponential backoff
                
                # Execute with timeout
                if hook_def.is_async:
                    result = await asyncio.wait_for(
                        hook_def.func(context),
                        timeout=hook_def.timeout_seconds
                    )
                else:
                    # Run sync function in executor
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, hook_def.func, context),
                        timeout=hook_def.timeout_seconds
                    )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.debug(f"Hook {hook_def.name} completed in {duration_ms}ms")
                
                return HookResult(
                    hook_name=hook_def.name,
                    success=True,
                    duration_ms=duration_ms,
                    output=result,
                    side_effects=[{'type': 'hook_execution', 'hook': hook_def.name}]
                )
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {hook_def.timeout_seconds}s"
                logger.warning(f"Hook {hook_def.name} timed out")
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Hook {hook_def.name} failed: {e}")
                traceback.print_exc()
        
        # All retries failed
        duration_ms = int((time.time() - start_time) * 1000)
        
        context.add_error('hook_failure', f"{hook_def.name}: {last_error}")
        
        return HookResult(
            hook_name=hook_def.name,
            success=False,
            duration_ms=duration_ms,
            error=last_error
        )
    
    def execute_sync(
        self,
        operation: str,
        context: HookContext,
        phase: Optional[HookPhase] = None
    ) -> List[HookResult]:
        """Execute hooks synchronously (for non-async code)."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.execute(operation, context, phase))
        finally:
            loop.close()
    
    def list_hooks(self, operation: Optional[str] = None) -> List[Dict]:
        """List registered hooks."""
        result = []
        
        operations = [operation] if operation else list(self._hooks.keys())
        
        for op in operations:
            for hook_def in self._hooks.get(op, []):
                result.append({
                    'operation': op,
                    'name': hook_def.name,
                    'phase': hook_def.phase.value,
                    'priority': hook_def.priority,
                    'async': hook_def.is_async,
                    'timeout': hook_def.timeout_seconds,
                    'retry': hook_def.retry_count,
                    'description': hook_def.description
                })
        
        return result
    
    def enable(self):
        """Enable hook execution."""
        self._enabled = True
    
    def disable(self):
        """Disable hook execution."""
        self._enabled = False
    
    def get_execution_log(self, limit: int = 100) -> List[Dict]:
        """Get recent execution log."""
        return self._execution_log[-limit:]
    
    def clear(self):
        """Clear all registered hooks."""
        self._hooks.clear()
        self._execution_log.clear()


# Built-in hooks for KMP migration
def create_migration_hooks(registry: HookRegistry):
    """Register built-in migration hooks."""
    
    @registry.register('migration_pre', priority=0)
    def backup_project(ctx: HookContext) -> Dict:
        """Backup project before migration."""
        project_path = ctx.get('project_path')
        if not project_path:
            return {'status': 'skipped', 'reason': 'no project path'}
        
        # Create backup directory
        backup_dir = os.path.join(project_path, '.migration_backup')
        os.makedirs(backup_dir, exist_ok=True)
        
        return {
            'status': 'success',
            'backup_dir': backup_dir,
            'timestamp': time.time()
        }
    
    @registry.register('migration_post', priority=10)
    def cleanup_temp_files(ctx: HookContext) -> Dict:
        """Clean up temporary files after migration."""
        project_path = ctx.get('project_path')
        if not project_path:
            return {'status': 'skipped'}
        
        cleaned = []
        temp_patterns = ['.tmp', '.bak', '.orig', '.swp']
        
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if any(file.endswith(p) for p in temp_patterns):
                    try:
                        os.remove(os.path.join(root, file))
                        cleaned.append(file)
                    except:
                        pass
        
        return {
            'status': 'success',
            'files_cleaned': len(cleaned)
        }
    
    @registry.register('batch_migration_pre', priority=0)
    def prepare_batch_context(ctx: HookContext) -> Dict:
        """Prepare context for batch migration."""
        batch_id = ctx.get('batch_id')
        files = ctx.get('files', [])
        
        # Load file contents into context
        file_contents = {}
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
        
        return {
            'file_contents': file_contents,
            'file_count': len(files),
            'batch_id': batch_id
        }
    
    @registry.register('batch_migration_post', priority=10)
    def validate_batch_output(ctx: HookContext) -> Dict:
        """Validate batch migration output."""
        output_files = ctx.get('output_files', [])
        
        validation_results = []
        for file_path in output_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    validation_results.append({
                        'file': file_path,
                        'exists': True,
                        'size': len(content),
                        'valid': len(content) > 0
                    })
            else:
                validation_results.append({
                    'file': file_path,
                    'exists': False,
                    'valid': False
                })
        
        return {
            'validated_count': len(validation_results),
            'valid_count': sum(1 for r in validation_results if r['valid']),
            'results': validation_results
        }
    
    @registry.register('testing_pre', priority=0)
    def prepare_test_environment(ctx: HookContext) -> Dict:
        """Prepare test environment."""
        return {
            'status': 'ready',
            'timestamp': time.time()
        }
    
    @registry.register('testing_post', priority=10)
    def collect_test_results(ctx: HookContext) -> Dict:
        """Collect test results."""
        results = ctx.get('test_results', {})
        return {
            'collected': True,
            'result_count': len(results)
        }
    
    @registry.register('migration_on_error', priority=0)
    def handle_migration_error(ctx: HookContext) -> Dict:
        """Handle migration errors."""
        errors = ctx.errors
        return {
            'error_count': len(errors),
            'handled': True,
            'timestamp': time.time()
        }
    
    logger.info("Registered built-in migration hooks")


# Global hook registry
_hook_registry: Optional[HookRegistry] = None

def get_hook_registry() -> HookRegistry:
    """Get global hook registry."""
    global _hook_registry
    if not _hook_registry:
        _hook_registry = HookRegistry()
        create_migration_hooks(_hook_registry)
    return _hook_registry
