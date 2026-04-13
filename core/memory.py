"""
Migration Memory System - Cross-Project Learning

Features:
- Pattern Database (what worked/didn't work)
- Migration History (track all migrations)
- Skill Improvement Tracking
- Best Practices Repository
- Failure Analysis

Usage:
    from core.memory import MigrationMemory
    
    memory = MigrationMemory()
    
    # Record a migration
    memory.record_migration(project_path, results)
    
    # Get patterns for similar project
    patterns = memory.get_patterns('MVVM', 'retrofit')
    
    # Get lessons from failures
    lessons = memory.get_failure_lessons('Room migration')
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Type of migration pattern."""
    ARCHITECTURE = "architecture"      # MVVM, MVI, Clean
    LIBRARY = "library"                # Retrofit→Ktor, Room→SQLDelight
    FILE_TYPE = "file_type"            # Activity, ViewModel, Repository
    DEPENDENCY = "dependency"          # Common dependency patterns
    ERROR = "error"                    # Common errors and fixes


class SuccessLevel(Enum):
    """Success level of a pattern."""
    EXCELLENT = "excellent"  # Worked perfectly
    GOOD = "good"           # Worked with minor issues
    FAIR = "fair"           # Worked but needed fixes
    POOR = "poor"           # Had major issues
    FAILED = "failed"       # Didn't work


@dataclass
class MigrationPattern:
    """A reusable migration pattern."""
    id: str
    pattern_type: PatternType
    name: str
    description: str
    source_technology: str
    target_technology: str
    success_level: SuccessLevel
    confidence: float = 0.0  # 0-1 based on past success
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    code_example: Optional[str] = None
    common_issues: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MigrationPattern':
        data['pattern_type'] = PatternType(data['pattern_type'])
        data['success_level'] = SuccessLevel(data['success_level'])
        return cls(**data)
    
    def record_outcome(self, success: bool):
        """Record outcome of using this pattern."""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update confidence
        if self.usage_count > 0:
            self.confidence = self.success_count / self.usage_count
        
        self.updated_at = time.time()


@dataclass
class MigrationRecord:
    """Record of a single migration."""
    id: str
    project_path: str
    project_name: str
    timestamp: float
    duration_seconds: float
    architecture: str
    total_files: int
    migrated_files: int
    failed_files: int
    score: float
    patterns_used: List[str] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MigrationRecord':
        return cls(**data)


@dataclass
class FailureLesson:
    """Lesson learned from a failure."""
    id: str
    error_type: str
    error_message: str
    context: str
    solution: str
    confidence: float = 0.0
    occurrences: int = 1
    resolved: bool = False
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MigrationMemory:
    """
    Memory system for cross-project learning.
    
    Stores:
    - Migration patterns
    - Migration history
    - Failure lessons
    - Best practices
    """
    
    def __init__(self, memory_dir: Optional[str] = None):
        self.memory_dir = memory_dir or os.path.expanduser('~/.hermes/kmp-migration/memory')
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # In-memory caches
        self.patterns: Dict[str, MigrationPattern] = {}
        self.migrations: Dict[str, MigrationRecord] = {}
        self.lessons: Dict[str, FailureLesson] = {}
        
        # Load from disk
        self._load_all()
    
    def record_migration(self, project_path: str, results: Dict):
        """
        Record a migration for future learning.
        
        Args:
            project_path: Path to migrated project
            results: Migration results from harness
        """
        # Create migration record
        record = MigrationRecord(
            id=hashlib.md5(f"{project_path}{time.time()}".encode()).hexdigest()[:12],
            project_path=project_path,
            project_name=os.path.basename(project_path),
            timestamp=time.time(),
            duration_seconds=results.get('total_time_seconds', 0),
            architecture=results.get('architecture', 'Unknown'),
            total_files=results.get('total_files', 0),
            migrated_files=results.get('migrated_files', 0),
            failed_files=results.get('failed_files', 0),
            score=results.get('score', 0),
            patterns_used=results.get('patterns_used', []),
            errors=results.get('errors', []),
            lessons_learned=results.get('lessons_learned', [])
        )
        
        self.migrations[record.id] = record
        self._save_migrations()
        
        # Extract and update patterns
        self._extract_patterns(results)
        
        # Record failure lessons
        for error in results.get('errors', []):
            self._record_failure(error)
        
        logger.info(f"Recorded migration: {record.project_name} (score: {record.score})")
    
    def get_patterns(self, architecture: Optional[str] = None, 
                     library: Optional[str] = None) -> List[MigrationPattern]:
        """
        Get patterns matching criteria.
        
        Args:
            architecture: Filter by architecture (e.g., 'MVVM')
            library: Filter by library (e.g., 'retrofit')
        
        Returns:
            List of matching patterns, sorted by confidence
        """
        matching = []
        
        for pattern in self.patterns.values():
            match = True
            
            if architecture and architecture.lower() not in pattern.tags:
                match = False
            
            if library and library.lower() not in pattern.name.lower():
                match = False
            
            if match:
                matching.append(pattern)
        
        # Sort by confidence (highest first)
        matching.sort(key=lambda p: p.confidence, reverse=True)
        
        return matching
    
    def get_best_practices(self, architecture: str) -> List[str]:
        """Get best practices for an architecture."""
        practices = []
        
        for pattern in self.patterns.values():
            if pattern.success_level in [SuccessLevel.EXCELLENT, SuccessLevel.GOOD]:
                if architecture.lower() in pattern.tags:
                    practices.append(pattern.description)
        
        return practices
    
    def get_failure_lessons(self, error_type: Optional[str] = None) -> List[FailureLesson]:
        """Get lessons from failures."""
        lessons = []
        
        for lesson in self.lessons.values():
            if error_type is None or error_type.lower() in lesson.error_type.lower():
                lessons.append(lesson)
        
        # Sort by occurrences (most common first)
        lessons.sort(key=lambda l: l.occurrences, reverse=True)
        
        return lessons
    
    def get_similar_migrations(self, architecture: str, file_count: int, 
                               limit: int = 5) -> List[MigrationRecord]:
        """Get similar past migrations."""
        similar = []
        
        for record in self.migrations.values():
            # Match architecture
            if architecture.lower() not in record.architecture.lower():
                continue
            
            # Match file count (within 50%)
            if abs(record.total_files - file_count) > file_count * 0.5:
                continue
            
            similar.append(record)
        
        # Sort by score (highest first)
        similar.sort(key=lambda r: r.score, reverse=True)
        
        return similar[:limit]
    
    def recommend_approach(self, architecture: str, libraries: List[str]) -> Dict:
        """
        Recommend migration approach based on past experience.
        
        Args:
            architecture: Project architecture
            libraries: List of libraries used
        
        Returns:
            Recommendation dictionary
        """
        recommendation = {
            'confidence': 0.0,
            'patterns': [],
            'warnings': [],
            'estimated_success_rate': 0.0,
            'similar_projects': []
        }
        
        # Get patterns for architecture
        patterns = self.get_patterns(architecture=architecture)
        recommendation['patterns'] = [p.to_dict() for p in patterns[:5]]
        
        # Get patterns for libraries
        for lib in libraries:
            lib_patterns = self.get_patterns(library=lib)
            recommendation['patterns'].extend([p.to_dict() for p in lib_patterns[:3]])
        
        # Get similar migrations
        similar = self.get_similar_migrations(architecture, 0)  # 0 = any file count
        recommendation['similar_projects'] = [s.to_dict() for s in similar[:3]]
        
        # Calculate estimated success rate
        if similar:
            avg_score = sum(s.score for s in similar) / len(similar)
            recommendation['estimated_success_rate'] = avg_score / 100.0
        
        # Get warnings from failure lessons
        lessons = self.get_failure_lessons()
        for lesson in lessons[:3]:
            if not lesson.resolved:
                recommendation['warnings'].append({
                    'type': lesson.error_type,
                    'message': lesson.error_message,
                    'solution': lesson.solution
                })
        
        # Overall confidence
        if recommendation['patterns'] and recommendation['similar_projects']:
            recommendation['confidence'] = 0.8
        elif recommendation['patterns']:
            recommendation['confidence'] = 0.5
        else:
            recommendation['confidence'] = 0.2  # No prior experience
        
        return recommendation
    
    def _extract_patterns(self, results: Dict):
        """Extract patterns from migration results."""
        # Extract architecture patterns
        architecture = results.get('architecture', 'Unknown')
        if architecture != 'Unknown':
            self._add_or_update_pattern(
                pattern_type=PatternType.ARCHITECTURE,
                name=architecture,
                source='Android',
                target='KMP',
                success=results.get('score', 0) > 60,
                tags=[architecture.lower()]
            )
        
        # Extract library patterns
        for lib_mapping in results.get('library_mappings', []):
            self._add_or_update_pattern(
                pattern_type=PatternType.LIBRARY,
                name=f"{lib_mapping.get('android', '')} → {lib_mapping.get('kmp', '')}",
                source=lib_mapping.get('android', ''),
                target=lib_mapping.get('kmp', ''),
                success=lib_mapping.get('success', True),
                common_issues=lib_mapping.get('issues', []),
                solutions=lib_mapping.get('solutions', [])
            )
    
    def _add_or_update_pattern(self, pattern_type: PatternType, name: str,
                                source: str, target: str, success: bool,
                                tags: Optional[List[str]] = None,
                                common_issues: Optional[List[str]] = None,
                                solutions: Optional[List[str]] = None):
        """Add or update a pattern."""
        pattern_id = hashlib.md5(f"{pattern_type.value}:{name}".encode()).hexdigest()[:12]
        
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.record_outcome(success)
        else:
            pattern = MigrationPattern(
                id=pattern_id,
                pattern_type=pattern_type,
                name=name,
                description=f"Migrate {source} to {target}",
                source_technology=source,
                target_technology=target,
                success_level=SuccessLevel.EXCELLENT if success else SuccessLevel.FAILED,
                confidence=1.0 if success else 0.0,
                usage_count=1,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                tags=tags or [],
                common_issues=common_issues or [],
                solutions=solutions or []
            )
            self.patterns[pattern_id] = pattern
        
        self._save_patterns()
    
    def _record_failure(self, error: Dict):
        """Record a failure lesson."""
        error_type = error.get('type', 'unknown')
        error_message = error.get('message', '')
        
        # Create lesson ID
        lesson_id = hashlib.md5(f"{error_type}:{error_message}".encode()).hexdigest()[:12]
        
        if lesson_id in self.lessons:
            lesson = self.lessons[lesson_id]
            lesson.occurrences += 1
        else:
            lesson = FailureLesson(
                id=lesson_id,
                error_type=error_type,
                error_message=error_message,
                context=error.get('context', ''),
                solution=error.get('solution', 'Review error and fix manually'),
                confidence=0.5
            )
            self.lessons[lesson_id] = lesson
        
        self._save_lessons()
    
    def _load_all(self):
        """Load all memory from disk."""
        self._load_patterns()
        self._load_migrations()
        self._load_lessons()
    
    def _load_patterns(self):
        """Load patterns from disk."""
        patterns_file = os.path.join(self.memory_dir, 'patterns.json')
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = MigrationPattern.from_dict(pattern_data)
                        self.patterns[pattern.id] = pattern
                logger.info(f"Loaded {len(self.patterns)} patterns")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def _load_migrations(self):
        """Load migration records from disk."""
        migrations_file = os.path.join(self.memory_dir, 'migrations.json')
        if os.path.exists(migrations_file):
            try:
                with open(migrations_file, 'r') as f:
                    data = json.load(f)
                    for record_data in data:
                        record = MigrationRecord.from_dict(record_data)
                        self.migrations[record.id] = record
                logger.info(f"Loaded {len(self.migrations)} migration records")
            except Exception as e:
                logger.warning(f"Failed to load migrations: {e}")
    
    def _load_lessons(self):
        """Load failure lessons from disk."""
        lessons_file = os.path.join(self.memory_dir, 'lessons.json')
        if os.path.exists(lessons_file):
            try:
                with open(lessons_file, 'r') as f:
                    data = json.load(f)
                    for lesson_data in data:
                        lesson = FailureLesson(**lesson_data)
                        self.lessons[lesson.id] = lesson
                logger.info(f"Loaded {len(self.lessons)} failure lessons")
            except Exception as e:
                logger.warning(f"Failed to load lessons: {e}")
    
    def _save_patterns(self):
        """Save patterns to disk."""
        patterns_file = os.path.join(self.memory_dir, 'patterns.json')
        with open(patterns_file, 'w') as f:
            json.dump([p.to_dict() for p in self.patterns.values()], f, indent=2)
    
    def _save_migrations(self):
        """Save migration records to disk."""
        migrations_file = os.path.join(self.memory_dir, 'migrations.json')
        with open(migrations_file, 'w') as f:
            json.dump([r.to_dict() for r in self.migrations.values()], f, indent=2)
    
    def _save_lessons(self):
        """Save failure lessons to disk."""
        lessons_file = os.path.join(self.memory_dir, 'lessons.json')
        with open(lessons_file, 'w') as f:
            json.dump([l.to_dict() for l in self.lessons.values()], f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        return {
            'patterns': len(self.patterns),
            'migrations': len(self.migrations),
            'lessons': len(self.lessons),
            'total_usage': sum(p.usage_count for p in self.patterns.values()),
            'avg_confidence': sum(p.confidence for p in self.patterns.values()) / max(len(self.patterns), 1)
        }


# Global memory instance
_memory: Optional[MigrationMemory] = None

def get_memory() -> MigrationMemory:
    """Get global memory instance."""
    global _memory
    if not _memory:
        _memory = MigrationMemory()
    return _memory
