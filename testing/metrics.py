import os
import json
import time
import subprocess
import re
from datetime import datetime

class TestingMetrics:
    """Collects traditional code quality and testing metrics."""
    
    def __init__(self, project_path, migrated_project_path):
        self.project_path = project_path
        self.migrated_project_path = migrated_project_path
        self.metrics = {}
    
    def collect_all_metrics(self):
        """Collect all traditional metrics."""
        print("\n--- Collecting Traditional Metrics ---")
        
        self.metrics['compilation'] = self.check_compilation()
        self.metrics['code_stats'] = self.analyze_code_statistics()
        self.metrics['test_coverage'] = self.estimate_test_coverage()
        self.metrics['dependency_check'] = self.check_dependencies()
        self.metrics['code_complexity'] = self.analyze_complexity()
        self.metrics['platform_compatibility'] = self.check_platform_compatibility()
        
        return self.metrics
    
    def check_compilation(self):
        """Check if the KMP project compiles successfully."""
        result = {
            'status': 'unknown',
            'errors': [],
            'warnings': [],
            'compile_time_seconds': 0
        }
        
        try:
            start_time = time.time()
            # Run Gradle compile
            proc = subprocess.run(
                ['./gradlew', 'compileKotlinMetadata'],
                cwd=self.migrated_project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            elapsed = time.time() - start_time
            result['compile_time_seconds'] = elapsed
            
            if proc.returncode == 0:
                result['status'] = 'success'
            else:
                result['status'] = 'failed'
                result['errors'] = proc.stderr.split('\n')[:10]
                result['warnings'] = proc.stdout.split('\n')[:10]
                
        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
            result['errors'] = ['Compilation timed out after 300 seconds']
        except FileNotFoundError:
            result['status'] = 'gradle_not_found'
            result['errors'] = ['Gradle wrapper not found']
        except Exception as e:
            result['status'] = 'error'
            result['errors'] = [str(e)]
        
        return result
    
    def analyze_code_statistics(self):
        """Analyze code statistics (LOC, files, classes, functions)."""
        stats = {
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'files': 0,
            'classes': 0,
            'functions': 0,
            'kotlin_files': 0,
            'java_files': 0
        }
        
        for root, dirs, files in os.walk(self.migrated_project_path):
            for file in files:
                if file.endswith(('.kt', '.java')):
                    stats['files'] += 1
                    if file.endswith('.kt'):
                        stats['kotlin_files'] += 1
                    else:
                        stats['java_files'] += 1
                    
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        stats['total_lines'] += len(lines)
                        
                        for line in lines:
                            stripped = line.strip()
                            if stripped.startswith('//') or stripped.startswith('/*'):
                                stats['comment_lines'] += 1
                            elif stripped == '':
                                stats['blank_lines'] += 1
                            else:
                                stats['code_lines'] += 1
                        
                        # Count classes and functions
                        stats['classes'] += len(re.findall(r'\b(class|object|interface)\s+\w+', content))
                        stats['functions'] += len(re.findall(r'\bfun\s+\w+', content))
        
        return stats
    
    def estimate_test_coverage(self):
        """Estimate test coverage based on test file presence."""
        coverage = {
            'unit_tests': 0,
            'instrumented_tests': 0,
            'total_test_files': 0,
            'estimated_coverage_percent': 0
        }
        
        test_dirs = ['src/test', 'src/androidTest', 'src/commonTest']
        
        for test_dir in test_dirs:
            full_path = os.path.join(self.migrated_project_path, 'shared', test_dir)
            if os.path.exists(full_path):
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        if file.endswith(('.kt', '.java')):
                            coverage['total_test_files'] += 1
                            if 'androidTest' in test_dir:
                                coverage['instrumented_tests'] += 1
                            else:
                                coverage['unit_tests'] += 1
        
        # Simple estimation based on test-to-source ratio
        source_files = self.analyze_code_statistics()['files']
        if source_files > 0:
            coverage['estimated_coverage_percent'] = min(
                100, 
                (coverage['total_test_files'] / source_files) * 100
            )
        
        return coverage
    
    def check_dependencies(self):
        """Check if all dependencies are KMP-compatible."""
        result = {
            'total_dependencies': 0,
            'kmp_compatible': 0,
            'android_only': 0,
            'unknown': 0,
            'dependencies': []
        }
        
        # Known KMP-compatible libraries
        kmp_libs = [
            'ktor', 'kotlinx.coroutines', 'kotlinx.serialization',
            'sqldelight', 'koin', 'kodein', 'napier', 'kotlinx.datetime',
            'multiplatform-settings', 'kermit', 'kotlinx.collections'
        ]
        
        # Android-only libraries (need replacement)
        android_only_libs = [
            'androidx.appcompat', 'androidx.activity', 'androidx.fragment',
            'androidx.recyclerview', 'com.google.android.material',
            'androidx.constraintlayout', 'androidx.cardview'
        ]
        
        gradle_files = []
        for root, dirs, files in os.walk(self.migrated_project_path):
            for file in files:
                if file.endswith(('.gradle', '.gradle.kts')):
                    gradle_files.append(os.path.join(root, file))
        
        for gradle_file in gradle_files:
            with open(gradle_file, 'r') as f:
                content = f.read()
                deps = re.findall(r'implementation\s*\(\s*["\']([^"\']+)["\']', content)
                
                for dep in deps:
                    result['total_dependencies'] += 1
                    dep_lower = dep.lower()
                    
                    if any(lib in dep_lower for lib in kmp_libs):
                        result['kmp_compatible'] += 1
                        status = 'kmp_compatible'
                    elif any(lib in dep_lower for lib in android_only_libs):
                        result['android_only'] += 1
                        status = 'android_only'
                    else:
                        result['unknown'] += 1
                        status = 'unknown'
                    
                    result['dependencies'].append({
                        'name': dep,
                        'status': status
                    })
        
        return result
    
    def analyze_complexity(self):
        """Analyze code complexity metrics."""
        complexity = {
            'average_function_length': 0,
            'max_function_length': 0,
            'functions_over_50_lines': 0,
            'cyclomatic_estimate': 0,
            'deep_nesting_count': 0
        }
        
        total_function_length = 0
        function_count = 0
        
        for root, dirs, files in os.walk(self.migrated_project_path):
            for file in files:
                if file.endswith(('.kt', '.java')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Find function bodies (simplified)
                        functions = re.findall(r'fun\s+\w+\s*\([^)]*\)\s*\{([^}]+)\}', content, re.DOTALL)
                        
                        for func in functions:
                            lines = func.strip().split('\n')
                            func_length = len(lines)
                            total_function_length += func_length
                            function_count += 1
                            
                            if func_length > 50:
                                complexity['functions_over_50_lines'] += 1
                            if func_length > complexity['max_function_length']:
                                complexity['max_function_length'] = func_length
                            
                            # Estimate cyclomatic complexity (branches)
                            complexity['cyclomatic_estimate'] += len(re.findall(r'\b(if|when|for|while|catch|&&|\|\|)\b', func))
                            
                            # Count deep nesting (4+ levels)
                            if re.search(r'(\s{8,}|\t{4,}){4,}', func):
                                complexity['deep_nesting_count'] += 1
        
        if function_count > 0:
            complexity['average_function_length'] = total_function_length / function_count
        
        return complexity
    
    def check_platform_compatibility(self):
        """Check platform-specific code separation."""
        compatibility = {
            'common_code_percent': 0,
            'android_specific': 0,
            'ios_specific': 0,
            'desktop_specific': 0,
            'expect_actual_pairs': 0,
            'platform_issues': []
        }
        
        source_sets = {
            'commonMain': 0,
            'androidMain': 0,
            'iosMain': 0,
            'desktopMain': 0
        }
        
        for source_set in source_sets.keys():
            path = os.path.join(self.migrated_project_path, 'shared', 'src', source_set)
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    source_sets[source_set] += len([f for f in files if f.endswith(('.kt', '.java'))])
        
        total_files = sum(source_sets.values())
        if total_files > 0:
            compatibility['common_code_percent'] = (source_sets['commonMain'] / total_files) * 100
        
        compatibility['android_specific'] = source_sets['androidMain']
        compatibility['ios_specific'] = source_sets['iosMain']
        compatibility['desktop_specific'] = source_sets['desktopMain']
        
        # Count expect/actual pairs
        for root, dirs, files in os.walk(os.path.join(self.migrated_project_path, 'shared', 'src')):
            for file in files:
                if file.endswith('.kt'):
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read()
                        compatibility['expect_actual_pairs'] += min(
                            len(re.findall(r'\bexpect\b', content)),
                            len(re.findall(r'\bactual\b', content))
                        )
        
        return compatibility
    
    def generate_report(self):
        """Generate a comprehensive metrics report."""
        report = f"""
# Traditional Testing Metrics Report

Generated: {datetime.now().isoformat()}

## Compilation Status
- **Status:** {self.metrics.get('compilation', {}).get('status', 'N/A')}
- **Compile Time:** {self.metrics.get('compilation', {}).get('compile_time_seconds', 0):.2f}s
- **Errors:** {len(self.metrics.get('compilation', {}).get('errors', []))}
- **Warnings:** {len(self.metrics.get('compilation', {}).get('warnings', []))}

## Code Statistics
- **Total Lines:** {self.metrics.get('code_stats', {}).get('total_lines', 0)}
- **Code Lines:** {self.metrics.get('code_stats', {}).get('code_lines', 0)}
- **Comment Lines:** {self.metrics.get('code_stats', {}).get('comment_lines', 0)}
- **Files:** {self.metrics.get('code_stats', {}).get('files', 0)}
- **Kotlin Files:** {self.metrics.get('code_stats', {}).get('kotlin_files', 0)}
- **Java Files:** {self.metrics.get('code_stats', {}).get('java_files', 0)}
- **Classes:** {self.metrics.get('code_stats', {}).get('classes', 0)}
- **Functions:** {self.metrics.get('code_stats', {}).get('functions', 0)}

## Test Coverage Estimate
- **Unit Tests:** {self.metrics.get('test_coverage', {}).get('unit_tests', 0)}
- **Instrumented Tests:** {self.metrics.get('test_coverage', {}).get('instrumented_tests', 0)}
- **Total Test Files:** {self.metrics.get('test_coverage', {}).get('total_test_files', 0)}
- **Estimated Coverage:** {self.metrics.get('test_coverage', {}).get('estimated_coverage_percent', 0):.1f}%

## Dependency Analysis
- **Total Dependencies:** {self.metrics.get('dependency_check', {}).get('total_dependencies', 0)}
- **KMP Compatible:** {self.metrics.get('dependency_check', {}).get('kmp_compatible', 0)}
- **Android Only:** {self.metrics.get('dependency_check', {}).get('android_only', 0)}
- **Unknown:** {self.metrics.get('dependency_check', {}).get('unknown', 0)}

## Code Complexity
- **Average Function Length:** {self.metrics.get('code_complexity', {}).get('average_function_length', 0):.1f} lines
- **Max Function Length:** {self.metrics.get('code_complexity', {}).get('max_function_length', 0)} lines
- **Functions Over 50 Lines:** {self.metrics.get('code_complexity', {}).get('functions_over_50_lines', 0)}
- **Estimated Cyclomatic Complexity:** {self.metrics.get('code_complexity', {}).get('cyclomatic_estimate', 0)}
- **Deep Nesting Issues:** {self.metrics.get('code_complexity', {}).get('deep_nesting_count', 0)}

## Platform Compatibility
- **Common Code:** {self.metrics.get('platform_compatibility', {}).get('common_code_percent', 0):.1f}%
- **Android Specific Files:** {self.metrics.get('platform_compatibility', {}).get('android_specific', 0)}
- **iOS Specific Files:** {self.metrics.get('platform_compatibility', {}).get('ios_specific', 0)}
- **Desktop Specific Files:** {self.metrics.get('platform_compatibility', {}).get('desktop_specific', 0)}
- **Expect/Actual Pairs:** {self.metrics.get('platform_compatibility', {}).get('expect_actual_pairs', 0)}

## Overall Score
"""
        
        # Calculate overall score
        score = 0
        max_score = 100
        
        # Compilation (25 points)
        if self.metrics.get('compilation', {}).get('status') == 'success':
            score += 25
        
        # Test coverage (25 points)
        coverage = self.metrics.get('test_coverage', {}).get('estimated_coverage_percent', 0)
        score += min(25, coverage * 0.25)
        
        # KMP dependencies (25 points)
        total_deps = self.metrics.get('dependency_check', {}).get('total_dependencies', 1)
        kmp_deps = self.metrics.get('dependency_check', {}).get('kmp_compatible', 0)
        score += min(25, (kmp_deps / max(total_deps, 1)) * 25)
        
        # Common code ratio (25 points)
        common_ratio = self.metrics.get('platform_compatibility', {}).get('common_code_percent', 0)
        score += min(25, common_ratio * 0.25)
        
        report += f"\n**Total Score: {score:.1f}/{max_score}**\n"
        
        return report
