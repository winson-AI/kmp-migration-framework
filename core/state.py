"""
Centralized State Management for KMP Migration

Inspired by Claude Code's AppState and SessionMemory patterns.

Features:
- Centralized state store (like state/AppStateStore.ts)
- Session-based memory (like services/SessionMemory/sessionMemory.ts)
- Context management (like context/*.tsx)
- File state caching (like utils/fileStateCache.ts)
- Team memory sync (like services/teamMemorySync)

Usage:
    from core.state import MigrationState, StateStore
    
    store = StateStore()
    state = store.get_state()
    state.current_phase = 'analysis'
    store.save()
"""

import os
import json
import time
import hashlib
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class MigrationPhase(Enum):
    """Migration pipeline phases."""
    INIT = "init"
    ANALYSIS = "analysis"
    BATCH_MIGRATION = "batch_migration"
    TESTING = "testing"
    EVALUATION = "evaluation"
    LEARNING = "learning"
    DELIVERY = "delivery"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class FileState:
    """State of a single file being migrated."""
    path: str
    original_hash: str
    migrated_hash: Optional[str] = None
    status: str = "pending"  # pending, in_progress, migrated, failed, skipped
    group_type: Optional[str] = None
    migration_attempts: int = 0
    last_error: Optional[str] = None
    migrated_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchState:
    """State of a file batch."""
    batch_id: str
    group_type: str
    files: List[str] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    success_count: int = 0
    failed_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Memory for a specific agent (like SessionMemory)."""
    agent_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    decisions: List[Dict] = field(default_factory=list)
    learnings: List[Dict] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    
    def add_decision(self, decision_type: str, data: Dict):
        """Record a decision made by the agent."""
        self.decisions.append({
            'timestamp': time.time(),
            'type': decision_type,
            'data': data
        })
        self.updated_at = time.time()
    
    def add_learning(self, learning_type: str, data: Dict):
        """Record a learning from experience."""
        self.learnings.append({
            'timestamp': time.time(),
            'type': learning_type,
            'data': data
        })
        self.updated_at = time.time()


@dataclass
class MigrationState:
    """Complete state of a migration session."""
    session_id: str
    project_path: str
    phase: MigrationPhase = MigrationPhase.INIT
    started_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # File tracking
    files: Dict[str, FileState] = field(default_factory=dict)
    batches: Dict[str, BatchState] = field(default_factory=dict)
    
    # Agent memories
    agent_memories: Dict[str, AgentMemory] = field(default_factory=dict)
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Errors
    errors: List[Dict] = field(default_factory=list)
    
    # Cache
    file_cache: Dict[str, str] = field(default_factory=dict)  # path -> content hash
    context_cache: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'project_path': self.project_path,
            'phase': self.phase.value,
            'started_at': self.started_at,
            'updated_at': self.updated_at,
            'files': {k: asdict(v) for k, v in self.files.items()},
            'batches': {k: asdict(v) for k, v in self.batches.items()},
            'agent_memories': {k: asdict(v) for k, v in self.agent_memories.items()},
            'metrics': self.metrics,
            'errors': self.errors,
            'file_cache': self.file_cache,
            'context_cache': self.context_cache
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MigrationState':
        """Create from dictionary."""
        state = cls(
            session_id=data['session_id'],
            project_path=data['project_path'],
            phase=MigrationPhase(data.get('phase', 'init')),
            started_at=data.get('started_at', time.time()),
            updated_at=data.get('updated_at', time.time()),
            metrics=data.get('metrics', {}),
            errors=data.get('errors', []),
            file_cache=data.get('file_cache', {}),
            context_cache=data.get('context_cache', {})
        )
        
        # Restore FileState objects
        for path, file_data in data.get('files', {}).items():
            state.files[path] = FileState(**file_data)
        
        # Restore BatchState objects
        for batch_id, batch_data in data.get('batches', {}).items():
            state.batches[batch_id] = BatchState(**batch_data)
        
        # Restore AgentMemory objects
        for agent_id, mem_data in data.get('agent_memories', {}).items():
            state.agent_memories[agent_id] = AgentMemory(**mem_data)
        
        return state


class StateStore:
    """
    Centralized state store with persistence.
    
    Inspired by Claude Code's AppStateStore and SessionMemory.
    """
    
    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize state store.
        
        Args:
            state_dir: Directory for state persistence (default: ~/.hermes/kmp-migration/state)
        """
        self.state_dir = state_dir or os.path.expanduser('~/.hermes/kmp-migration/state')
        os.makedirs(self.state_dir, exist_ok=True)
        
        self._current_state: Optional[MigrationState] = None
        self._lock = threading.RLock()
        self._listeners: List[Callable[[MigrationState], None]] = []
        
        # Load existing state if available
        self._load_latest_state()
    
    def create_session(self, project_path: str) -> MigrationState:
        """Create a new migration session."""
        with self._lock:
            session_id = hashlib.md5(f"{project_path}{time.time()}".encode()).hexdigest()[:12]
            
            self._current_state = MigrationState(
                session_id=session_id,
                project_path=project_path
            )
            
            self._save_state()
            logger.info(f"Created new session: {session_id}")
            
            return self._current_state
    
    def get_state(self) -> MigrationState:
        """Get current state."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session. Call create_session() first.")
            return self._current_state
    
    def update_phase(self, phase: MigrationPhase):
        """Update migration phase."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            old_phase = self._current_state.phase
            self._current_state.phase = phase
            self._current_state.updated_at = time.time()
            
            logger.info(f"Phase changed: {old_phase.value} → {phase.value}")
            self._save_state()
            self._notify_listeners()
    
    def track_file(self, file_path: str, content: Optional[str] = None) -> FileState:
        """Track a file's migration state."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            if file_path not in self._current_state.files:
                file_hash = hashlib.md5(content.encode() if content else b'').hexdigest() if content else None
                
                file_state = FileState(
                    path=file_path,
                    original_hash=file_hash or ''
                )
                self._current_state.files[file_path] = file_state
                
                # Update cache
                if content:
                    self._current_state.file_cache[file_path] = file_hash
                
                self._save_state()
            
            return self._current_state.files[file_path]
    
    def update_file_status(self, file_path: str, status: str, error: Optional[str] = None):
        """Update file migration status."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            if file_path in self._current_state.files:
                file_state = self._current_state.files[file_path]
                file_state.status = status
                file_state.last_error = error
                file_state.migration_attempts += 1
                
                if status == 'migrated':
                    file_state.migrated_at = time.time()
                
                self._current_state.updated_at = time.time()
                self._save_state()
    
    def create_batch(self, group_type: str, files: List[str]) -> BatchState:
        """Create a file batch for batch migration."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            batch_id = f"{group_type}_{len(self._current_state.batches)}"
            
            batch = BatchState(
                batch_id=batch_id,
                group_type=group_type,
                files=files
            )
            
            self._current_state.batches[batch_id] = batch
            self._save_state()
            
            return batch
    
    def get_agent_memory(self, agent_id: str) -> AgentMemory:
        """Get or create agent memory."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            if agent_id not in self._current_state.agent_memories:
                self._current_state.agent_memories[agent_id] = AgentMemory(agent_id=agent_id)
                self._save_state()
            
            return self._current_state.agent_memories[agent_id]
    
    def record_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """Record an error."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            self._current_state.errors.append({
                'timestamp': time.time(),
                'type': error_type,
                'message': message,
                'context': context or {}
            })
            self._save_state()
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update metrics."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            self._current_state.metrics.update(metrics)
            self._current_state.updated_at = time.time()
            self._save_state()
    
    def add_context(self, key: str, value: Any):
        """Add to context cache."""
        with self._lock:
            if not self._current_state:
                raise RuntimeError("No active session.")
            
            self._current_state.context_cache[key] = value
            self._save_state()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get from context cache."""
        with self._lock:
            if not self._current_state:
                return default
            return self._current_state.context_cache.get(key, default)
    
    def _save_state(self):
        """Save state to disk."""
        if not self._current_state:
            return
        
        state_file = os.path.join(self.state_dir, f"session_{self._current_state.session_id}.json")
        
        with open(state_file, 'w') as f:
            json.dump(self._current_state.to_dict(), f, indent=2, default=str)
    
    def _load_latest_state(self):
        """Load latest state from disk."""
        state_files = [f for f in os.listdir(self.state_dir) if f.startswith('session_') and f.endswith('.json')]
        
        if not state_files:
            return
        
        # Load most recent
        latest = max(state_files, key=lambda f: os.path.getmtime(os.path.join(self.state_dir, f)))
        state_file = os.path.join(self.state_dir, latest)
        
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                self._current_state = MigrationState.from_dict(data)
                logger.info(f"Loaded state from session: {self._current_state.session_id}")
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def subscribe(self, callback: Callable[[MigrationState], None]):
        """Subscribe to state changes."""
        self._listeners.append(callback)
    
    def _notify_listeners(self):
        """Notify listeners of state changes."""
        for listener in self._listeners:
            try:
                listener(self._current_state)
            except Exception as e:
                logger.error(f"State listener error: {e}")
    
    def export_state(self, output_path: str):
        """Export state to a file."""
        if not self._current_state:
            raise RuntimeError("No active session.")
        
        with open(output_path, 'w') as f:
            json.dump(self._current_state.to_dict(), f, indent=2, default=str)
        
        logger.info(f"State exported to: {output_path}")


# Global state store instance
_state_store: Optional[StateStore] = None

def get_state_store() -> StateStore:
    """Get global state store instance."""
    global _state_store
    if not _state_store:
        _state_store = StateStore()
    return _state_store
