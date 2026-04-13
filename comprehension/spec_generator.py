"""
SPEC.md Generator - PRD, DESIGN, PLAN

Generates comprehensive specification document with:
1. PRD (Product Requirements Document) - What the app does
2. DESIGN - Architecture, patterns, structure
3. PLAN - Detailed migration strategy

This is the EXPLORE phase - deep understanding before migration.
"""

import os
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppFeature:
    """A feature of the Android app."""
    name: str
    description: str
    files: List[str] = field(default_factory=list)
    priority: str = "high"  # high, medium, low
    kmp_impact: str = "shared"  # shared, android-only, ios-only


@dataclass
class DataModel:
    """A data model/entity in the app."""
    name: str
    package: str
    fields: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    is_room_entity: bool = False


@dataclass
class Screen:
    """A UI screen in the app."""
    name: str
    type: str  # Activity, Fragment, Composable
    layout_file: Optional[str] = None
    viewmodel: Optional[str] = None
    navigation: List[str] = field(default_factory=list)


@dataclass
class PRD:
    """Product Requirements Document."""
    app_name: str
    package_name: str
    description: str
    features: List[AppFeature]
    data_models: List[DataModel]
    screens: List[Screen]
    user_flows: List[Dict]


@dataclass
class Design:
    """Architecture Design Document."""
    architecture_pattern: str
    architecture_confidence: float
    layers: Dict[str, List[str]]  # layer -> files
    dependency_graph: Dict[str, List[str]]  # file -> dependencies
    patterns_used: List[str]
    kmp_structure: Dict[str, str]  # module -> purpose


@dataclass
class MigrationPlan:
    """Detailed Migration Plan."""
    phases: List[Dict]  # phase -> tasks
    file_groups: List[Dict]  # groups for batch migration
    dependency_replacements: List[Dict]
    expect_actual_requirements: List[Dict]
    risk_assessment: List[Dict]
    timeline_estimate: Dict


def generate_comprehensive_spec(project_path: str) -> str:
    """
    Generate comprehensive SPEC.md with PRD, DESIGN, and PLAN.
    
    This is the EXPLORE phase - deep understanding of the Android project.
    """
    logger.info(f"Starting comprehensive SPEC generation for {project_path}")
    
    # Extract all information
    project_info = _extract_project_info(project_path)
    prd = _generate_prd(project_path, project_info)
    design = _generate_design(project_path, project_info)
    plan = _generate_plan(project_path, prd, design)
    
    # Generate SPEC.md content
    spec_content = _build_spec_content(project_info, prd, design, plan)
    
    return spec_content


def _extract_project_info(project_path: str) -> Dict:
    """Extract basic project information."""
    info = {
        'name': os.path.basename(project_path),
        'package': _extract_package_name(project_path),
        'min_sdk': 21,
        'target_sdk': 33,
        'version_name': '1.0',
        'version_code': 1,
        'total_files': 0,
        'total_lines': 0,
        'languages': []
    }
    
    # Extract from AndroidManifest.xml
    manifest_path = os.path.join(project_path, 'app', 'src', 'main', 'AndroidManifest.xml')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            content = f.read()
            
            # Package name
            match = re.search(r'package="([^"]+)"', content)
            if match:
                info['package'] = match.group(1)
            
            # Version info
            version_match = re.search(r'android:versionName="([^"]+)"', content)
            if version_match:
                info['version_name'] = version_match.group(1)
            
            version_code_match = re.search(r'android:versionCode="(\d+)"', content)
            if version_code_match:
                info['version_code'] = int(version_code_match.group(1))
    
    # Extract from build.gradle
    build_gradle = os.path.join(project_path, 'app', 'build.gradle')
    if not os.path.exists(build_gradle):
        build_gradle = os.path.join(project_path, 'app', 'build.gradle.kts')
    
    if os.path.exists(build_gradle):
        with open(build_gradle, 'r') as f:
            content = f.read()
            
            min_match = re.search(r'minSdk(?:Version)?\s*[=]?\s*(\d+)', content)
            if min_match:
                info['min_sdk'] = int(min_match.group(1))
            
            target_match = re.search(r'targetSdk(?:Version)?\s*[=]?\s*(\d+)', content)
            if target_match:
                info['target_sdk'] = int(target_match.group(1))
    
    # Count files and lines
    total_files = 0
    total_lines = 0
    languages = set()
    
    src_dir = os.path.join(project_path, 'app', 'src')
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            if 'build/' in root:
                continue
            
            for file in files:
                if file.endswith(('.kt', '.java', '.xml', '.gradle')):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            total_lines += len(f.readlines())
                    except:
                        pass
                    
                    if file.endswith('.kt'):
                        languages.add('Kotlin')
                    elif file.endswith('.java'):
                        languages.add('Java')
    
    info['total_files'] = total_files
    info['total_lines'] = total_lines
    info['languages'] = list(languages)
    
    return info


def _generate_prd(project_path: str, project_info: Dict) -> PRD:
    """Generate Product Requirements Document by analyzing the app."""
    prd = PRD(
        app_name=project_info['name'],
        package_name=project_info['package'],
        description="",
        features=[],
        data_models=[],
        screens=[],
        user_flows=[]
    )
    
    # Find features by analyzing packages and file names
    features = _detect_features(project_path)
    prd.features = features
    
    # Find data models
    data_models = _find_data_models(project_path)
    prd.data_models = data_models
    
    # Find screens
    screens = _find_screens(project_path)
    prd.screens = screens
    
    # Detect user flows
    user_flows = _detect_user_flows(screens)
    prd.user_flows = user_flows
    
    # Generate description based on features
    if features:
        feature_names = [f.name for f in features[:3]]
        prd.description = f"Android application with {', '.join(feature_names)} functionality"
    
    return prd


def _generate_design(project_path: str, project_info: Dict) -> Design:
    """Generate Architecture Design Document."""
    design = Design(
        architecture_pattern="Unknown",
        architecture_confidence=0.0,
        layers={},
        dependency_graph={},
        patterns_used=[],
        kmp_structure={}
    )
    
    # Detect architecture pattern
    pattern, confidence, patterns = _detect_architecture_pattern(project_path)
    design.architecture_pattern = pattern
    design.architecture_confidence = confidence
    design.patterns_used = patterns
    
    # Organize files by layer
    layers = _organize_by_layers(project_path)
    design.layers = layers
    
    # Build dependency graph
    dep_graph = _build_dependency_graph(project_path)
    design.dependency_graph = dep_graph
    
    # Propose KMP structure
    kmp_structure = _propose_kmp_structure(design, project_info)
    design.kmp_structure = kmp_structure
    
    return design


def _generate_plan(project_path: str, prd: PRD, design: Design) -> MigrationPlan:
    """Generate Detailed Migration Plan."""
    plan = MigrationPlan(
        phases=[],
        file_groups=[],
        dependency_replacements=[],
        expect_actual_requirements=[],
        risk_assessment=[],
        timeline_estimate={}
    )
    
    # Create migration phases
    phases = _create_migration_phases(prd, design)
    plan.phases = phases
    
    # Group files for batch migration
    file_groups = _create_file_groups(design)
    plan.file_groups = file_groups
    
    # Identify dependency replacements
    dep_replacements = _identify_dependency_replacements(project_path)
    plan.dependency_replacements = dep_replacements
    
    # Identify expect/actual requirements
    expect_actual = _identify_expect_actual_requirements(project_path)
    plan.expect_actual_requirements = expect_actual
    
    # Assess risks
    risks = _assess_risks(prd, design)
    plan.risk_assessment = risks
    
    # Estimate timeline
    timeline = _estimate_timeline(design)
    plan.timeline_estimate = timeline
    
    return plan


def _build_spec_content(project_info: Dict, prd: PRD, design: Design, plan: MigrationPlan) -> str:
    """Build the complete SPEC.md content."""
    sections = []
    
    # Header
    sections.append("# KMP Migration Specification")
    sections.append("")
    sections.append(f"**Project:** {project_info['name']}")
    sections.append(f"**Package:** {project_info['package']}")
    sections.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    sections.append(f"**SDK:** {project_info['min_sdk']} - {project_info['target_sdk']}")
    sections.append(f"**Languages:** {', '.join(project_info['languages'])}")
    sections.append(f"**Files:** {project_info['total_files']} ({project_info['total_lines']:,} lines)")
    sections.append("")
    sections.append("---")
    sections.append("")
    
    # PART 1: PRD
    sections.append("# PART 1: PRODUCT REQUIREMENTS DOCUMENT (PRD)")
    sections.append("")
    sections.append("## 1.1 App Overview")
    sections.append("")
    sections.append(f"**App Name:** {prd.app_name}")
    sections.append(f"**Description:** {prd.description}")
    sections.append(f"**Package:** {prd.package_name}")
    sections.append(f"**Version:** {project_info['version_name']} ({project_info['version_code']})")
    sections.append("")
    
    sections.append("## 1.2 Features")
    sections.append("")
    for i, feature in enumerate(prd.features, 1):
        sections.append(f"### Feature {i}: {feature.name}")
        sections.append(f"**Priority:** {feature.priority}")
        sections.append(f"**KMP Impact:** {feature.kmp_impact}")
        sections.append(f"**Description:** {feature.description}")
        if feature.files:
            sections.append("**Files:**")
            for f in feature.files[:5]:
                sections.append(f"- `{f}`")
            if len(feature.files) > 5:
                sections.append(f"- ... and {len(feature.files) - 5} more")
        sections.append("")
    
    sections.append("## 1.3 Data Models")
    sections.append("")
    if prd.data_models:
        sections.append("| Model | Package | Fields | Type |")
        sections.append("|-------|---------|--------|------|")
        for model in prd.data_models[:10]:
            fields_count = len(model.fields)
            model_type = "Room Entity" if model.is_room_entity else "Data Class"
            sections.append(f"| {model.name} | {model.package} | {fields_count} | {model_type} |")
    else:
        sections.append("*No data models detected*")
    sections.append("")
    
    sections.append("## 1.4 Screens")
    sections.append("")
    if prd.screens:
        sections.append("| Screen | Type | ViewModel | Navigation |")
        sections.append("|--------|------|-----------|------------|")
        for screen in prd.screens[:10]:
            nav_count = len(screen.navigation)
            sections.append(f"| {screen.name} | {screen.type} | {screen.viewmodel or 'N/A'} | {nav_count} destinations |")
    else:
        sections.append("*No screens detected*")
    sections.append("")
    
    sections.append("## 1.5 User Flows")
    sections.append("")
    for i, flow in enumerate(prd.user_flows[:5], 1):
        sections.append(f"### Flow {i}: {flow.get('name', 'Unnamed')}")
        if 'steps' in flow:
            for j, step in enumerate(flow['steps'][:5], 1):
                sections.append(f"  {j}. {step}")
        sections.append("")
    
    sections.append("---")
    sections.append("")
    
    # PART 2: DESIGN
    sections.append("# PART 2: ARCHITECTURE DESIGN")
    sections.append("")
    sections.append("## 2.1 Architecture Pattern")
    sections.append("")
    sections.append(f"**Detected Pattern:** {design.architecture_pattern}")
    sections.append(f"**Confidence:** {design.architecture_confidence:.0%}")
    sections.append(f"**Patterns Used:** {', '.join(design.patterns_used) if design.patterns_used else 'None detected'}")
    sections.append("")
    
    sections.append("## 2.2 Layer Structure")
    sections.append("")
    for layer, files in design.layers.items():
        sections.append(f"### {layer}")
        sections.append(f"**Files:** {len(files)}")
        for f in files[:5]:
            sections.append(f"- `{f}`")
        if len(files) > 5:
            sections.append(f"- ... and {len(files) - 5} more")
        sections.append("")
    
    sections.append("## 2.3 Proposed KMP Structure")
    sections.append("")
    for module, purpose in design.kmp_structure.items():
        sections.append(f"### {module}")
        sections.append(f"**Purpose:** {purpose}")
        sections.append("")
    
    sections.append("---")
    sections.append("")
    
    # PART 3: PLAN
    sections.append("# PART 3: MIGRATION PLAN")
    sections.append("")
    
    sections.append("## 3.1 Migration Phases")
    sections.append("")
    for i, phase in enumerate(plan.phases, 1):
        sections.append(f"### Phase {i}: {phase.get('name', 'Unnamed')}")
        sections.append(f"**Duration:** {phase.get('duration', 'TBD')}")
        sections.append(f"**Priority:** {phase.get('priority', 'Normal')}")
        if 'tasks' in phase:
            sections.append("**Tasks:**")
            for task in phase['tasks'][:5]:
                sections.append(f"- [ ] {task}")
        sections.append("")
    
    sections.append("## 3.2 File Groups (Batch Migration)")
    sections.append("")
    for i, group in enumerate(plan.file_groups[:10], 1):
        sections.append(f"### Group {i}: {group.get('name', 'Unnamed')}")
        sections.append(f"**Files:** {len(group.get('files', []))}")
        sections.append(f"**KMP Module:** {group.get('target_module', 'shared')}")
        sections.append("")
    
    sections.append("## 3.3 Dependency Replacements")
    sections.append("")
    if plan.dependency_replacements:
        sections.append("| Android | KMP Alternative | Complexity |")
        sections.append("|---------|-----------------|------------|")
        for dep in plan.dependency_replacements[:10]:
            sections.append(f"| `{dep.get('android', '')}` | `{dep.get('kmp', '')}` | {dep.get('complexity', 'Medium')} |")
    else:
        sections.append("*No dependency replacements needed*")
    sections.append("")
    
    sections.append("## 3.4 Expect/Actual Requirements")
    sections.append("")
    if plan.expect_actual_requirements:
        for req in plan.expect_actual_requirements[:5]:
            sections.append(f"### {req.get('feature', 'Feature')}")
            sections.append(f"**Interface:** `{req.get('interface', 'N/A')}`")
            sections.append(f"**Android:** `{req.get('android_impl', 'N/A')}`")
            sections.append(f"**iOS:** `{req.get('ios_impl', 'TBD')}`")
            sections.append("")
    else:
        sections.append("*No expect/actual requirements detected*")
    sections.append("")
    
    sections.append("## 3.5 Risk Assessment")
    sections.append("")
    if plan.risk_assessment:
        sections.append("| Risk | Impact | Probability | Mitigation |")
        sections.append("|------|--------|-------------|------------|")
        for risk in plan.risk_assessment[:5]:
            sections.append(f"| {risk.get('risk', 'Unknown')} | {risk.get('impact', 'Medium')} | {risk.get('probability', 'Medium')} | {risk.get('mitigation', 'Review')} |")
    else:
        sections.append("*No significant risks identified*")
    sections.append("")
    
    sections.append("## 3.6 Timeline Estimate")
    sections.append("")
    if plan.timeline_estimate:
        sections.append(f"**Total Estimated Effort:** {plan.timeline_estimate.get('total_hours', 'TBD')} hours")
        sections.append(f"**Complexity Score:** {plan.timeline_estimate.get('complexity', 'TBD')}/10")
        sections.append("")
        sections.append("| Phase | Hours | Dependencies |")
        sections.append("|-------|-------|--------------|")
        for phase_name, hours in plan.timeline_estimate.get('phases', {}).items():
            sections.append(f"| {phase_name} | {hours} | - |")
    sections.append("")
    
    sections.append("---")
    sections.append("")
    sections.append("*SPEC.md generated by KMP Migration Framework v3.1*")
    
    return '\n'.join(sections)


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


def _detect_features(project_path: str) -> List[AppFeature]:
    """Detect app features by analyzing code structure."""
    features = []
    
    # Common feature patterns
    feature_patterns = {
        'Authentication': [r'Login', r'Register', r'Auth', r'SignIn', r'SignUp'],
        'Database/Storage': [r'Room', r'DAO', r'Entity', r'Database', r'Repository'],
        'Networking': [r'Retrofit', r'Api', r'HttpClient', r'Network'],
        'Image Loading': [r'Glide', r'Picasso', r'Coil', r'ImageLoader'],
        'Navigation': [r'Navigation', r'NavController', r'NavGraph'],
        'Settings': [r'Settings', r'Preferences', r'Config'],
        'Search': [r'Search', r'Filter', r'Query'],
        'Notifications': [r'Notification', r'Firebase', r'Push'],
        'Analytics': [r'Analytics', r'Tracking', r'FirebaseAnalytics'],
    }
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main', 'java')
    if not os.path.exists(src_dir):
        src_dir = os.path.join(project_path, 'app', 'src', 'main', 'kotlin')
    
    if not os.path.exists(src_dir):
        return features
    
    feature_matches = defaultdict(list)
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for feature_name, patterns in feature_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            feature_matches[feature_name].append(rel_path)
                            break
    
    for feature_name, files in feature_matches.items():
        features.append(AppFeature(
            name=feature_name,
            description=f"{feature_name} functionality detected in codebase",
            files=files[:10],
            priority="high" if len(files) > 5 else "medium",
            kmp_impact="shared" if feature_name in ['Database/Storage', 'Networking'] else "android-only"
        ))
    
    return features


def _find_data_models(project_path: str) -> List[DataModel]:
    """Find data models/entities in the project."""
    models = []
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main', 'java')
    if not os.path.exists(src_dir):
        src_dir = os.path.join(project_path, 'app', 'src', 'main', 'kotlin')
    
    if not os.path.exists(src_dir):
        return models
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for Room Entity
                is_room = '@Entity' in content
                
                # Check for data class
                is_data = 'data class' in content
                
                if is_room or is_data:
                    # Extract class name
                    class_match = re.search(r'(?:data\s+)?class\s+(\w+)', content)
                    if class_match:
                        class_name = class_match.group(1)
                        
                        # Extract fields
                        fields = []
                        field_matches = re.findall(r'val\s+(\w+):\s*\w+', content)
                        fields.extend(field_matches)
                        
                        # Get package
                        package_match = re.search(r'package\s+([\w.]+)', content)
                        package = package_match.group(1) if package_match else 'unknown'
                        
                        models.append(DataModel(
                            name=class_name,
                            package=package,
                            fields=fields[:10],
                            is_room_entity=is_room
                        ))
    
    return models[:20]


def _find_screens(project_path: str) -> List[Screen]:
    """Find UI screens in the project."""
    screens = []
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main', 'java')
    if not os.path.exists(src_dir):
        src_dir = os.path.join(project_path, 'app', 'src', 'main', 'kotlin')
    
    if not os.path.exists(src_dir):
        return screens
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for Activity
                if 'Activity' in file or 'AppCompatActivity' in content:
                    screen_name = file.replace('.kt', '').replace('.java', '')
                    
                    # Find associated ViewModel
                    viewmodel = None
                    vm_match = re.search(r'by\s+viewModels\(\)\s*<\s*(\w+ViewModel)', content)
                    if vm_match:
                        viewmodel = vm_match.group(1)
                    
                    screens.append(Screen(
                        name=screen_name,
                        type='Activity',
                        viewmodel=viewmodel
                    ))
                
                # Check for Fragment
                elif 'Fragment' in file:
                    screen_name = file.replace('.kt', '').replace('.java', '')
                    screens.append(Screen(
                        name=screen_name,
                        type='Fragment'
                    ))
    
    return screens[:20]


def _detect_user_flows(screens: List[Screen]) -> List[Dict]:
    """Detect user flows from screens."""
    flows = []
    
    # Simple flow detection based on screen names
    activity_screens = [s for s in screens if s.type == 'Activity']
    
    if len(activity_screens) >= 2:
        flows.append({
            'name': 'Main Flow',
            'steps': [f"Start at {activity_screens[0].name}"] + 
                    [f"Navigate to {s.name}" for s in activity_screens[1:4]]
        })
    
    return flows


def _detect_architecture_pattern(project_path: str) -> Tuple[str, float, List[str]]:
    """Detect architecture pattern used in project."""
    patterns_found = defaultdict(float)
    pattern_evidence = defaultdict(list)
    
    architecture_indicators = {
        'MVVM': {
            'keywords': ['ViewModel', 'LiveData', 'StateFlow', 'Binding'],
            'weight': 1.0
        },
        'MVI': {
            'keywords': ['Intent', 'State', 'Reducer', 'Store', 'Action'],
            'weight': 1.0
        },
        'Clean Architecture': {
            'keywords': ['domain', 'data', 'presentation', 'usecase', 'UseCase', 'repository'],
            'weight': 1.0
        },
        'MVP': {
            'keywords': ['Presenter', 'View', 'Contract'],
            'weight': 1.0
        }
    }
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return 'Unknown', 0.0, []
    
    for root, dirs, files in os.walk(src_dir):
        if 'test' in root:
            continue
        
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
                for pattern, config in architecture_indicators.items():
                    for keyword in config['keywords']:
                        if keyword.lower() in content:
                            patterns_found[pattern] += config['weight']
                            pattern_evidence[pattern].append(keyword)
    
    if not patterns_found:
        return 'Unknown', 0.0, []
    
    best_pattern = max(patterns_found.keys(), key=lambda k: patterns_found[k])
    total_possible = sum(config['weight'] * len(config['keywords']) 
                        for config in architecture_indicators.values())
    confidence = min(1.0, patterns_found[best_pattern] / total_possible)
    
    patterns_used = [p for p in patterns_found.keys() if patterns_found[p] > 0]
    
    return best_pattern, confidence, patterns_used


def _organize_by_layers(project_path: str) -> Dict[str, List[str]]:
    """Organize files by architectural layer."""
    layers = {
        'Presentation (UI)': [],
        'ViewModel': [],
        'Domain (Use Cases)': [],
        'Data (Repository)': [],
        'Data (Local/Remote)': [],
        'Models': []
    }
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return layers
    
    for root, dirs, files in os.walk(src_dir):
        if 'test' in root:
            continue
        
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            # Categorize by file name and content
            file_lower = file.lower()
            
            if 'activity' in file_lower or 'fragment' in file_lower or 'composable' in file_lower:
                layers['Presentation (UI)'].append(rel_path)
            elif 'viewmodel' in file_lower:
                layers['ViewModel'].append(rel_path)
            elif 'usecase' in file_lower or 'use_case' in file_lower:
                layers['Domain (Use Cases)'].append(rel_path)
            elif 'repository' in file_lower:
                layers['Data (Repository)'].append(rel_path)
            elif 'dao' in file_lower or 'api' in file_lower or 'service' in file_lower:
                layers['Data (Local/Remote)'].append(rel_path)
            elif 'entity' in file_lower or 'model' in file_lower or 'data class' in open(file_path, 'r', encoding='utf-8', errors='ignore').read():
                layers['Models'].append(rel_path)
    
    # Remove empty layers
    layers = {k: v for k, v in layers.items() if v}
    
    return layers


def _build_dependency_graph(project_path: str) -> Dict[str, List[str]]:
    """Build dependency graph between files."""
    dep_graph = {}
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return dep_graph
    
    # Simple implementation - track imports
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Find imports that reference other project files
                imports = re.findall(r'import\s+[\w.]+\.(\w+)', content)
                dep_graph[rel_path] = imports[:10]
    
    return dep_graph


def _propose_kmp_structure(design: Design, project_info: Dict) -> Dict[str, str]:
    """Propose KMP project structure."""
    structure = {
        'shared/': 'Shared code across all platforms',
        'shared/src/commonMain/': 'Common Kotlin code (business logic, models, repositories)',
        'shared/src/androidMain/': 'Android-specific implementations',
        'shared/src/iosMain/': 'iOS-specific implementations',
        'shared/src/desktopMain/': 'Desktop-specific implementations (optional)',
        'androidApp/': 'Android application module (UI layer)',
        'iosApp/': 'iOS application (to be created)'
    }
    
    # Add specific recommendations based on detected layers
    if 'ViewModel' in design.layers:
        structure['shared/src/commonMain/viewmodel/'] = 'Shared ViewModels using Kotlin Flow'
    
    if 'Data (Repository)' in design.layers:
        structure['shared/src/commonMain/data/'] = 'Repository interfaces and implementations'
    
    if 'Models' in design.layers:
        structure['shared/src/commonMain/model/'] = 'Data classes and entities'
    
    return structure


def _create_migration_phases(prd: PRD, design: Design) -> List[Dict]:
    """Create migration phases."""
    phases = [
        {
            'name': 'Setup & Foundation',
            'duration': '4-8 hours',
            'priority': 'Critical',
            'tasks': [
                'Create KMP project structure',
                'Configure shared module build.gradle.kts',
                'Set up androidApp module',
                'Configure iOS target (optional)',
                'Add KMP-compatible dependencies'
            ]
        },
        {
            'name': 'Data Layer Migration',
            'duration': '8-16 hours',
            'priority': 'High',
            'tasks': [
                'Migrate data models to commonMain',
                'Replace Room with SQLDelight',
                'Migrate repositories to commonMain',
                'Create expect/actual for platform data sources'
            ]
        },
        {
            'name': 'Domain Layer Migration',
            'duration': '4-8 hours',
            'priority': 'High',
            'tasks': [
                'Migrate use cases to commonMain',
                'Replace LiveData with StateFlow',
                'Ensure all business logic is platform-agnostic'
            ]
        },
        {
            'name': 'ViewModel Migration',
            'duration': '8-16 hours',
            'priority': 'Medium',
            'tasks': [
                'Migrate ViewModels to commonMain',
                'Replace Android-specific ViewModel with shared implementation',
                'Update UI observers to use Flow'
            ]
        },
        {
            'name': 'UI Layer',
            'duration': '16-40 hours',
            'priority': 'Medium',
            'tasks': [
                'Keep Android UI in androidApp module',
                'Consider Compose Multiplatform for shared UI',
                'Create iOS UI (if targeting iOS)'
            ]
        },
        {
            'name': 'Testing & Validation',
            'duration': '8-16 hours',
            'priority': 'High',
            'tasks': [
                'Migrate unit tests to commonTest',
                'Keep instrumented tests in androidTest',
                'Validate all features work correctly',
                'Performance testing'
            ]
        }
    ]
    
    return phases


def _create_file_groups(design: Design) -> List[Dict]:
    """Create file groups for batch migration."""
    groups = []
    
    for i, (layer, files) in enumerate(design.layers.items(), 1):
        target_module = 'shared/src/commonMain/kotlin'
        if 'UI' in layer:
            target_module = 'androidApp/src/main/java'
        
        groups.append({
            'name': layer,
            'files': files,
            'target_module': target_module,
            'batch_size': min(10, len(files))
        })
    
    return groups


def _identify_dependency_replacements(project_path: str) -> List[Dict]:
    """Identify dependencies that need replacement."""
    replacements = []
    
    kmp_mappings = {
        'androidx.room:room-runtime': {
            'kmp': 'app.cash.sqldelight:runtime',
            'complexity': 'High'
        },
        'androidx.lifecycle:lifecycle-viewmodel-ktx': {
            'kmp': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
            'complexity': 'Medium'
        },
        'androidx.lifecycle:lifecycle-livedata-ktx': {
            'kmp': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
            'complexity': 'Medium'
        },
        'com.squareup.retrofit2:retrofit': {
            'kmp': 'io.ktor:ktor-client-core',
            'complexity': 'High'
        },
        'com.google.code.gson:gson': {
            'kmp': 'org.jetbrains.kotlinx:kotlinx-serialization-json',
            'complexity': 'Medium'
        }
    }
    
    # Parse build.gradle for dependencies
    build_gradle = os.path.join(project_path, 'app', 'build.gradle')
    if not os.path.exists(build_gradle):
        build_gradle = os.path.join(project_path, 'app', 'build.gradle.kts')
    
    if os.path.exists(build_gradle):
        with open(build_gradle, 'r') as f:
            content = f.read()
            
            for android_dep, info in kmp_mappings.items():
                if android_dep in content:
                    replacements.append({
                        'android': android_dep,
                        'kmp': info['kmp'],
                        'complexity': info['complexity']
                    })
    
    return replacements


def _identify_expect_actual_requirements(project_path: str) -> List[Dict]:
    """Identify code that needs expect/actual implementation."""
    requirements = []
    
    src_dir = os.path.join(project_path, 'app', 'src', 'main')
    if not os.path.exists(src_dir):
        return requirements
    
    # Common expect/actual candidates
    candidates = {
        'Database': {
            'interface': 'DatabaseProvider',
            'android': 'Room implementation',
            'ios': 'SQLDelight implementation'
        },
        'Preferences': {
            'interface': 'PreferencesStore',
            'android': 'SharedPreferences',
            'ios': 'UserDefaults'
        },
        'Network': {
            'interface': 'HttpClientEngine',
            'android': 'OkHttp engine',
            'ios': 'Darwin engine'
        },
        'File System': {
            'interface': 'FileSystem',
            'android': 'Android file API',
            'ios': 'iOS file API'
        }
    }
    
    # Check which ones are used
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.kt', '.java')):
                continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for feature, info in candidates.items():
                    if feature.lower() in content.lower() or \
                       'SharedPreferences' in content or \
                       'Room' in content or \
                       'OkHttp' in content:
                        
                        if feature not in [r.get('feature') for r in requirements]:
                            requirements.append({
                                'feature': feature,
                                'interface': info['interface'],
                                'android_impl': info['android'],
                                'ios_impl': info['ios']
                            })
    
    return requirements


def _assess_risks(prd: PRD, design: Design) -> List[Dict]:
    """Assess migration risks."""
    risks = []
    
    # Risk: Complex architecture
    if design.architecture_pattern == 'Unknown':
        risks.append({
            'risk': 'Unknown architecture pattern',
            'impact': 'High',
            'probability': 'High',
            'mitigation': 'Refactor to clear architecture before migration'
        })
    
    # Risk: Many dependencies
    dep_count = sum(len(files) for files in design.layers.values())
    if dep_count > 50:
        risks.append({
            'risk': 'Large codebase',
            'impact': 'Medium',
            'probability': 'High',
            'mitigation': 'Migrate in small batches, test frequently'
        })
    
    # Risk: Android-only features
    android_only_features = [f for f in prd.features if f.kmp_impact == 'android-only']
    if len(android_only_features) > 3:
        risks.append({
            'risk': 'Many Android-specific features',
            'impact': 'Medium',
            'probability': 'Medium',
            'mitigation': 'Keep in androidApp module, use expect/actual'
        })
    
    # Risk: Room database
    has_room = any(m.is_room_entity for m in prd.data_models)
    if has_room:
        risks.append({
            'risk': 'Room database migration to SQLDelight',
            'impact': 'High',
            'probability': 'High',
            'mitigation': 'Plan schema migration carefully, test data integrity'
        })
    
    return risks


def _estimate_timeline(design: Design) -> Dict:
    """Estimate migration timeline."""
    total_files = sum(len(files) for files in design.layers.values())
    
    # Base estimate: 2 hours per file
    base_hours = total_files * 2
    
    # Complexity multiplier
    complexity = min(10, max(1, total_files // 10))
    multiplier = 1.0 + (complexity / 10)
    
    total_hours = base_hours * multiplier
    
    # Phase breakdown
    phases = {
        'Setup': round(total_hours * 0.1),
        'Data Layer': round(total_hours * 0.25),
        'Domain Layer': round(total_hours * 0.15),
        'ViewModel': round(total_hours * 0.2),
        'UI Layer': round(total_hours * 0.2),
        'Testing': round(total_hours * 0.1)
    }
    
    return {
        'total_hours': round(total_hours, 1),
        'complexity': complexity,
        'phases': phases
    }


# Main function
def generate_spec_md(project_path: str, output_path: Optional[str] = None):
    """Generate comprehensive SPEC.md for Android project."""
    spec_content = generate_comprehensive_spec(project_path)
    
    if output_path is None:
        output_path = os.path.join(project_path, 'SPEC.md')
    
    with open(output_path, 'w') as f:
        f.write(spec_content)
    
    logger.info(f"SPEC.md generated at {output_path}")
    print(f"✓ SPEC.md generated successfully at {output_path}")
    print(f"  Size: {len(spec_content)} characters")
    
    return spec_content
