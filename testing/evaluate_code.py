import os
import sys

# Add testing subdirectory to path
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

try:
    from .comprehensive import ComprehensiveTesting
except ImportError:
    from comprehensive import ComprehensiveTesting

def evaluate_code(project_path, delegate_task=None, vision_analyze=None):
    """
    Comprehensive code evaluation using traditional metrics, LLM-as-a-Judge, and multi-modal analysis.
    """
    migrated_project_path = os.path.join(project_path, 'migrated_kmp_project')
    
    if not os.path.exists(migrated_project_path):
        print(f"Warning: Migrated project not found at {migrated_project_path}")
        print("Running evaluation on original project structure...")
        migrated_project_path = project_path
    
    # Initialize comprehensive testing
    testing = ComprehensiveTesting(
        project_path=project_path,
        migrated_project_path=migrated_project_path,
        delegate_task=delegate_task,
        vision_analyze=vision_analyze
    )
    
    # Run all evaluations
    results = testing.run_all_evaluations()
    
    # Export JSON results
    testing.export_results_json()
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Overall Score: {results.get('overall_score', 0)}/100")
    
    if results.get('overall_score', 0) >= 80:
        print("Status: ✅ EXCELLENT - Ready for production")
    elif results.get('overall_score', 0) >= 60:
        print("Status: ⚠️ GOOD - Minor improvements recommended")
    elif results.get('overall_score', 0) >= 40:
        print("Status: ⚡ NEEDS WORK - Significant improvements needed")
    else:
        print("Status: ❌ CRITICAL - Major refactoring required")
    
    print("="*60)
    
    return results
