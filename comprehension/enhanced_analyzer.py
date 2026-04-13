"""
Enhanced Project Comprehension - Deep Understanding

Generates comprehensive SPEC.md with:
- Architecture analysis (MVVM, MVI, Clean, etc.)
- File categorization (ViewModels, Activities, Repositories, etc.)
- Dependency analysis with KMP alternatives
- Platform-specific code identification
- Test structure analysis
- Migration complexity estimation

Usage:
    from comprehension.enhanced_analyzer import analyze_project_deep
    spec = analyze_project_deep('/path/to/project')
"""

import os
import re
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ArchitecturePattern:
    """Detected architecture pattern."""
    name: str  # MVVM, MVI, Clean, etc.
    confidence: float  # 0-1
    evidence: List[str] = field(default_factory=list)
    file_count: int = 0


@dataclass
class FileCategory:
    """Category of source files."""
    name: str  # ViewModel, Activity, Repository, etc.
    files: List[str] = field(default_factory=list)
    kmp_compatible: bool = True
    notes: str = ""


@dataclass
class DependencyInfo:
    """Dependency with KMP alternative."""
    group: str
    artifact: str
    version: str
    configuration: str  # implementation, api, testImplementation, etc.
    kmp_alternative: Optional[str] = None
    kmp_compatible: bool = False
    migration_notes: str = ""


@dataclass
class ProjectStructure:
    """Complete project structure analysis."""
    project_name: str
    package_name: str
    min_sdk: int
    target_sdk: int
    architecture: ArchitecturePattern
    modules: List[str]
    file_categories: Dict[str, FileCategory]
    dependencies: List[DependencyInfo]
    test_structure: Dict[str, int]  # test_type -> file_count
    platform_specific: Dict[str, List[str]]  # platform -> files
    complexity_score: int  # 1-10
    estimated_effort_hours: float


# KMP-compatible library mappings
KMP_LIBRARY_MAPPINGS = {
    # Networking
    'com.squareup.retrofit2:retrofit': {
        'kmp': 'io.ktor:ktor-client-core',
        'notes': 'Use Ktor for networking. Add platform-specific engines.'
    },
    'com.squareup.okhttp3:okhttp': {
        'kmp': 'io.ktor:ktor-client-core',
        'notes': 'Ktor uses OkHttp as engine on Android.'
    },
    
    # Database
    'androidx.room:room-runtime': {
        'kmp': 'app.cash.sqldelight:runtime',
        'notes': 'SQLDelight is the recommended KMP database solution.'
    },
    'androidx.room:room-ktx': {
        'kmp': 'app.cash.sqldelight:coroutines-extensions',
        'notes': 'SQLDelight coroutines extensions.'
    },
    
    # Lifecycle/Architecture
    'androidx.lifecycle:lifecycle-viewmodel-ktx': {
        'kmp': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
        'notes': 'Use Kotlin Flow/StateFlow instead of ViewModel.'
    },
    'androidx.lifecycle:lifecycle-livedata-ktx': {
        'kmp': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
        'notes': 'Use Kotlin Flow instead of LiveData.'
    },
    'androidx.lifecycle:lifecycle-runtime-ktx': {
        'kmp': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
        'notes': 'Use coroutines for lifecycle-aware operations.'
    },
    
    # Serialization
    'com.google.code.gson:gson': {
        'kmp': 'org.jetbrains.kotlinx:kotlinx-serialization-json',
        'notes': 'Kotlinx Serialization is KMP-compatible.'
    },
    'com.squareup.moshi:moshi': {
        'kmp': 'org.jetbrains.kotlinx:kotlinx-serialization-json',
        'notes': 'Kotlinx Serialization is recommended.'
    },
    
    # Dependency Injection
    'org.koin:koin-core': {
        'kmp': 'org.koin:koin-core',
        'notes': 'Koin is already KMP-compatible!'
    },
    'com.google.dagger:dagger': {
        'kmp': 'org.koin:koin-core',
        'notes': 'Consider Koin for KMP (simpler than Dagger).'
    },
    
    # Testing
    'junit:junit': {
        'kmp': 'org.jetbrains.kotlin:kotlin-test',
        'notes': 'Use kotlin.test for common tests.'
    },
    'org.junit.jupiter:junit-jupiter': {
        'kmp': 'org.jetbrains.kotlin:kotlin-test',
        'notes': 'Use kotlin.test for common tests.'
    },
    'androidx.test:runner': {
        'kmp': 'org.jetbrains.kotlin:kotlin-test',
        'notes': 'Platform-specific tests remain in androidTest.'
    },
    
    # UI (Android-only, need expect/actual)
    'androidx.appcompat:appcompat': {
        'kmp': None,
        'notes': 'Android UI - keep in androidApp module or use Compose Multiplatform.'
    },
    'com.google.android.material:material': {
        'kmp': None,
        'notes': 'Android UI - keep in androidApp module.'
    },
    'androidx.compose:compose-bom': {
        'kmp': 'org.jetbrains.compose:compose-bom',
        'notes': 'Use Compose Multiplatform for shared UI.'
    }
}

# Architecture patterns detection
ARCHITECTURE_PATTERNS = {
    'MVVM': {
        'indicators': ['ViewModel', 'LiveData', 'StateFlow', 'Binding'],
        'weight': 1.0
    },
    'MVI': {
        'indicators': ['Intent', 'State', 'Reducer', 'Store'],
        'weight': 1.0
    },
    'Clean Architecture': {
        'indicators': ['domain', 'data', 'presentation', 'usecase', 'repository'],
        'weight': 1.0
    },
    'MVP': {
        'indicators': ['Presenter', 'View', 'Contract'],
        'weight': 1.0
    }
}

# File category patterns
FILE_CATEGORIES = {
    'ViewModel': [r'.*ViewModel\.kt$', r'.*ViewModel\.java$'],
    'Activity': [r'.*Activity\.kt$', r'.*Activity\.java$'],
    'Fragment': [r'.*Fragment\.kt$', r'.*Fragment\.java$'],
    'Repository': [r'.*Repository\.kt$', r'.*Repository\.java$'],
    'DataSource': [r'.*DataSource\.kt$', r'.*DataSource\.java$'],
    'DAO': [r'.*Dao\.kt$', r'.*Dao\.java$', r'.*DAO\.kt$'],
    'Entity': [r'.*Entity\.kt$', r'@Entity'],
    'Service': [r'.*Service\.kt$', r'.*Service\.java$'],
    'Adapter': [r'.*Adapter\.kt$', r'.*Adapter\.java$'],
    'Util': [r'.*Util\.kt$', r'.*Utils\.kt$', r'.*Helper\.kt$'],
    'Model': [r'.*Model\.kt$', r'data class.*'],
    'Interface': [r'interface.*'],
}


def analyze_project_deep(project_path: str) -> ProjectStructure:
    """
    Perform deep analysis of Android project.
    
    Args:
        project_path: Path to Android project
    
    Returns:
        ProjectStructure with comprehensive analysis
    """
    logger.info(f"Starting deep analysis of {project_path}")
    
    # Extract basic project info
    project_name = os.path.basename(project_path)
    package_name = _extract_package_name(project_path)
    sdk_info = _extract_sdk_info(project_path)
    
    # Get modules
    modules = _get_project_modules(project_path)
    
    # Analyze architecture
    architecture = _analyze_architecture(project_path)
    
    # Categorize files
    file_categories = _categorize_files(project_path)
    
    # Analyze dependencies
    dependencies = _analyze_dependencies(project_path)
    
    # Analyze test structure
    test_structure = _analyze_tests(project_path)
    
    # Identify platform-specific code
    platform_specific = _identify_platform_specific(project_path)
    
    # Calculate complexity
    complexity = _calculate_complexity(
        architecture=architecture,
        file_categories=file_categories,
        dependencies=dependencies,
        platform_specific=platform_specific
    )
    
    # Estimate effort
    effort = _estimate_effort(complexity, file_categories)
    
    return ProjectStructure(
        project_name=project_name,
        package_name=package_name,
        min_sdk=sdk_info.get('min_sdk', 21),
        target_sdk=sdk_info.get('target_sdk', 33),
        architecture=architecture,
        modules=modules,
        file_categories=file_categories,
        dependencies=dependencies,
        test_structure=test_structure,
        platform_specific=platform_specific,
        complexity_score=complexity,
        estimated_effort_hours=effort
    )


def generate_spec_md(structure: ProjectStructure, output_path: str):
    """
    Generate comprehensive SPEC.md from project structure.
    
    Args:
        structure: Project structure analysis
        output_path: Path to write SPEC.md
    """
    spec = []
    spec.append("# KMP Migration Specification")
    spec.append("")
    spec.append(f"**Project:** {structure.project_name}")
    spec.append(f"**Package:** {structure.package_name}")
    spec.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    spec.append("")
    
    # Architecture
    spec.append("## 1. Architecture Analysis")
    spec.append("")
    spec.append(f"**Detected Pattern:** {structure.architecture.name}")
    spec.append(f"**Confidence:** {structure.architecture.confidence:.0%}")
    spec.append("")
    if structure.architecture.evidence:
        spec.append("**Evidence:**")
        for evidence in structure.architecture.evidence[:5]:
            spec.append(f"- {evidence}")
    spec.append("")
    
    # Modules
    spec.append("## 2. Project Modules")
    spec.append("")
    for module in structure.modules:
        spec.append(f"- `{module}/`")
    spec.append("")
    
    # File Categories
    spec.append("## 3. File Categories")
    spec.append("")
    total_files = sum(len(cat.files) for cat in structure.file_categories.values())
    spec.append(f"**Total Source Files:** {total_files}")
    spec.append("")
    spec.append("| Category | Count | KMP Compatible |")
    spec.append("|----------|-------|----------------|")
    for cat_name, cat in sorted(structure.file_categories.items(), 
                                 key=lambda x: len(x[1].files), reverse=True):
        compatible = "✓" if cat.kmp_compatible else "⚠️"
        spec.append(f"| {cat_name} | {len(cat.files)} | {compatible} |")
    spec.append("")
    
    # Dependencies
    spec.append("## 4. Dependencies")
    spec.append("")
    
    kmp_compatible = [d for d in structure.dependencies if d.kmp_compatible]
    needs_replacement = [d for d in structure.dependencies if d.kmp_alternative]
    android_only = [d for d in structure.dependencies if not d.kmp_compatible and not d.kmp_alternative]
    
    spec.append(f"**Total:** {len(structure.dependencies)}")
    spec.append(f"**KMP Compatible:** {len(kmp_compatible)}")
    spec.append(f"**Need Replacement:** {len(needs_replacement)}")
    spec.append(f"**Android Only:** {len(android_only)}")
    spec.append("")
    
    if needs_replacement:
        spec.append("### Dependencies Needing Replacement")
        spec.append("")
        spec.append("| Android | KMP Alternative | Notes |")
        spec.append("|---------|-----------------|-------|")
        for dep in needs_replacement[:10]:
            spec.append(f"| `{dep.group}:{dep.artifact}` | `{dep.kmp_alternative}` | {dep.migration_notes[:50]} |")
        spec.append("")
    
    # Platform-Specific Code
    spec.append("## 5. Platform-Specific Code")
    spec.append("")
    for platform, files in structure.platform_specific.items():
        if files:
            spec.append(f"### {platform}")
            spec.append("")
            for file in files[:5]:
                spec.append(f"- `{file}`")
            if len(files) > 5:
                spec.append(f"- ... and {len(files) - 5} more")
            spec.append("")
    
    # Test Structure
    spec.append("## 6. Test Structure")
    spec.append("")
    for test_type, count in structure.test_structure.items():
        spec.append(f"- **{test_type}:** {count} files")
    spec.append("")
    
    # Migration Complexity
    spec.append("## 7. Migration Complexity")
    spec.append("")
    spec.append(f"**Complexity Score:** {structure.complexity_score}/10")
    spec.append(f"**Estimated Effort:** {structure.estimated_effort_hours:.1f} hours")
    spec.append("")
    
    # Recommendations
    spec.append("## 8. Migration Recommendations")
    spec.append("")
    spec.append("### Priority 1: Core Logic")
    core_files = structure.file_categories.get('ViewModel', FileCategory('ViewModel'))
    repo_files = structure.file_categories.get('Repository', FileCategory('Repository'))
    if core_files.files or repo_files.files:
        spec.append(f"- Migrate {len(core_files.files) + len(repo_files.files)} ViewModel/Repository files first")
    spec.append("")
    
    spec.append("### Priority 2: Data Layer")
    dao_files = structure.file_categories.get('DAO', FileCategory('DAO'))
    entity_files = structure.file_categories.get('Entity', FileCategory('Entity'))
    if dao_files.files or entity_files.files:
        spec.append(f"- Migrate {len(dao_files.files) + len(entity_files.files)} DAO/Entity files")
        spec.append("- Replace Room with SQLDelight")
    spec.append("")
    
    spec.append("### Priority 3: UI Layer")
    activity_files = structure.file_categories.get('Activity', FileCategory('Activity'))
    if activity_files.files:
        spec.append(f"- Keep {len(activity_files.files)} Activity files in androidApp module")
        spec.append("- Consider Compose Multiplatform for shared UI")
    spec.append("")
    
    # File List
    spec.append("## 9. Complete File List")
    spec.append("")
    for cat_name, cat in sorted(structure.file_categories.items()):
        if cat.files:
            spec.append(f"### {cat_name}")
            spec.append("")
            for file in cat.files:
                spec.append(f"- `{file}`")
            spec.append("")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(spec))
    
    logger.info(f"SPEC.md written to {output_path}")


# Helper Functions

def _extract_package_name(project_path: str) -> str:
    """Extract package name from AndroidManifest.xml."""
    manifest_path = os.path.join(project_path, 'app', 'src', 'main', 'AndroidManifest.xml')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            content = f.read()
            match = re.search(r'package="([^"]+)"', content)
            if match:
                return match.group(1)
    return "unknown"


def _extract_sdk_info(project_path: str) -> Dict[str, int]:
    """Extract SDK versions from build.gradle."""
    sdk_info = {'min_sdk': 21, 'target_sdk': 33}
    
    build_gradle = os.path.join(project_path, 'app', 'build.gradle')
    if not os.path.exists(build_gradle):
        build_gradle = os.path.join(project_path, 'app', 'build.gradle.kts')
    
    if os.path.exists(build_gradle):
        with open(build_gradle, 'r') as f:
            content = f.read()
            
            min_match = re.search(r'minSdk(?:Version)?\s*[=]?\s*(\d+)', content)
            if min_match:
                sdk_info['min_sdk'] = int(min_match.group(1))
            
            target_match = re.search(r'targetSdk(?:Version)?\s*[=]?\s*(\d+)', content)
            if target_match:
                sdk_info['target_sdk'] = int(target_match.group(1))
    
    return sdk_info


def _get_project_modules(project_path: str) -> List[str]:
    """Get project modules from settings.gradle."""
    modules = ['app']  # Default
    
    for settings_file in ['settings.gradle', 'settings.gradle.kts']:
        path = os.path.join(project_path, settings_file)
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                matches = re.findall(r'include\s*[\'"]:([^\'"]+)[\'"]', content)
                modules = [m.replace(':', '') for m in matches]
                break
    
    return modules


def _analyze_architecture(project_path: str) -> ArchitecturePattern:
    """Detect architecture pattern used in project."""
    scores = defaultdict(float)
    evidence = defaultdict(list)
    
    for root, dirs, files in os.walk(os.path.join(project_path, 'app', 'src')):
        if 'test' in root or 'androidTest' in root:
            continue
        
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern, config in ARCHITECTURE_PATTERNS.items():
                    for indicator in config['indicators']:
                        if indicator.lower() in content.lower():
                            scores[pattern] += config['weight']
                            evidence[pattern].append(f"{file}: contains {indicator}")
    
    if not scores:
        return ArchitecturePattern(name='Unknown', confidence=0.0)
    
    best_pattern = max(scores.keys(), key=lambda k: scores[k])
    total_possible = sum(config['weight'] * len(config['indicators']) 
                        for config in ARCHITECTURE_PATTERNS.values())
    confidence = min(1.0, scores[best_pattern] / total_possible)
    
    return ArchitecturePattern(
        name=best_pattern,
        confidence=confidence,
        evidence=evidence[best_pattern][:10],
        file_count=len(evidence[best_pattern])
    )


def _categorize_files(project_path: str) -> Dict[str, FileCategory]:
    """Categorize source files by type."""
    categories = {name: FileCategory(name=name) for name in FILE_CATEGORIES.keys()}
    categories['Other'] = FileCategory(name='Other')
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return categories
    
    for root, dirs, files in os.walk(src_dir):
        if 'test' in root or 'androidTest' in root:
            continue
        
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                categorized = False
                
                # Check by filename pattern
                for cat_name, patterns in FILE_CATEGORIES.items():
                    for pattern in patterns:
                        if pattern.endswith('$'):
                            # Filename pattern
                            if re.search(pattern, file):
                                categories[cat_name].files.append(rel_path)
                                categorized = True
                                break
                        else:
                            # Content pattern
                            if pattern.lower() in content.lower():
                                categories[cat_name].files.append(rel_path)
                                categorized = True
                                break
                    
                    if categorized:
                        break
                
                if not categorized:
                    categories['Other'].files.append(rel_path)
    
    # Mark UI categories as not KMP compatible
    for ui_cat in ['Activity', 'Fragment', 'Adapter']:
        if ui_cat in categories:
            categories[ui_cat].kmp_compatible = False
            categories[ui_cat].notes = "Keep in androidApp or use Compose Multiplatform"
    
    return categories


def _analyze_dependencies(project_path: str) -> List[DependencyInfo]:
    """Analyze dependencies with KMP alternatives."""
    dependencies = []
    
    dep_pattern = re.compile(
        r'(implementation|api|testImplementation|androidTestImplementation)'
        r'\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    )
    
    for root, dirs, files in os.walk(project_path):
        if 'build/' in root or '.gradle/' in root:
            continue
        
        for file in files:
            if file.endswith(('.gradle', '.gradle.kts')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    for match in dep_pattern.finditer(content):
                        config = match.group(1)
                        dep_string = match.group(2)
                        
                        parts = dep_string.split(':')
                        if len(parts) >= 3:
                            group, artifact, version = parts[0], parts[1], parts[2]
                            
                            dep_key = f"{group}:{artifact}"
                            kmp_info = KMP_LIBRARY_MAPPINGS.get(dep_key, {})
                            
                            dep = DependencyInfo(
                                group=group,
                                artifact=artifact,
                                version=version,
                                configuration=config,
                                kmp_alternative=kmp_info.get('kmp'),
                                kmp_compatible=kmp_info.get('kmp') is not None,
                                migration_notes=kmp_info.get('notes', '')
                            )
                            dependencies.append(dep)
    
    return dependencies


def _analyze_tests(project_path: str) -> Dict[str, int]:
    """Analyze test structure."""
    test_counts = {
        'Unit Tests (test/)': 0,
        'Instrumented Tests (androidTest/)': 0,
        'Common Tests (commonTest/)': 0
    }
    
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            if '/test/' in root or '\\test\\' in root:
                test_counts['Unit Tests (test/)'] += 1
            elif '/androidTest/' in root or '\\androidTest\\' in root:
                test_counts['Instrumented Tests (androidTest/)'] += 1
            elif '/commonTest/' in root or '\\commonTest\\' in root:
                test_counts['Common Tests (commonTest/)'] += 1
    
    return test_counts


def _identify_platform_specific(project_path: str) -> Dict[str, List[str]]:
    """Identify platform-specific code."""
    platform_code = {
        'Android UI': [],
        'Android Services': [],
        'Android Broadcast Receivers': [],
        'Android Content Providers': []
    }
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return platform_code
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if 'AppCompatActivity' in content or 'android.view.' in content:
                    platform_code['Android UI'].append(rel_path)
                elif 'Service' in file or 'class.*Service' in content:
                    platform_code['Android Services'].append(rel_path)
                elif 'BroadcastReceiver' in content:
                    platform_code['Android Broadcast Receivers'].append(rel_path)
                elif 'ContentProvider' in content:
                    platform_code['Android Content Providers'].append(rel_path)
    
    return platform_code


def _calculate_complexity(architecture: ArchitecturePattern, 
                          file_categories: Dict[str, FileCategory],
                          dependencies: List[DependencyInfo],
                          platform_specific: Dict[str, List[str]]) -> int:
    """Calculate migration complexity score (1-10)."""
    score = 5.0  # Base score
    
    # Architecture complexity
    if architecture.name == 'Unknown':
        score += 2  # Harder to migrate unknown architecture
    elif architecture.name == 'Clean Architecture':
        score -= 1  # Well-structured, easier to migrate
    
    # File count
    total_files = sum(len(cat.files) for cat in file_categories.values())
    if total_files > 50:
        score += 2
    elif total_files > 20:
        score += 1
    
    # UI-heavy projects are harder
    ui_files = len(file_categories.get('Activity', FileCategory(name='Activity')).files) + \
               len(file_categories.get('Fragment', FileCategory(name='Fragment')).files)
    if ui_files > 10:
        score += 2
    
    # Many dependencies needing replacement
    deps_needing_replacement = sum(1 for d in dependencies if d.kmp_alternative)
    if deps_needing_replacement > 5:
        score += 1
    
    # Platform-specific code
    platform_count = sum(len(files) for files in platform_specific.values())
    if platform_count > 20:
        score += 1
    
    return min(10, max(1, int(score)))


def _estimate_effort(complexity: int, file_categories: Dict[str, FileCategory]) -> float:
    """Estimate migration effort in hours."""
    total_files = sum(len(cat.files) for cat in file_categories.values())
    
    # Base: 0.5 hours per file
    base_hours = total_files * 0.5
    
    # Complexity multiplier
    multiplier = 1.0 + (complexity / 10)
    
    return base_hours * multiplier


# Main function for backward compatibility
def analyze_android_project(project_path: str):
    """Analyze Android project and generate SPEC.md (backward compatible)."""
    structure = analyze_project_deep(project_path)
    spec_path = os.path.join(project_path, 'SPEC.md')
    generate_spec_md(structure, spec_path)
    print(f"SPEC.md generated successfully at {spec_path}")
