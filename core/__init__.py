"""
Core Package - Foundation for KMP Migration Framework

Provides:
- Harness: Advanced orchestration (checkpoint, parallel, recovery)
- Memory: Cross-project learning (patterns, history, lessons)
- Tools: Tool registry (discovery, fallback, composition)
- State: Session management (inspired by Claude Code AppState)
- Hooks: Side-effect management (inspired by Claude Code AsyncHookRegistry)
- Config: Centralized configuration
- Validation: Input validation
"""

from .harness import (
    MigrationHarness,
    HarnessConfig,
    PhaseStatus,
    ErrorStrategy,
    PhaseResult,
    MigrationCheckpoint,
    run_with_harness
)

from .memory import (
    MigrationMemory,
    MigrationPattern,
    MigrationRecord,
    FailureLesson,
    PatternType,
    SuccessLevel,
    get_memory
)

from .tool_registry import (
    ToolRegistry,
    Tool,
    ToolResult,
    ToolCapability,
    ToolStatus,
    get_registry
)

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

from .config import (
    MigrationConfig,
    LLMConfig,
    LLMProvider,
    MigrationMode,
    load_config,
    save_config,
    create_config_wizard,
    print_config
)

from .input_validator import (
    InputValidator,
    validate_inputs,
    print_requirements,
    ValidationResult
)

__all__ = [
    # Harness (NEW)
    'MigrationHarness',
    'HarnessConfig',
    'PhaseStatus',
    'ErrorStrategy',
    'PhaseResult',
    'MigrationCheckpoint',
    'run_with_harness',
    
    # Memory (NEW)
    'MigrationMemory',
    'MigrationPattern',
    'MigrationRecord',
    'FailureLesson',
    'PatternType',
    'SuccessLevel',
    'get_memory',
    
    # Tools (NEW)
    'ToolRegistry',
    'Tool',
    'ToolResult',
    'ToolCapability',
    'ToolStatus',
    'get_registry',
    
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
    
    # Config
    'MigrationConfig',
    'LLMConfig',
    'LLMProvider',
    'MigrationMode',
    'load_config',
    'save_config',
    'create_config_wizard',
    'print_config',
    
    # Input Validation
    'InputValidator',
    'validate_inputs',
    'print_requirements',
    'ValidationResult',
]

__version__ = '3.0.0'
