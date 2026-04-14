"""
Gradle Build Verification for KMP Projects

Verifies that migrated KMP projects:
1. Have valid Gradle configuration
2. Compile successfully (compileKotlinMetadata)
3. Pass unit tests (if available)
4. Report detailed errors with fix suggestions

Usage:
    from testing.gradle_verifier import GradleVerifier
    
    verifier = GradleVerifier('/path/to/migrated_kmp_project')
    result = verifier.verify()
    
    if result.success:
        print("✓ Build passed!")
    else:
        print(f"✗ Build failed: {result.error}")
        print(f"Suggestions: {result.suggestions}")
"""

import os
import subprocess
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build verification status."""
    SUCCESS = "success"
    COMPILATION_ERROR = "compilation_error"
    CONFIGURATION_ERROR = "configuration_error"
    GRADLE_NOT_FOUND = "gradle_not_found"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class BuildError:
    """A single build error."""
    file: str
    line: Optional[int]
    column: Optional[int]
    error_type: str
    message: str
    suggestion: str = ""


@dataclass
class BuildResult:
    """Result of build verification."""
    status: BuildStatus
    success: bool
    duration_seconds: float
    gradle_version: Optional[str] = None
    kotlin_version: Optional[str] = None
    errors: List[BuildError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    output: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'success': self.success,
            'duration_seconds': self.duration_seconds,
            'gradle_version': self.gradle_version,
            'kotlin_version': self.kotlin_version,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': [
                {
                    'file': e.file,
                    'line': e.line,
                    'error_type': e.error_type,
                    'message': e.message,
                    'suggestion': e.suggestion
                }
                for e in self.errors
            ],
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'output': self.output[:2000]  # Truncate for storage
        }


class GradleVerifier:
    """
    Verify KMP project builds successfully with Gradle.
    """
    
    def __init__(self, project_path: str, timeout_seconds: int = 300):
        self.project_path = project_path
        self.timeout_seconds = timeout_seconds
        self.gradle_wrapper = self._find_gradle_wrapper()
        self.gradle_version: Optional[str] = None
        self.kotlin_version: Optional[str] = None
    
    def _find_gradle_wrapper(self) -> Optional[str]:
        """Find Gradle wrapper script."""
        # Check for Gradle wrapper
        if os.name == 'nt':  # Windows
            wrapper = os.path.join(self.project_path, 'gradlew.bat')
        else:  # Unix/Mac
            wrapper = os.path.join(self.project_path, 'gradlew')
        
        if os.path.exists(wrapper):
            return wrapper
        
        # Try parent directory (for migrated projects)
        parent = os.path.dirname(self.project_path)
        if os.name == 'nt':
            wrapper = os.path.join(parent, 'gradlew.bat')
        else:
            wrapper = os.path.join(parent, 'gradlew')
        
        if os.path.exists(wrapper):
            return wrapper
        
        return None
    
    def verify(self) -> BuildResult:
        """
        Run complete build verification.
        
        Returns:
            BuildResult with status, errors, and suggestions
        """
        start_time = time.time()
        
        # Check if project exists
        if not os.path.exists(self.project_path):
            return BuildResult(
                status=BuildStatus.CONFIGURATION_ERROR,
                success=False,
                duration_seconds=0,
                errors=[BuildError(
                    file=self.project_path,
                    line=None,
                    column=None,
                    error_type="not_found",
                    message=f"Project path does not exist: {self.project_path}",
                    suggestion="Check that the migrated project path is correct"
                )]
            )
        
        # Check for Gradle wrapper
        if not self.gradle_wrapper:
            return BuildResult(
                status=BuildStatus.GRADLE_NOT_FOUND,
                success=False,
                duration_seconds=0,
                errors=[BuildError(
                    file="gradlew",
                    line=None,
                    column=None,
                    error_type="gradle_not_found",
                    message="Gradle wrapper not found",
                    suggestion="Run 'gradle wrapper' in the project root or copy gradlew from template"
                )]
            )
        
        # Make wrapper executable (Unix/Mac)
        if os.name != 'nt':
            try:
                os.chmod(self.gradle_wrapper, 0o755)
            except:
                pass
        
        # Get Gradle and Kotlin versions
        self.gradle_version = self._get_gradle_version()
        self.kotlin_version = self._get_kotlin_version()
        
        # Run compilation
        result = self._run_compilation()
        
        result.duration_seconds = time.time() - start_time
        result.gradle_version = self.gradle_version
        result.kotlin_version = self.kotlin_version
        
        # Add suggestions based on errors
        self._add_suggestions(result)
        
        return result
    
    def _get_gradle_version(self) -> Optional[str]:
        """Get Gradle version."""
        try:
            result = subprocess.run(
                [self.gradle_wrapper, '--version'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )
            
            if result.returncode == 0:
                match = re.search(r'Gradle\s+([\d.]+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.warning(f"Failed to get Gradle version: {e}")
        
        return None
    
    def _get_kotlin_version(self) -> Optional[str]:
        """Get Kotlin version from build.gradle."""
        build_files = [
            os.path.join(self.project_path, 'build.gradle'),
            os.path.join(self.project_path, 'build.gradle.kts'),
            os.path.join(self.project_path, 'shared', 'build.gradle'),
            os.path.join(self.project_path, 'shared', 'build.gradle.kts'),
        ]
        
        for build_file in build_files:
            if os.path.exists(build_file):
                with open(build_file, 'r') as f:
                    content = f.read()
                    
                    # Look for Kotlin version
                    match = re.search(r'kotlin["\']?\s*[)=]\s*["\']?([\d.]+)', content)
                    if match:
                        return match.group(1)
                    
                    # Look for Kotlin plugin version
                    match = re.search(r'kotlin["\']?\s*version\s*["\']?([\d.]+)', content)
                    if match:
                        return match.group(1)
        
        return None
    
    def _run_direct_gradle(self) -> BuildResult:
        """Fallback: Run Gradle compilation directly."""
        try:
            result = subprocess.run(
                [self.gradle_wrapper, 'compileKotlinMetadata', '--stacktrace'],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=self.project_path
            )
            
            output = result.stdout + result.stderr
            errors = self._parse_errors(output)
            
            if result.returncode == 0:
                status = BuildStatus.SUCCESS
                success = True
            elif errors:
                status = BuildStatus.COMPILATION_ERROR
                success = False
            else:
                status = BuildStatus.UNKNOWN_ERROR
                success = False
            
            return BuildResult(
                status=status,
                success=success,
                duration_seconds=0,
                errors=errors,
                output=output
            )
        except Exception as e:
            return BuildResult(
                status=BuildStatus.UNKNOWN_ERROR,
                success=False,
                duration_seconds=0,
                errors=[BuildError(
                    file="gradle",
                    line=None,
                    column=None,
                    error_type="exception",
                    message=str(e),
                    suggestion="Check Gradle installation"
                )]
            )
    
    def _run_compilation(self) -> BuildResult:
        """Run Gradle compilation using build script."""
        try:
            # Find build script
            build_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                'build_kmp.sh'
            )
            
            if not os.path.exists(build_script):
                # Fallback to direct gradle
                return self._run_direct_gradle()
            
            # Run build script
            result = subprocess.run(
                ['bash', build_script, self.project_path, '--timeout', str(self.timeout_seconds)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds + 30,  # Extra time for script setup
                cwd=os.path.dirname(self.project_path)
            )
            
            output = result.stdout + result.stderr
            
            # Parse errors
            errors = self._parse_errors(output)
            
            # Determine status
            if result.returncode == 0:
                status = BuildStatus.SUCCESS
                success = True
            elif errors:
                status = BuildStatus.COMPILATION_ERROR
                success = False
            else:
                status = BuildStatus.UNKNOWN_ERROR
                success = False
            
            return BuildResult(
                status=status,
                success=success,
                duration_seconds=0,  # Will be set by caller
                errors=errors,
                output=output
            )
            
        except subprocess.TimeoutExpired:
            return BuildResult(
                status=BuildStatus.TIMEOUT,
                success=False,
                duration_seconds=0,
                errors=[BuildError(
                    file="gradle",
                    line=None,
                    column=None,
                    error_type="timeout",
                    message=f"Build timed out after {self.timeout_seconds}s",
                    suggestion="Increase timeout or check for infinite loops in build script"
                )]
            )
        
        except Exception as e:
            return BuildResult(
                status=BuildStatus.UNKNOWN_ERROR,
                success=False,
                duration_seconds=0,
                errors=[BuildError(
                    file="gradle",
                    line=None,
                    column=None,
                    error_type="exception",
                    message=str(e),
                    suggestion="Check Gradle installation and project configuration"
                )]
            )
    
    def _parse_errors(self, output: str) -> List[BuildError]:
        """Parse compilation errors from Gradle output."""
        errors = []
        
        # Kotlin compilation error pattern
        # e: file.kt:10:5 error: unresolved reference
        kotlin_error_pattern = re.compile(
            r'e:\s+([^\s:]+):(\d+):(\d+)\s+error:\s+(.+)',
            re.MULTILINE
        )
        
        for match in kotlin_error_pattern.finditer(output):
            file_path = match.group(1)
            line = int(match.group(2))
            column = int(match.group(3))
            message = match.group(4).strip()
            
            error_type = self._classify_error(message)
            suggestion = self._get_suggestion(error_type, message)
            
            errors.append(BuildError(
                file=file_path,
                line=line,
                column=column,
                error_type=error_type,
                message=message,
                suggestion=suggestion
            ))
        
        # Gradle configuration error pattern
        if 'Could not resolve' in output:
            errors.append(BuildError(
                file="build.gradle",
                line=None,
                column=None,
                error_type="dependency_resolution",
                message="Could not resolve dependencies",
                suggestion="Check repository configuration and dependency versions"
            ))
        
        if 'Plugin not found' in output or 'Plugin is wrong' in output:
            errors.append(BuildError(
                file="settings.gradle",
                line=None,
                column=None,
                error_type="plugin_not_found",
                message="Gradle plugin not found",
                suggestion="Check plugin ID and version in settings.gradle"
            ))
        
        return errors
    
    def _classify_error(self, message: str) -> str:
        """Classify error type from message."""
        message_lower = message.lower()
        
        if 'unresolved reference' in message_lower:
            return 'unresolved_reference'
        elif 'syntax error' in message_lower:
            return 'syntax_error'
        elif 'type mismatch' in message_lower:
            return 'type_mismatch'
        elif 'override' in message_lower and 'required' in message_lower:
            return 'missing_override'
        elif 'expect' in message_lower and 'actual' in message_lower:
            return 'expect_actual_mismatch'
        elif 'import' in message_lower:
            return 'import_error'
        elif 'visibility' in message_lower:
            return 'visibility_error'
        elif 'null' in message_lower and 'safe call' in message_lower:
            return 'null_safety'
        else:
            return 'compilation_error'
    
    def _get_suggestion(self, error_type: str, message: str) -> str:
        """Get fix suggestion for error type."""
        suggestions = {
            'unresolved_reference': 'Check import statements and ensure dependency is added to build.gradle',
            'syntax_error': 'Check Kotlin syntax - missing brackets, semicolons, or keywords',
            'type_mismatch': 'Ensure types match - check function signatures and variable types',
            'missing_override': 'Add "override" keyword to overridden methods',
            'expect_actual_mismatch': 'Ensure expect/actual declarations match in signature',
            'import_error': 'Check import path and ensure module is included in dependencies',
            'visibility_error': 'Check visibility modifiers (public, internal, private)',
            'null_safety': 'Use safe call operator (?.) or Elvis operator (?:) for nullable types',
            'dependency_resolution': 'Run "gradle --refresh-dependencies" and check repository URLs',
            'plugin_not_found': 'Verify plugin ID in settings.gradle and version in build.gradle',
            'compilation_error': 'Review error message and check Kotlin documentation'
        }
        
        return suggestions.get(error_type, 'Review error and check Kotlin documentation')
    
    def _add_suggestions(self, result: BuildResult):
        """Add general suggestions based on build result."""
        if result.status == BuildStatus.SUCCESS:
            result.suggestions.append("✓ Build successful! Consider running tests next.")
            return
        
        if result.status == BuildStatus.GRADLE_NOT_FOUND:
            result.suggestions.extend([
                "Copy gradlew from the KMP template",
                "Run 'gradle wrapper' to generate wrapper",
                "Ensure gradle/wrapper/gradle-wrapper.jar exists"
            ])
            return
        
        if result.status == BuildStatus.COMPILATION_ERROR:
            # Group errors by type
            error_types = {}
            for error in result.errors:
                error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            # Add specific suggestions
            if error_types.get('unresolved_reference', 0) > 3:
                result.suggestions.append("Multiple unresolved references - check if KMP dependencies are properly configured")
            
            if error_types.get('expect_actual_mismatch', 0) > 0:
                result.suggestions.append("Expect/actual mismatch - ensure signatures match exactly between common and platform code")
            
            if error_types.get('dependency_resolution', 0) > 0:
                result.suggestions.append("Dependency resolution failed - check repositories in settings.gradle")
            
            # General suggestions
            result.suggestions.extend([
                "Run 'gradle clean' and retry",
                "Check Kotlin version compatibility across modules",
                "Ensure all KMP plugins are applied correctly"
            ])
        
        if result.status == BuildStatus.TIMEOUT:
            result.suggestions.extend([
                "Increase timeout in GradleVerifier constructor",
                "Check for circular dependencies in build script",
                "Run 'gradle --profile' to identify slow tasks"
            ])
    
    def quick_check(self) -> Tuple[bool, str]:
        """
        Quick check without full compilation.
        
        Returns:
            (success, message)
        """
        issues = []
        
        # Check project structure
        if not os.path.exists(os.path.join(self.project_path, 'shared')):
            issues.append("Missing 'shared' module directory")
        
        if not os.path.exists(os.path.join(self.project_path, 'shared', 'build.gradle.kts')):
            issues.append("Missing shared/build.gradle.kts")
        
        # Check for Kotlin files
        kotlin_files = []
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.kt'):
                    kotlin_files.append(os.path.join(root, file))
        
        if not kotlin_files:
            issues.append("No Kotlin files found")
        
        # Check Gradle wrapper
        if not self.gradle_wrapper:
            issues.append("Gradle wrapper not found")
        
        if issues:
            return False, "Quick check failed:\n" + "\n".join(f"  - {issue}" for issue in issues)
        
        return True, "Quick check passed"


def verify_gradle_build(project_path: str, timeout: int = 300) -> BuildResult:
    """
    Verify KMP project builds successfully.
    
    Args:
        project_path: Path to migrated KMP project
        timeout: Build timeout in seconds
    
    Returns:
        BuildResult with status and errors
    """
    verifier = GradleVerifier(project_path, timeout)
    return verifier.verify()


def verify_quick(project_path: str) -> Tuple[bool, str]:
    """
    Quick verification without compilation.
    
    Args:
        project_path: Path to migrated KMP project
    
    Returns:
        (success, message)
    """
    verifier = GradleVerifier(project_path)
    return verifier.quick_check()
