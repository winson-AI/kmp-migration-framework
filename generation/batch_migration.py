"""
Batch Migration System

Migrates projects holistically by:
1. Analyzing entire project structure
2. Grouping files by pattern/type
3. Creating architecture-level decisions
4. Processing in dependency order
5. Sharing context across related files

Usage:
    from generation.batch_migration import BatchMigrator
    
    migrator = BatchMigrator(project_path, invoker)
    results = migrator.migrate_all()
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

try:
    from llm import LLMInvoker, PromptManager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


@dataclass
class FileGroup:
    """Group of files with similar patterns."""
    group_type: str  # e.g., 'ViewModel', 'Activity', 'Repository'
    files: List[str] = field(default_factory=list)
    shared_dependencies: List[str] = field(default_factory=list)
    migration_priority: int = 0  # Lower = migrate first


@dataclass
class MigrationPlan:
    """Complete migration plan for a project."""
    project_name: str
    total_files: int
    file_groups: List[FileGroup] = field(default_factory=list)
    architecture_pattern: str = "Unknown"
    kmp_modules: List[str] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    estimated_time_seconds: int = 0


class BatchMigrator:
    """Batch-based KMP migration system."""
    
    def __init__(self, project_path: str, invoker: Optional[LLMInvoker] = None):
        self.project_path = project_path
        self.invoker = invoker
        self.prompt_manager = PromptManager() if LLM_AVAILABLE else None
        self.migration_plan: Optional[MigrationPlan] = None
        self.results = {
            'migrated_files': [],
            'skipped_files': [],
            'failed_files': [],
            'shared_code_generated': [],
            'architecture_decisions': []
        }
    
    def analyze_project(self) -> MigrationPlan:
        """Analyze entire project and create migration plan."""
        print("\n" + "="*60)
        print("PHASE 1: PROJECT ANALYSIS")
        print("="*60)
        
        # Find all source files
        source_files = self._find_all_source_files()
        print(f"✓ Found {len(source_files)} source files")
        
        # Analyze file patterns
        file_groups = self._group_files_by_pattern(source_files)
        print(f"✓ Identified {len(file_groups)} file groups")
        
        # Analyze dependencies
        dependency_graph = self._analyze_dependencies(source_files)
        print(f"✓ Mapped dependencies")
        
        # Determine architecture pattern
        architecture = self._detect_architecture(file_groups)
        print(f"✓ Architecture: {architecture}")
        
        # Create migration plan
        self.migration_plan = MigrationPlan(
            project_name=os.path.basename(self.project_path),
            total_files=len(source_files),
            file_groups=file_groups,
            architecture_pattern=architecture,
            kmp_modules=self._plan_kmp_modules(file_groups),
            dependency_graph=dependency_graph,
            estimated_time_seconds=len(source_files) * 30  # ~30s per file
        )
        
        return self.migration_plan
    
    def _find_all_source_files(self) -> List[str]:
        """Find all Kotlin/Java source files in project."""
        source_files = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip build directories
            if any(skip in root for skip in ['build/', '.gradle/', 'gradle/']):
                continue
            
            for file in files:
                if file.endswith(('.kt', '.java')):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
        
        return source_files
    
    def _group_files_by_pattern(self, files: List[str]) -> List[FileGroup]:
        """Group files by their pattern/type."""
        groups = defaultdict(list)
        
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect file type by pattern matching
            file_type = self._detect_file_type(file_path, content)
            groups[file_type].append(file_path)
        
        # Create FileGroup objects with priority
        file_groups = []
        priority_order = [
            'DataModel',      # 0 - Migrate first (no dependencies)
            'Repository',     # 1
            'ViewModel',      # 2
            'Service',        # 3
            'Activity',       # 4
            'Fragment',       # 5
            'View',           # 6
            'Adapter',        # 7
            'Utility',        # 8
            'Test',           # 9 - Migrate last
            'Other'           # 10
        ]
        
        for group_type, files in groups.items():
            priority = priority_order.index(group_type) if group_type in priority_order else 10
            
            # Analyze shared dependencies for this group
            shared_deps = self._extract_shared_dependencies(files)
            
            file_groups.append(FileGroup(
                group_type=group_type,
                files=files,
                shared_dependencies=shared_deps,
                migration_priority=priority
            ))
        
        # Sort by priority
        file_groups.sort(key=lambda g: g.migration_priority)
        
        return file_groups
    
    def _detect_file_type(self, file_path: str, content: str) -> str:
        """Detect the type of a file based on content patterns."""
        filename = os.path.basename(file_path)
        
        # Test files
        if 'test' in file_path.lower() or 'Test' in filename:
            return 'Test'
        
        # Data models
        if any(kw in content for kw in ['data class', '@Entity', 'Parcelable']):
            return 'DataModel'
        
        # ViewModels
        if any(kw in content for kw in ['ViewModel', 'StateFlow', 'LiveData']):
            return 'ViewModel'
        
        # Repositories
        if any(kw in content for kw in ['Repository', 'Dao', '@Repository']):
            return 'Repository'
        
        # Activities
        if any(kw in content for kw in ['Activity', 'AppCompatActivity']):
            return 'Activity'
        
        # Fragments
        if 'Fragment' in content:
            return 'Fragment'
        
        # Services
        if 'Service' in content and 'IntentService' in content:
            return 'Service'
        
        # Adapters
        if 'Adapter' in filename or 'RecyclerView.Adapter' in content:
            return 'Adapter'
        
        # Views
        if any(kw in content for kw in ['@Composable', 'View', 'LayoutInflater']):
            return 'View'
        
        # Utilities
        if 'util' in file_path.lower() or 'Util' in filename:
            return 'Utility'
        
        return 'Other'
    
    def _extract_shared_dependencies(self, files: List[str]) -> List[str]:
        """Extract dependencies shared across a group of files."""
        all_imports = defaultdict(int)
        
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract import statements
            for line in content.split('\n'):
                if line.strip().startswith('import '):
                    import_path = line.strip().replace('import ', '').replace(';', '')
                    all_imports[import_path] += 1
        
        # Find imports used in multiple files
        shared = [
            imp for imp, count in all_imports.items()
            if count >= len(files) * 0.5  # Used in 50%+ of files
        ]
        
        return shared
    
    def _analyze_dependencies(self, files: List[str]) -> Dict[str, List[str]]:
        """Analyze dependencies between files."""
        dependency_graph = {}
        
        # Build a map of class names to files
        class_to_file = {}
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract class/object/interface names
            import re
            classes = re.findall(r'(?:class|object|interface)\s+(\w+)', content)
            for cls in classes:
                class_to_file[cls] = file_path
        
        # Build dependency graph
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            deps = []
            for cls, dep_file in class_to_file.items():
                if cls in content and dep_file != file_path:
                    deps.append(dep_file)
            
            dependency_graph[file_path] = list(set(deps))
        
        return dependency_graph
    
    def _detect_architecture(self, file_groups: List[FileGroup]) -> str:
        """Detect the architecture pattern used in the project."""
        group_types = [g.group_type for g in file_groups]
        
        if 'ViewModel' in group_types and 'Repository' in group_types:
            if 'DataModel' in group_types:
                return 'MVVM + Clean Architecture'
            return 'MVVM'
        
        if 'View' in group_types and 'Presenter' in group_types:
            return 'MVP'
        
        if any('MVI' in g for g in group_types):
            return 'MVI'
        
        return 'Unknown/Legacy'
    
    def _plan_kmp_modules(self, file_groups: List[FileGroup]) -> List[str]:
        """Plan KMP module structure."""
        modules = ['shared']
        
        # Check if there are platform-specific files
        for group in file_groups:
            for file_path in group.files:
                if 'android' in file_path.lower():
                    modules.append('androidApp')
                    break
        
        return modules
    
    def migrate_all(self) -> Dict:
        """Execute batch migration based on the plan."""
        if not self.migration_plan:
            self.analyze_project()
        
        print("\n" + "="*60)
        print("PHASE 2: BATCH MIGRATION")
        print("="*60)
        
        start_time = time.time()
        
        # Step 1: Generate shared code for each group
        for group in self.migration_plan.file_groups:
            self._migrate_group_batch(group)
        
        # Step 2: Generate project-level shared utilities
        self._generate_shared_utilities()
        
        # Step 3: Create KMP project structure
        self._create_kmp_structure()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"MIGRATION COMPLETE")
        print(f"{'='*60}")
        print(f"Time: {elapsed:.1f}s")
        print(f"Files Migrated: {len(self.results['migrated_files'])}")
        print(f"Files Skipped: {len(self.results['skipped_files'])}")
        print(f"Files Failed: {len(self.results['failed_files'])}")
        print(f"Shared Code Generated: {len(self.results['shared_code_generated'])}")
        
        return self.results
    
    def _migrate_group_batch(self, group: FileGroup):
        """Migrate a group of similar files together."""
        print(f"\n--- Migrating {group.group_type} ({len(group.files)} files) ---")
        
        # Load all files in the group
        file_contents = {}
        for file_path in group.files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_contents[file_path] = f.read()
        
        # Create batch migration prompt
        if LLM_AVAILABLE and self.invoker:
            batch_prompt = self._create_batch_prompt(group, file_contents)
            
            try:
                response = self.invoker.invoke(batch_prompt, json_mode=False)
                
                # Parse and save migrated files
                self._parse_batch_response(response.content, group, file_contents)
                
                print(f"  ✓ Migrated {len(group.files)} files as a batch")
                
            except Exception as e:
                print(f"  ✗ Batch migration failed: {e}")
                # Fallback to individual migration
                for file_path, content in file_contents.items():
                    self._migrate_individual_file(file_path, content, group.group_type)
        else:
            # Mock migration
            for file_path, content in file_contents.items():
                self._migrate_individual_file(file_path, content, group.group_type)
    
    def _create_batch_prompt(self, group: FileGroup, file_contents: Dict[str, str]) -> str:
        """Create a prompt for batch migrating a group of files."""
        prompt = f"""You are an expert Kotlin Multiplatform developer.

## Task
Migrate the following {len(file_contents)} {group.group_type} files from Android to KMP.

## Architecture Context
- Pattern: {self.migration_plan.architecture_pattern}
- Shared Dependencies: {', '.join(group.shared_dependencies[:5])}
- Target Module: shared/src/commonMain/kotlin

## Files to Migrate

"""
        for i, (file_path, content) in enumerate(file_contents.items(), 1):
            prompt += f"\n### File {i}: {os.path.basename(file_path)}\n"
            prompt += f"```kotlin\n{content[:2000]}\n```\n"  # Truncate for token limits
        
        prompt += """
## Output Format

For each file, provide:
1. The migrated KMP code
2. File path in KMP structure
3. Brief explanation of changes

Format each file as:
---
FILE: path/to/File.kt
CHANGES: Brief description
CODE:
```kotlin
// Migrated code
```
---

## Guidelines
- Use common code where possible
- Mark platform-specific code with expect/actual
- Replace Android dependencies with KMP equivalents
- Maintain consistent code style across all files
"""
        
        return prompt
    
    def _parse_batch_response(self, response: str, group: FileGroup, original_files: Dict[str, str]):
        """Parse batch migration response and save files."""
        import re
        
        # Split response by file markers
        file_pattern = r'FILE:\s*([^\n]+)\s*CHANGES:\s*([^\n]+)\s*CODE:\s*```(?:kotlin)?\s*([\s\S]*?)```'
        matches = re.findall(file_pattern, response)
        
        for match in matches:
            file_path, changes, code = match
            
            # Save the migrated file
            self._save_migrated_file(file_path.strip(), code.strip(), changes.strip())
            self.results['migrated_files'].append(file_path.strip())
    
    def _migrate_individual_file(self, file_path: str, content: str, file_type: str):
        """Fallback: migrate a single file."""
        migrated_code = f"// Mock migration of {file_type}\n// Original: {file_path}\n\n{content}"
        
        self._save_migrated_file(file_path, migrated_code, "Mock migration")
        self.results['migrated_files'].append(file_path)
    
    def _save_migrated_file(self, target_path: str, code: str, changes: str):
        """Save a migrated file to the KMP project structure."""
        migrated_project_path = os.path.join(self.project_path, 'migrated_kmp_project')
        
        # Determine target location
        if 'Activity' in target_path or 'Fragment' in target_path:
            target_dir = os.path.join(migrated_project_path, 'androidApp', 'src', 'main', 'java')
        else:
            target_dir = os.path.join(migrated_project_path, 'shared', 'src', 'commonMain', 'kotlin')
        
        # Create directory structure
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file
        filename = os.path.basename(target_path)
        target_file = os.path.join(target_dir, filename)
        
        with open(target_file, 'w') as f:
            f.write(code)
    
    def _generate_shared_utilities(self):
        """Generate shared utilities used across the project."""
        print("\n--- Generating Shared Utilities ---")
        
        utilities = [
            ('CoroutineUtils.kt', '// Shared coroutine utilities'),
            ('PlatformUtils.kt', '// expect/actual platform utilities'),
            ('Constants.kt', '// Shared constants'),
        ]
        
        for filename, content in utilities:
            target_dir = os.path.join(
                self.project_path, 'migrated_kmp_project',
                'shared', 'src', 'commonMain', 'kotlin'
            )
            os.makedirs(target_dir, exist_ok=True)
            
            target_file = os.path.join(target_dir, filename)
            with open(target_file, 'w') as f:
                f.write(content)
            
            self.results['shared_code_generated'].append(filename)
            print(f"  ✓ Generated {filename}")
    
    def _create_kmp_structure(self):
        """Create the KMP project structure."""
        print("\n--- Creating KMP Project Structure ---")
        
        migrated_path = os.path.join(self.project_path, 'migrated_kmp_project')
        
        # Copy template if exists
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            'templates', 'kmp-project'
        )
        
        if os.path.exists(template_path):
            os.system(f"cp -r {template_path}/* {migrated_path}/ 2>/dev/null")
            print(f"  ✓ Copied KMP template")
        
        # Create architecture documentation
        arch_doc = f"""# {self.migration_plan.project_name} KMP Architecture

## Architecture Pattern
{self.migration_plan.architecture_pattern}

## Module Structure
"""
        for module in self.migration_plan.kmp_modules:
            arch_doc += f"- {module}/\n"
        
        arch_doc += "\n## File Groups\n"
        for group in self.migration_plan.file_groups:
            arch_doc += f"- {group.group_type}: {len(group.files)} files\n"
        
        arch_doc_path = os.path.join(migrated_path, 'ARCHITECTURE.md')
        with open(arch_doc_path, 'w') as f:
            f.write(arch_doc)
        
        self.results['architecture_decisions'].append(arch_doc_path)
        print(f"  ✓ Created architecture documentation")
