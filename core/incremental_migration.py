"""
Incremental Migration System - Production Implementation

Allows:
- Migrating files one at a time or in small batches
- Saving state after each file
- Resuming from any checkpoint
- Partial commits
"""

import json
import os
import time
import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    """Status for a file in migration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MIGRATED = "migrated"
    REVIEWED = "reviewed"
    COMMITTED = "committed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileState:
    """State for a single file in migration."""
    path: str
    status: FileStatus = FileStatus.PENDING
    migrated_code: Optional[str] = None
    original_hash: str = ""
    migrated_hash: str = ""
    error: Optional[str] = None
    retry_count: int = 0
    migrated_at: Optional[float] = None
    committed_at: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'path': self.path,
            'status': self.status.value,
            'migrated_code': self.migrated_code[:500] + '...' if self.migrated_code and len(self.migrated_code) > 500 else self.migrated_code,
            'original_hash': self.original_hash,
            'migrated_hash': self.migrated_hash,
            'error': self.error,
            'retry_count': self.retry_count,
            'migrated_at': self.migrated_at,
            'committed_at': self.committed_at
        }


@dataclass
class MigrationState:
    """Complete state of incremental migration."""
    project_path: str
    session_id: str
    started_at: float
    files: Dict[str, FileState] = field(default_factory=dict)
    current_file: Optional[str] = None
    completed: bool = False
    completed_at: Optional[float] = None
    config: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'project_path': self.project_path,
            'session_id': self.session_id,
            'started_at': self.started_at,
            'current_file': self.current_file,
            'completed': self.completed,
            'completed_at': self.completed_at,
            'config': self.config,
            'files': {k: v.to_dict() for k, v in self.files.items()}
        }


class IncrementalMigrator:
    """
    Incremental migration with checkpoint/resume.
    
    Production-ready implementation with:
    - File-by-file migration
    - State persistence (JSON)
    - Resume from any checkpoint
    - Progress tracking
    - Retry logic
    """
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.state_dir = os.path.join(
            project_path,
            '.kmp_migration',
            'state'
        )
        os.makedirs(self.state_dir, exist_ok=True)
        
        self.state = self._load_or_create_state()
    
    def _load_or_create_state(self) -> MigrationState:
        """Load existing state or create new."""
        # Find latest state file
        state_files = [
            f for f in os.listdir(self.state_dir)
            if f.startswith('migration_') and f.endswith('.json')
        ]
        
        if state_files:
            # Load most recent
            latest = max(state_files, key=lambda f: os.path.getmtime(
                os.path.join(self.state_dir, f)
            ))
            return self._load_state_file(os.path.join(self.state_dir, latest))
        
        # Create new state
        session_id = hashlib.md5(
            f"{self.project_path}{time.time()}".encode()
        ).hexdigest()[:12]
        
        return MigrationState(
            project_path=self.project_path,
            session_id=session_id,
            started_at=time.time()
        )
    
    def _load_state_file(self, path: str) -> MigrationState:
        """Load state from file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state = MigrationState(
            project_path=data['project_path'],
            session_id=data['session_id'],
            started_at=data['started_at'],
            current_file=data.get('current_file'),
            completed=data.get('completed', False),
            completed_at=data.get('completed_at'),
            config=data.get('config', {})
        )
        
        # Load files
        for file_path, file_data in data.get('files', {}).items():
            state.files[file_path] = FileState(
                path=file_path,
                status=FileStatus(file_data['status']),
                migrated_code=file_data.get('migrated_code'),
                original_hash=file_data.get('original_hash', ''),
                migrated_hash=file_data.get('migrated_hash', ''),
                error=file_data.get('error'),
                retry_count=file_data.get('retry_count', 0),
                migrated_at=file_data.get('migrated_at'),
                committed_at=file_data.get('committed_at')
            )
        
        logger.info(f"Loaded migration state: {state.session_id}")
        return state
    
    def _save_state(self):
        """Save current state to disk."""
        state_file = os.path.join(
            self.state_dir,
            f"migration_{self.state.session_id}.json"
        )
        
        data = self.state.to_dict()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved migration state: {state_file}")
    
    def initialize(self, files: List[str], config: Optional[Dict] = None):
        """Initialize migration with list of files."""
        for file_path in files:
            self.state.files[file_path] = FileState(
                path=file_path,
                status=FileStatus.PENDING
            )
        
        if config:
            self.state.config = config
        
        self._save_state()
        
        logger.info(f"Initialized migration with {len(files)} files")
    
    def get_next_file(self) -> Optional[str]:
        """Get next file to migrate."""
        for file_path, file_state in self.state.files.items():
            if file_state.status == FileStatus.PENDING:
                return file_path
        
        return None
    
    def get_failed_files(self) -> List[str]:
        """Get list of failed files."""
        return [
            file_path for file_path, file_state in self.state.files.items()
            if file_state.status == FileStatus.FAILED
        ]
    
    def start_file(self, file_path: str) -> bool:
        """Mark file as in progress."""
        if file_path not in self.state.files:
            logger.warning(f"File not in migration: {file_path}")
            return False
        
        self.state.files[file_path].status = FileStatus.IN_PROGRESS
        self.state.current_file = file_path
        self._save_state()
        
        logger.info(f"Started file: {file_path}")
        return True
    
    def complete_file(self,
                     file_path: str,
                     migrated_code: str,
                     success: bool = True,
                     error: Optional[str] = None) -> bool:
        """Mark file as migrated."""
        if file_path not in self.state.files:
            logger.warning(f"File not in migration: {file_path}")
            return False
        
        file_state = self.state.files[file_path]
        
        if success:
            file_state.status = FileStatus.MIGRATED
            file_state.migrated_code = migrated_code
            file_state.migrated_hash = self._hash_code(migrated_code)
            file_state.migrated_at = time.time()
            
            logger.info(f"Completed file: {file_path}")
        else:
            file_state.status = FileStatus.FAILED
            file_state.error = error
            file_state.retry_count += 1
            
            logger.warning(f"Failed file: {file_path} - {error}")
        
        self.state.current_file = None
        self._save_state()
        
        return True
    
    def retry_failed(self, max_retries: int = 3) -> List[str]:
        """Reset failed files for retry."""
        retried = []
        
        for file_path, file_state in self.state.files.items():
            if file_state.status == FileStatus.FAILED:
                if file_state.retry_count < max_retries:
                    file_state.status = FileStatus.PENDING
                    file_state.error = None
                    retried.append(file_path)
        
        self._save_state()
        
        logger.info(f"Retrying {len(retried)} failed files")
        return retried
    
    def mark_reviewed(self, file_path: str) -> bool:
        """Mark file as reviewed."""
        if file_path not in self.state.files:
            return False
        
        file_state = self.state.files[file_path]
        
        if file_state.status != FileStatus.MIGRATED:
            return False
        
        file_state.status = FileStatus.REVIEWED
        self._save_state()
        
        logger.info(f"Marked as reviewed: {file_path}")
        return True
    
    def commit_file(self, file_path: str) -> bool:
        """Mark file as committed."""
        if file_path not in self.state.files:
            return False
        
        file_state = self.state.files[file_path]
        
        if file_state.status not in [FileStatus.MIGRATED, FileStatus.REVIEWED]:
            return False
        
        file_state.status = FileStatus.COMMITTED
        file_state.committed_at = time.time()
        
        self._save_state()
        
        logger.info(f"Committed: {file_path}")
        return True
    
    def skip_file(self, file_path: str, reason: str = "") -> bool:
        """Skip a file (don't migrate)."""
        if file_path not in self.state.files:
            return False
        
        file_state = self.state.files[file_path]
        file_state.status = FileStatus.SKIPPED
        file_state.error = reason
        
        self._save_state()
        
        logger.info(f"Skipped: {file_path} - {reason}")
        return True
    
    def get_progress(self) -> Dict:
        """Get migration progress."""
        total = len(self.state.files)
        
        if total == 0:
            return {
                'total': 0,
                'pending': 0,
                'in_progress': 0,
                'migrated': 0,
                'reviewed': 0,
                'committed': 0,
                'failed': 0,
                'skipped': 0,
                'percent_complete': 0
            }
        
        status_counts = {}
        for file_state in self.state.files.values():
            status = file_state.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        committed = status_counts.get('committed', 0)
        
        return {
            'total': total,
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'migrated': status_counts.get('migrated', 0),
            'reviewed': status_counts.get('reviewed', 0),
            'committed': committed,
            'failed': status_counts.get('failed', 0),
            'skipped': status_counts.get('skipped', 0),
            'percent_complete': (committed / total * 100)
        }
    
    def can_resume(self) -> bool:
        """Check if migration can be resumed."""
        return not self.state.completed and len(self.state.files) > 0
    
    def get_resume_point(self) -> Optional[str]:
        """Get file to resume from."""
        return self.get_next_file()
    
    def get_session_summary(self) -> Dict:
        """Get session summary."""
        progress = self.get_progress()
        
        return {
            'session_id': self.state.session_id,
            'project_path': self.state.project_path,
            'started_at': self.state.started_at,
            'duration_hours': (time.time() - self.state.started_at) / 3600,
            'progress': progress,
            'completed': self.state.completed,
            'config': self.state.config
        }
    
    def export_report(self, output_path: Optional[str] = None) -> str:
        """Export migration report."""
        if not output_path:
            output_path = os.path.join(
                self.state_dir,
                f"report_{self.state.session_id}.md"
            )
        
        summary = self.get_session_summary()
        progress = summary['progress']
        
        report = f"""# Migration Progress Report

**Session:** {self.state.session_id}
**Project:** {self.state.project_path}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Duration:** {summary['duration_hours']:.2f} hours

## Progress

| Status | Count | Percentage |
|--------|-------|------------|
| Total | {progress['total']} | 100% |
| Committed | {progress['committed']} | {progress['percent_complete']:.1f}% |
| Migrated | {progress['migrated']} | {progress['migrated']/progress['total']*100:.1f}% |
| Pending | {progress['pending']} | {progress['pending']/progress['total']*100:.1f}% |
| Failed | {progress['failed']} | {progress['failed']/progress['total']*100:.1f}% |
| Skipped | {progress['skipped']} | {progress['skipped']/progress['total']*100:.1f}% |

## Failed Files

"""
        
        failed_files = self.get_failed_files()
        if failed_files:
            for file_path in failed_files[:10]:
                file_state = self.state.files[file_path]
                report += f"- {file_path}\n"
                if file_state.error:
                    report += f"  - Error: {file_state.error}\n"
            if len(failed_files) > 10:
                report += f"\n... and {len(failed_files) - 10} more\n"
        else:
            report += "*No failed files*\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Exported migration report: {output_path}")
        return output_path
    
    def _hash_code(self, code: str) -> str:
        """Generate hash of code."""
        return hashlib.md5(code.encode()).hexdigest()
    
    def clear_state(self):
        """Clear all state (use with caution)."""
        self.state = MigrationState(
            project_path=self.project_path,
            session_id=hashlib.md5(
                f"{self.project_path}{time.time()}".encode()
            ).hexdigest()[:12],
            started_at=time.time()
        )
        
        # Remove old state files
        for f in os.listdir(self.state_dir):
            if f.startswith('migration_'):
                os.remove(os.path.join(self.state_dir, f))
        
        self._save_state()
        
        logger.info("Cleared migration state")


def create_migrator(project_path: str) -> IncrementalMigrator:
    """Create incremental migrator for a project."""
    return IncrementalMigrator(project_path)
