"""
Interactive Review System - Production Implementation

Allows users to:
- See diffs before changes are applied
- Approve/reject individual files
- Edit suggestions before committing
- Track review decisions
"""

import json
import os
import difflib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status for a file."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    SKIPPED = "skipped"


@dataclass
class FileReview:
    """Review status for a single file."""
    file_path: str
    original_code: str
    migrated_code: str
    status: ReviewStatus = ReviewStatus.PENDING
    user_edits: Optional[str] = None
    review_notes: str = ""
    reviewed_at: Optional[float] = None
    reviewed_by: str = "user"
    
    def get_final_code(self) -> str:
        """Get final code (edited or migrated)."""
        return self.user_edits or self.migrated_code
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'original_code': self.original_code[:500] + '...' if len(self.original_code) > 500 else self.original_code,
            'migrated_code': self.migrated_code[:500] + '...' if len(self.migrated_code) > 500 else self.migrated_code,
            'status': self.status.value,
            'user_edits': self.user_edits is not None,
            'review_notes': self.review_notes,
            'reviewed_at': self.reviewed_at,
            'reviewed_by': self.reviewed_by
        }


@dataclass
class ReviewSession:
    """Session for tracking review progress."""
    session_id: str
    project_path: str
    started_at: float
    files: Dict[str, FileReview] = field(default_factory=dict)
    completed: bool = False
    completed_at: Optional[float] = None
    config: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'project_path': self.project_path,
            'started_at': self.started_at,
            'completed': self.completed,
            'completed_at': self.completed_at,
            'config': self.config,
            'files': {k: v.to_dict() for k, v in self.files.items()}
        }


class InteractiveReviewer:
    """
    Interactive review system for migration changes.
    
    Production-ready implementation with:
    - Diff generation (unified diff)
    - Approve/reject workflow
    - Edit before commit
    - Session persistence
    - Progress tracking
    """
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.review_dir = os.path.join(
            project_path,
            '.kmp_migration',
            'reviews'
        )
        os.makedirs(self.review_dir, exist_ok=True)
        
        self.session = self._load_or_create_session()
    
    def _load_or_create_session(self) -> ReviewSession:
        """Load existing session or create new."""
        import hashlib
        
        # Find latest session file
        session_files = [
            f for f in os.listdir(self.review_dir)
            if f.startswith('review_') and f.endswith('.json')
        ]
        
        if session_files:
            # Load most recent
            latest = max(session_files, key=lambda f: os.path.getmtime(
                os.path.join(self.review_dir, f)
            ))
            return self._load_session_file(os.path.join(self.review_dir, latest))
        
        # Create new session
        session_id = hashlib.md5(
            f"{self.project_path}{time.time()}".encode()
        ).hexdigest()[:12]
        
        return ReviewSession(
            session_id=session_id,
            project_path=self.project_path,
            started_at=time.time()
        )
    
    def _load_session_file(self, path: str) -> ReviewSession:
        """Load session from file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = ReviewSession(
            session_id=data['session_id'],
            project_path=data['project_path'],
            started_at=data['started_at'],
            completed=data.get('completed', False),
            completed_at=data.get('completed_at'),
            config=data.get('config', {})
        )
        
        # Load files
        for file_path, file_data in data.get('files', {}).items():
            session.files[file_path] = FileReview(
                file_path=file_path,
                original_code=file_data.get('original_code', ''),
                migrated_code=file_data.get('migrated_code', ''),
                status=ReviewStatus(file_data.get('status', 'pending')),
                user_edits=file_data.get('user_edits'),
                review_notes=file_data.get('review_notes', ''),
                reviewed_at=file_data.get('reviewed_at'),
                reviewed_by=file_data.get('reviewed_by', 'user')
            )
        
        logger.info(f"Loaded review session: {session.session_id}")
        return session
    
    def add_file_for_review(self,
                           file_path: str,
                           original_code: str,
                           migrated_code: str) -> FileReview:
        """Add a file to the review queue."""
        review = FileReview(
            file_path=file_path,
            original_code=original_code,
            migrated_code=migrated_code
        )
        
        self.session.files[file_path] = review
        
        # Auto-save session
        self._save_session()
        
        logger.info(f"Added file for review: {file_path}")
        return review
    
    def generate_diff(self, file_path: str, context_lines: int = 3) -> str:
        """Generate unified diff for a file."""
        review = self.session.files.get(file_path)
        if not review:
            return ""
        
        diff = difflib.unified_diff(
            review.original_code.splitlines(keepends=True),
            review.migrated_code.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=context_lines
        )
        
        return ''.join(diff)
    
    def approve_file(self,
                    file_path: str,
                    notes: str = "") -> bool:
        """Approve a file for commit."""
        review = self.session.files.get(file_path)
        if not review:
            logger.warning(f"File not found for approval: {file_path}")
            return False
        
        review.status = ReviewStatus.APPROVED
        review.review_notes = notes
        review.reviewed_at = time.time()
        
        self._save_session()
        
        logger.info(f"Approved: {file_path}")
        return True
    
    def reject_file(self,
                   file_path: str,
                   notes: str = "") -> bool:
        """Reject a file (won't be committed)."""
        review = self.session.files.get(file_path)
        if not review:
            logger.warning(f"File not found for rejection: {file_path}")
            return False
        
        review.status = ReviewStatus.REJECTED
        review.review_notes = notes
        review.reviewed_at = time.time()
        
        self._save_session()
        
        logger.info(f"Rejected: {file_path} - {notes}")
        return True
    
    def edit_file(self,
                 file_path: str,
                 edited_code: str,
                 notes: str = "") -> bool:
        """Edit migrated code before committing."""
        review = self.session.files.get(file_path)
        if not review:
            logger.warning(f"File not found for editing: {file_path}")
            return False
        
        review.status = ReviewStatus.EDITED
        review.user_edits = edited_code
        review.review_notes = notes
        review.reviewed_at = time.time()
        
        self._save_session()
        
        logger.info(f"Edited: {file_path}")
        return True
    
    def skip_file(self, file_path: str, notes: str = "") -> bool:
        """Skip a file (don't migrate)."""
        review = self.session.files.get(file_path)
        if not review:
            return False
        
        review.status = ReviewStatus.SKIPPED
        review.review_notes = notes
        review.reviewed_at = time.time()
        
        self._save_session()
        
        logger.info(f"Skipped: {file_path}")
        return True
    
    def get_pending_reviews(self) -> List[FileReview]:
        """Get all pending reviews."""
        return [
            review for review in self.session.files.values()
            if review.status == ReviewStatus.PENDING
        ]
    
    def get_approved_files(self) -> List[FileReview]:
        """Get all approved files ready for commit."""
        return [
            review for review in self.session.files.values()
            if review.status in [ReviewStatus.APPROVED, ReviewStatus.EDITED]
        ]
    
    def get_rejected_files(self) -> List[FileReview]:
        """Get all rejected files."""
        return [
            review for review in self.session.files.values()
            if review.status == ReviewStatus.REJECTED
        ]
    
    def get_session_summary(self) -> Dict:
        """Get summary of review session."""
        total = len(self.session.files)
        pending = len(self.get_pending_reviews())
        approved = len(self.get_approved_files())
        rejected = len(self.get_rejected_files())
        skipped = sum(
            1 for r in self.session.files.values()
            if r.status == ReviewStatus.SKIPPED
        )
        
        return {
            'session_id': self.session.session_id,
            'total_files': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'skipped': skipped,
            'progress_percent': ((total - pending) / total * 100) if total > 0 else 0,
            'completed': self.session.completed
        }
    
    def commit_approved(self, dry_run: bool = False) -> List[str]:
        """Commit all approved files."""
        committed = []
        
        for review in self.get_approved_files():
            if dry_run:
                logger.info(f"Would commit: {review.file_path}")
                committed.append(review.file_path)
                continue
            
            # Determine target path
            target_path = self._get_target_path(review.file_path)
            
            # Get final code (edited or migrated)
            final_code = review.get_final_code()
            
            # Create directory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Write file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            committed.append(review.file_path)
            logger.info(f"Committed: {review.file_path} → {target_path}")
        
        # Mark session complete if all files reviewed
        if len(self.get_pending_reviews()) == 0:
            self.session.completed = True
            self.session.completed_at = time.time()
        
        self._save_session()
        
        return committed
    
    def _get_target_path(self, original_path: str) -> str:
        """Determine target path for migrated file."""
        migrated_project = os.path.join(
            self.project_path,
            'migrated_kmp_project'
        )
        
        # Simple mapping - can be enhanced based on file type
        if 'app/src/main/java' in original_path:
            relative = original_path.split('app/src/main/java')[1]
            target = os.path.join(
                migrated_project,
                'shared/src/commonMain/kotlin',
                relative.lstrip('/')
            )
        elif 'app/src/main/kotlin' in original_path:
            relative = original_path.split('app/src/main/kotlin')[1]
            target = os.path.join(
                migrated_project,
                'shared/src/commonMain/kotlin',
                relative.lstrip('/')
            )
        else:
            target = os.path.join(
                migrated_project,
                'shared/src/commonMain/kotlin',
                os.path.basename(original_path)
            )
        
        return target
    
    def _save_session(self):
        """Save session state to disk."""
        session_file = os.path.join(
            self.review_dir,
            f"review_{self.session.session_id}.json"
        )
        
        data = self.session.to_dict()
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved review session: {session_file}")
    
    def export_report(self, output_path: Optional[str] = None) -> str:
        """Export review report to file."""
        if not output_path:
            output_path = os.path.join(
                self.review_dir,
                f"report_{self.session.session_id}.md"
            )
        
        summary = self.get_session_summary()
        
        report = f"""# Migration Review Report

**Session:** {self.session.session_id}
**Project:** {self.session.project_path}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Count |
|--------|-------|
| Total Files | {summary['total_files']} |
| Approved | {summary['approved']} |
| Rejected | {summary['rejected']} |
| Skipped | {summary['skipped']} |
| Pending | {summary['pending']} |
| Progress | {summary['progress_percent']:.1f}% |

## Approved Files

"""
        
        for review in self.get_approved_files():
            report += f"### {review.file_path}\n\n"
            report += f"**Status:** {review.status.value}\n"
            if review.review_notes:
                report += f"**Notes:** {review.review_notes}\n"
            report += f"\n---\n\n"
        
        if self.get_rejected_files():
            report += "## Rejected Files\n\n"
            for review in self.get_rejected_files():
                report += f"- {review.file_path}: {review.review_notes}\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Exported review report: {output_path}")
        return output_path


def create_reviewer(project_path: str) -> InteractiveReviewer:
    """Create interactive reviewer for a project."""
    return InteractiveReviewer(project_path)
