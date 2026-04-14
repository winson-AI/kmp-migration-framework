import os
import json
import time
from datetime import datetime

try:
    from .metrics import TestingMetrics
    from .llm_judge import LLMJudge
    from .multimodal import MultiModalEvaluator
    from .gradle_verifier import GradleVerifier, verify_gradle_build
except ImportError:
    from metrics import TestingMetrics
    from llm_judge import LLMJudge
    from multimodal import MultiModalEvaluator
    from gradle_verifier import GradleVerifier, verify_gradle_build

class ComprehensiveTesting:
    """Orchestrates all testing and evaluation methods."""
    
    def __init__(self, project_path, migrated_project_path, delegate_task=None, vision_analyze=None):
        self.project_path = project_path
        self.migrated_project_path = migrated_project_path
        self.delegate_task = delegate_task
        self.vision_analyze = vision_analyze
        
        self.metrics_evaluator = TestingMetrics(project_path, migrated_project_path)
        self.llm_judge = LLMJudge(project_path, delegate_task)
        self.multimodal_eval = MultiModalEvaluator(project_path, vision_analyze)
        
        self.results = {}
    
    def run_all_evaluations(self):
        """Run all evaluation methods and generate comprehensive report."""
        print("\n" + "="*60)
        print("COMPREHENSIVE TESTING & EVALUATION")
        print("="*60)
        
        self.results = {
            'project': os.path.basename(self.project_path),
            'timestamp': datetime.now().isoformat(),
            'traditional_metrics': None,
            'llm_judge': None,
            'multimodal': None,
            'overall_score': 0
        }
        
        # Phase 1: Traditional Metrics
        print("\n[1/3] Running Traditional Metrics...")
        self.metrics_evaluator.collect_all_metrics()
        self.results['traditional_metrics'] = self.metrics_evaluator.metrics
        
        # Phase 2: LLM-as-a-Judge
        print("\n[2/3] Running LLM-as-a-Judge Evaluation...")
        migrated_files = self._collect_migrated_files()
        self.results['llm_judge'] = self.llm_judge.evaluate_all(migrated_files)
        
        # Phase 3: Multi-Modal Evaluation
        print("\n[3/4] Running Multi-Modal UI Evaluation...")
        compose_files = self._find_compose_files()
        ui_evaluation = self.multimodal_eval.evaluate_ui_components(compose_files)
        platform_evaluation = self.multimodal_eval.evaluate_cross_platform_ui(compose_files)
        self.results['multimodal'] = {
            'ui': ui_evaluation,
            'platform': platform_evaluation
        }
        
        # Phase 4: Gradle Build Verification (NEW)
        print("\n[4/4] Running Gradle Build Verification...")
        gradle_result = verify_gradle_build(self.migrated_project_path, timeout=300)
        self.results['gradle_build'] = gradle_result.to_dict()
        
        if gradle_result.success:
            print("  ✓ Gradle build PASSED")
        else:
            print(f"  ✗ Gradle build FAILED: {gradle_result.status.value}")
            if gradle_result.errors:
                print(f"  Errors: {len(gradle_result.errors)}")
        
        # Calculate overall score
        self.results['overall_score'] = self._calculate_overall_score()
        
        # Generate final report
        report = self.generate_final_report()
        
        # Save report
        report_path = os.path.join(self.project_path, 'COMPREHENSIVE_TEST_REPORT.md')
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Comprehensive test report saved to: {report_path}")
        
        return self.results
    
    def _collect_migrated_files(self):
        """Collect all migrated source files for evaluation."""
        files = []
        kmp_path = os.path.join(self.migrated_project_path, 'shared', 'src', 'commonMain', 'kotlin')
        
        if os.path.exists(kmp_path):
            for root, dirs, filenames in os.walk(kmp_path):
                for filename in filenames:
                    if filename.endswith(('.kt', '.java')):
                        file_path = os.path.join(root, filename)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        files.append({
                            'path': file_path,
                            'original_path': 'N/A',  # Would need mapping from SPEC.md
                            'content': content
                        })
        
        return files
    
    def _find_compose_files(self):
        """Find all Jetpack Compose / Compose Multiplatform files."""
        compose_files = []
        kmp_path = os.path.join(self.migrated_project_path, 'shared', 'src')
        
        if os.path.exists(kmp_path):
            for root, dirs, filenames in os.walk(kmp_path):
                for filename in filenames:
                    if filename.endswith('.kt'):
                        file_path = os.path.join(root, filename)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Check if it's a Compose file
                        if '@Composable' in content or 'import androidx.compose' in content:
                            compose_files.append(file_path)
        
        return compose_files
    
    def _calculate_overall_score(self):
        """Calculate weighted overall score from all evaluations."""
        scores = []
        weights = []
        
        # Gradle Build score (weight: 40%) - MOST IMPORTANT
        gradle_score = 0
        gradle_result = self.results.get('gradle_build', {})
        
        if gradle_result.get('success', False):
            gradle_score = 100  # Full points for passing build
        else:
            # Partial credit based on error count
            error_count = gradle_result.get('error_count', 0)
            if error_count == 0:
                gradle_score = 50  # Some other issue
            else:
                gradle_score = max(0, 100 - (error_count * 10))  # -10 per error
        
        scores.append(gradle_score)
        weights.append(0.40)
        
        # Traditional metrics score (weight: 25%)
        traditional_score = 0
        metrics = self.results.get('traditional_metrics', {})
        
        if metrics.get('compilation', {}).get('status') == 'success':
            traditional_score += 25
        
        coverage = metrics.get('test_coverage', {}).get('estimated_coverage_percent', 0)
        traditional_score += min(25, coverage * 0.25)
        
        total_deps = metrics.get('dependency_check', {}).get('total_dependencies', 1)
        kmp_deps = metrics.get('dependency_check', {}).get('kmp_compatible', 0)
        traditional_score += min(25, (kmp_deps / max(total_deps, 1)) * 25)
        
        common_ratio = metrics.get('platform_compatibility', {}).get('common_code_percent', 0)
        traditional_score += min(25, common_ratio * 0.25)
        
        scores.append(traditional_score)
        weights.append(0.25)
        
        # LLM Judge score (weight: 40%)
        llm_report = self.results.get('llm_judge', '')
        # Extract overall score from report
        import re
        score_match = re.search(r'Overall Score: ([\d.]+)/10', llm_report)
        if score_match:
            llm_score = float(score_match.group(1)) * 10  # Convert to 0-100
            scores.append(llm_score)
            weights.append(0.40)
        
        # Multi-modal score (weight: 30%)
        multimodal = self.results.get('multimodal', {})
        ui_eval = multimodal.get('ui', {})
        platform_eval = multimodal.get('platform', {})
        
        multimodal_score = 0
        multimodal_score += ui_eval.get('accessibility_score', 0) * 0.3
        multimodal_score += ui_eval.get('design_system_compliance', 0) * 0.3
        multimodal_score += ui_eval.get('responsive_design_score', 0) * 0.2
        multimodal_score += platform_eval.get('ios_compatibility', 0) * 0.2
        
        scores.append(multimodal_score)
        weights.append(0.30)
        
        # Calculate weighted average
        if scores and weights:
            overall = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
            return round(overall, 1)
        
        return 0
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        report = f"""
# Comprehensive KMP Migration Test Report

**Project:** {self.results.get('project', 'Unknown')}  
**Generated:** {self.results.get('timestamp', 'N/A')}  
**Overall Score:** {self.results.get('overall_score', 0)}/100

---

## Executive Summary

"""
        
        # Determine overall status
        score = self.results.get('overall_score', 0)
        if score >= 80:
            status = "✅ EXCELLENT - Ready for production"
        elif score >= 60:
            status = "⚠️ GOOD - Minor improvements recommended"
        elif score >= 40:
            status = "⚡ NEEDS WORK - Significant improvements needed"
        else:
            status = "❌ CRITICAL - Major refactoring required"
        
        report += f"**Status:** {status}\n\n"
        
        # Add all sub-reports
        report += self.metrics_evaluator.generate_report()
        report += "\n---\n"
        report += self.results.get('llm_judge', 'LLM evaluation not available')
        report += "\n---\n"
        
        ui_eval = self.results.get('multimodal', {}).get('ui', {})
        platform_eval = self.results.get('multimodal', {}).get('platform', {})
        report += self.multimodal_eval.generate_report(ui_eval, platform_eval)
        
        # Add Gradle build results (NEW)
        report += "\n---\n\n"
        report += "## Gradle Build Verification\n\n"
        
        gradle = self.results.get('gradle_build', {})
        if gradle:
            success = gradle.get('success', False)
            status = gradle.get('status', 'unknown')
            duration = gradle.get('duration_seconds', 0)
            error_count = gradle.get('error_count', 0)
            
            report += f"**Build Status:** {'✓ PASSED' if success else '✗ FAILED'}\n"
            report += f"**Status:** `{status}`\n"
            report += f"**Duration:** {duration:.1f}s\n"
            report += f"**Errors:** {error_count}\n\n"
            
            if gradle.get('gradle_version'):
                report += f"**Gradle Version:** {gradle['gradle_version']}\n"
            if gradle.get('kotlin_version'):
                report += f"**Kotlin Version:** {gradle['kotlin_version']}\n"
            
            if gradle.get('errors'):
                report += "\n### Compilation Errors\n\n"
                for i, error in enumerate(gradle['errors'][:10], 1):
                    report += f"{i}. **{error['error_type']}** in `{error['file']}`"
                    if error.get('line'):
                        report += f" (line {error['line']})"
                    report += f"\n   ```\n   {error['message']}\n   ```\n"
                    if error.get('suggestion'):
                        report += f"   \n   💡 **Fix:** {error['suggestion']}\n"
            
            if gradle.get('suggestions'):
                report += "\n### Recommendations\n\n"
                for suggestion in gradle['suggestions'][:5]:
                    report += f"- {suggestion}\n"
        else:
            report += "*Gradle build verification not performed*\n"
        
        # Add action items
        report += f"""
---

## Action Items

### Critical (Fix Immediately)
"""
        # Collect critical issues from all evaluations
        critical_issues = []
        
        if self.results.get('traditional_metrics', {}).get('compilation', {}).get('status') != 'success':
            critical_issues.append("Fix compilation errors before proceeding")
        
        if score < 40:
            critical_issues.append("Overall score below 40 - major refactoring needed")
        
        for issue in critical_issues:
            report += f"- [ ] {issue}\n"
        
        if not critical_issues:
            report += "- [ ] No critical issues found\n"
        
        report += """
### High Priority
- [ ] Review LLM judge recommendations
- [ ] Address accessibility issues in UI
- [ ] Improve test coverage

### Medium Priority
- [ ] Optimize code complexity
- [ ] Enhance platform compatibility
- [ ] Add documentation

### Low Priority
- [ ] Performance optimization
- [ ] Code style improvements
- [ ] Additional platform support

---

## Next Steps

1. **Review** all evaluation reports above
2. **Prioritize** action items based on impact
3. **Implement** fixes iteratively
4. **Re-run** evaluation to track improvements
5. **Deploy** when score exceeds 80/100

---

*Report generated by KMP Migration Framework v1.0*
"""
        
        return report
    
    def export_results_json(self, output_path=None):
        """Export results as JSON for programmatic access."""
        if output_path is None:
            output_path = os.path.join(self.project_path, 'test_results.json')
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"✓ Results exported to: {output_path}")
        return output_path
