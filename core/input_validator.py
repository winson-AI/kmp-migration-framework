"""
Input Validator for KMP Migration

Validates all required user inputs before running migration.

Usage:
    from core.input_validator import validate_inputs, InputRequirements
    
    # Check requirements
    requirements = InputRequirements()
    requirements.check_project_path('/path/to/project')
    requirements.check_python_version()
    requirements.check_dependencies()
    
    # Validate all
    errors = validate_inputs(project_path='/path/to/project')
    if errors:
        print("Fix these issues:")
        for error in errors:
            print(f"  - {error}")
"""

import os
import sys
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    message: str
    fix_command: Optional[str] = None
    severity: str = 'error'  # error, warning, info


class InputValidator:
    """Validate user inputs and system requirements."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
    
    def validate_all(self, project_path: str, check_llm: bool = True) -> bool:
        """
        Run all validation checks.
        
        Args:
            project_path: Path to Android project
            check_llm: Whether to check LLM availability
        
        Returns:
            True if all critical checks pass
        """
        print("\n" + "="*60)
        print("INPUT VALIDATION")
        print("="*60)
        
        self.results = []
        
        # System requirements
        self.check_python_version()
        self.check_framework_installed()
        
        # Project validation
        self.check_project_path(project_path)
        self.check_project_structure(project_path)
        self.check_gradle_files(project_path)
        
        # LLM check (optional)
        if check_llm:
            self.check_llm_availability()
        
        # Print results
        self._print_results()
        
        # Return True if no critical errors
        return not any(r.severity == 'error' and not r.passed for r in self.results)
    
    def check_python_version(self, min_version: Tuple[int, int] = (3, 9)):
        """Check Python version."""
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            self.results.append(ValidationResult(
                check_name='Python Version',
                passed=True,
                message=f'Python {current_version[0]}.{current_version[1]} ✓',
                severity='info'
            ))
        else:
            self.results.append(ValidationResult(
                check_name='Python Version',
                passed=False,
                message=f'Python {current_version[0]}.{current_version[1]} (need {min_version[0]}.{min_version[1]}+)',
                fix_command='Install Python 3.9+ from https://www.python.org/',
                severity='error'
            ))
    
    def check_framework_installed(self):
        """Check if framework is properly installed."""
        framework_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        required_files = [
            'orchestrator.py',
            'core/config.py',
            'generation/batch_migration.py',
            'testing/comprehensive.py'
        ]
        
        missing = []
        for file in required_files:
            if not os.path.exists(os.path.join(framework_path, file)):
                missing.append(file)
        
        if not missing:
            self.results.append(ValidationResult(
                check_name='Framework Installation',
                passed=True,
                message='All required files present ✓',
                severity='info'
            ))
        else:
            self.results.append(ValidationResult(
                check_name='Framework Installation',
                passed=False,
                message=f'Missing files: {", ".join(missing)}',
                fix_command='Clone or reinstall the framework',
                severity='error'
            ))
    
    def check_project_path(self, project_path: str):
        """Check if project path exists and is accessible."""
        if not project_path:
            self.results.append(ValidationResult(
                check_name='Project Path',
                passed=False,
                message='Project path not provided',
                fix_command='Provide path to your Android project',
                severity='error'
            ))
            return
        
        if not os.path.exists(project_path):
            self.results.append(ValidationResult(
                check_name='Project Path',
                passed=False,
                message=f'Path does not exist: {project_path}',
                fix_command=f'Check path: cd {project_path}',
                severity='error'
            ))
            return
        
        if not os.path.isdir(project_path):
            self.results.append(ValidationResult(
                check_name='Project Path',
                passed=False,
                message=f'Path is not a directory: {project_path}',
                fix_command='Provide a directory path, not a file',
                severity='error'
            ))
            return
        
        # Check if readable
        try:
            os.listdir(project_path)
            self.results.append(ValidationResult(
                check_name='Project Path',
                passed=True,
                message=f'{project_path} ✓',
                severity='info'
            ))
        except PermissionError:
            self.results.append(ValidationResult(
                check_name='Project Path',
                passed=False,
                message=f'No permission to read: {project_path}',
                fix_command='Check file permissions',
                severity='error'
            ))
    
    def check_project_structure(self, project_path: str):
        """Check if project has expected Android structure."""
        if not project_path or not os.path.exists(project_path):
            return
        
        # Check for app directory
        app_dir = os.path.join(project_path, 'app')
        has_app = os.path.exists(app_dir) and os.path.isdir(app_dir)
        
        # Check for source files
        src_dirs = [
            os.path.join(app_dir, 'src', 'main', 'java'),
            os.path.join(app_dir, 'src', 'main', 'kotlin')
        ]
        has_source = any(os.path.exists(d) for d in src_dirs)
        
        # Count Kotlin/Java files
        kt_files = []
        java_files = []
        for root, dirs, files in os.walk(project_path):
            if 'build/' in root or '.gradle/' in root:
                continue
            for file in files:
                if file.endswith('.kt'):
                    kt_files.append(file)
                elif file.endswith('.java'):
                    java_files.append(file)
        
        total_files = len(kt_files) + len(java_files)
        
        # Build message
        messages = []
        if has_app:
            messages.append('app/ directory ✓')
        if has_source:
            messages.append('source files ✓')
        if total_files > 0:
            messages.append(f'{total_files} files ({len(kt_files)} Kotlin, {len(java_files)} Java)')
        
        # Determine pass/fail
        passed = has_app and has_source and total_files > 0
        
        self.results.append(ValidationResult(
            check_name='Project Structure',
            passed=passed,
            message=', '.join(messages) if messages else 'Missing expected structure',
            fix_command='Ensure project has app/src/main/java or app/src/main/kotlin',
            severity='error' if not passed else 'info'
        ))
    
    def check_gradle_files(self, project_path: str):
        """Check for required Gradle files."""
        if not project_path or not os.path.exists(project_path):
            return
        
        required = [
            'build.gradle',
            'settings.gradle',
            'app/build.gradle'
        ]
        
        found = []
        missing = []
        
        for file in required:
            full_path = os.path.join(project_path, file)
            if os.path.exists(full_path):
                found.append(file)
            else:
                # Check for .kts variants
                kts_path = full_path + '.kts'
                if os.path.exists(kts_path):
                    found.append(file + '.kts')
                else:
                    missing.append(file)
        
        if not missing:
            self.results.append(ValidationResult(
                check_name='Gradle Files',
                passed=True,
                message=f'Found: {", ".join(found)} ✓',
                severity='info'
            ))
        else:
            self.results.append(ValidationResult(
                check_name='Gradle Files',
                passed=False,
                message=f'Missing: {", ".join(missing)}',
                fix_command='Ensure project has build.gradle and settings.gradle',
                severity='warning'  # Not critical, can still analyze
            ))
    
    def check_llm_availability(self):
        """Check if any LLM provider is available."""
        try:
            from llm.health_checker import check_llm_health
            result = check_llm_health(timeout_seconds=5, print_report=False)
            
            if result.is_healthy:
                self.results.append(ValidationResult(
                    check_name='LLM Provider',
                    passed=True,
                    message=f'{result.recommended_provider} ({result.recommended_model}) ✓',
                    severity='info'
                ))
            else:
                self.results.append(ValidationResult(
                    check_name='LLM Provider',
                    passed=False,
                    message='No LLM providers configured',
                    fix_command='Configure Ollama, Dashscope, OpenAI, or Anthropic',
                    severity='warning'  # Can still use mock mode
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                check_name='LLM Provider',
                passed=False,
                message=f'Error checking LLM: {str(e)}',
                severity='warning'
            ))
    
    def check_dependencies(self):
        """Check Python dependencies."""
        required_packages = ['yaml', 'requests']
        optional_packages = ['dashscope', 'openai', 'anthropic']
        
        missing_required = []
        missing_optional = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_required.append(package)
        
        for package in optional_packages:
            try:
                __import__(package)
            except ImportError:
                missing_optional.append(package)
        
        if not missing_required:
            self.results.append(ValidationResult(
                check_name='Python Dependencies',
                passed=True,
                message='All required packages installed ✓',
                severity='info'
            ))
        else:
            self.results.append(ValidationResult(
                check_name='Python Dependencies',
                passed=False,
                message=f'Missing: {", ".join(missing_required)}',
                fix_command=f'pip install {" ".join(missing_required)}',
                severity='error'
            ))
        
        if missing_optional:
            self.results.append(ValidationResult(
                check_name='Optional Packages',
                passed=True,
                message=f'Not installed (optional): {", ".join(missing_optional)}',
                severity='info'
            ))
    
    def _print_results(self):
        """Print validation results."""
        print()
        
        errors = [r for r in self.results if r.severity == 'error' and not r.passed]
        warnings = [r for r in self.results if r.severity == 'warning' and not r.passed]
        passed = [r for r in self.results if r.passed]
        
        # Errors
        if errors:
            print("\n❌ ERRORS (must fix):")
            for error in errors:
                print(f"  • {error.check_name}: {error.message}")
                if error.fix_command:
                    print(f"    Fix: {error.fix_command}")
        
        # Warnings
        if warnings:
            print("\n⚠️  WARNINGS (recommended to fix):")
            for warning in warnings:
                print(f"  • {warning.check_name}: {warning.message}")
                if warning.fix_command:
                    print(f"    Fix: {warning.fix_command}")
        
        # Passed
        if passed:
            print("\n✓ PASSED:")
            for p in passed:
                print(f"  • {p.check_name}: {p.message}")
        
        # Summary
        print("\n" + "="*60)
        total_errors = len(errors)
        total_warnings = len(warnings)
        
        if total_errors == 0 and total_warnings == 0:
            print("STATUS: ✓ ALL CHECKS PASSED - Ready to migrate!")
        elif total_errors == 0:
            print(f"STATUS: ⚠️  {total_warnings} warning(s) - Can proceed with caution")
        else:
            print(f"STATUS: ❌ {total_errors} error(s) - Must fix before migrating")
        
        print("="*60)


def validate_inputs(project_path: str, check_llm: bool = True) -> bool:
    """
    Validate all inputs and requirements.
    
    Args:
        project_path: Path to Android project
        check_llm: Whether to check LLM availability
    
    Returns:
        True if validation passes (no critical errors)
    """
    validator = InputValidator()
    return validator.validate_all(project_path, check_llm)


def print_requirements():
    """Print all requirements for users."""
    print("\n" + "="*60)
    print("KMP MIGRATION - REQUIREMENTS")
    print("="*60)
    
    print("\n📁 INPUT REQUIRED:")
    print("  1. Android project path")
    print("     - Must have app/src/main/java or app/src/main/kotlin")
    print("     - Must have build.gradle and settings.gradle")
    print("     - Must have at least one .kt or .java file")
    print("\n  Example path:")
    print("    /Users/yourname/CodeBase/MyAndroidApp")
    
    print("\n💻 SYSTEM REQUIREMENTS:")
    print("  • Python 3.9 or higher")
    print("  • KMP Migration Framework installed")
    print("  • PyYAML package (pip install PyYAML)")
    
    print("\n🤖 LLM PROVIDERS (OPTIONAL):")
    print("  • Ollama (free, local) - ollama pull qwen2.5-coder:7b")
    print("  • Dashscope (paid) - export DASHSCOPE_API_KEY=sk-...")
    print("  • OpenAI (paid) - export OPENAI_API_KEY=sk-...")
    print("  • Anthropic (paid) - export ANTHROPIC_API_KEY=sk-...")
    print("\n  Note: Framework works without LLM (mock mode)")
    
    print("\n📋 COMMAND TO RUN:")
    print("  python3 -c \"")
    print("    import sys")
    print("    sys.path.append('/Users/winson/kmp-migration-framework')")
    print("    from orchestrator import run_orchestrator")
    print("    run_orchestrator('/path/to/your/project')")
    print("  \"")
    
    print("\n" + "="*60)


# CLI
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='KMP Migration Input Validator')
    parser.add_argument('--project', type=str, help='Project path to validate')
    parser.add_argument('--requirements', action='store_true', help='Print requirements')
    parser.add_argument('--no-llm', action='store_true', help='Skip LLM check')
    
    args = parser.parse_args()
    
    if args.requirements:
        print_requirements()
    elif args.project:
        success = validate_inputs(args.project, check_llm=not args.no_llm)
        sys.exit(0 if success else 1)
    else:
        print_requirements()
        print("\nUsage:")
        print("  python -m core.input_validator --requirements")
        print("  python -m core.input_validator --project /path/to/project")


if __name__ == '__main__':
    main()
