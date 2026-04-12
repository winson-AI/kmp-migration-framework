"""
Core Package - Foundation for KMP Migration Framework

Provides:
- State management (inspired by Claude Code AppState)
- Hook system (inspired by Claude Code AsyncHookRegistry)
- Message bus (inspired by Claude Code event system)
- Shared utilities
"""

from .state import (
    StateStore,
    MigrationState,
    FileState,
    BatchState,
    AgentMemory,
    MigrationPhase,
    get_state_store
)

from .hooks import (
    HookRegistry,
    HookContext,
    HookResult,
    HookPhase,
    get_hook_registry,
    create_migration_hooks
)

__all__ = [
    # State
    'StateStore',
    'MigrationState',
    'FileState',
    'BatchState',
    'AgentMemory',
    'MigrationPhase',
    'get_state_store',
    
    # Hooks
    'HookRegistry',
    'HookContext',
    'HookResult',
    'HookPhase',
    'get_hook_registry',
    'create_migration_hooks',
]

__version__ = '2.0.0'
