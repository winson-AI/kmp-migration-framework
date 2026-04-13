import os
import sys
import threading

# Add the subdirectories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'comprehension'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'generation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'testing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'learning'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'delivery'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'supervisor'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'reporting'))

try:
    from comprehension.spec_generator import generate_spec_md as analyze_android_project
except ImportError:
    try:
        from comprehension.enhanced_analyzer import analyze_android_project
    except ImportError:
        from analyze_project import analyze_android_project
from batch_migration import BatchMigrator
from generate_code import generate_kmp_code
from migrate_tests import migrate_tests
from evaluate_code import evaluate_code
from refine_skills import refine_skills
from delivery_agent import delivery_agent
from supervisor_agent import supervisor_agent
from reporter_agent import reporter_agent
from llm.health_checker import check_llm_health, get_recommended_invoker

class KmpMigrationPipeline:
    def __init__(self, project_path, delegate_task_func=None, dry_run=True):
        self.project_path = project_path
        self.delegate_task = delegate_task_func
        self.dry_run = dry_run

    def run(self):
        # Start the supervisor in a separate thread
        supervisor_thread = threading.Thread(target=supervisor_agent, args=(self,))
        supervisor_thread.daemon = True
        supervisor_thread.start()

        # Phase 1: Comprehension
        print("\n--- Phase 1: Comprehension ---")
        analyze_android_project(self.project_path)

        # Phase 2: Batch Code Migration (NEW - Holistic approach)
        print("\n--- Phase 2: Batch Code Migration ---")
        print("Analyzing project structure and migrating in batches...")
        
        if self.delegate_task:
            migrator = BatchMigrator(self.project_path, self.delegate_task)
        else:
            migrator = BatchMigrator(self.project_path)
        
        migration_plan = migrator.analyze_project()
        migration_results = migrator.migrate_all()
        
        print(f"\n✓ Migrated {len(migration_results['migrated_files'])} files in {len(migration_plan.file_groups)} batches")

        # Phase 3: Test Migration
        print("\n--- Phase 3: Test Migration ---")
        migrate_tests(self.project_path)

        # Phase 4: Comprehensive Evaluation (NEW)
        print("\n--- Phase 4: Comprehensive Evaluation ---")
        print("Includes: Traditional Metrics + LLM-as-a-Judge + Multi-Modal")
        evaluate_code(self.project_path, self.delegate_task, None)

        # Phase 5: Learning
        print("\n--- Phase 5: Learning ---")
        refine_skills(self.delegate_task)

        # Phase 6: Delivery
        print("\n--- Phase 6: Delivery ---")
        delivery_agent(self.project_path, self.delegate_task, self.dry_run)

        # Phase 7: Reporting
        print("\n--- Phase 7: Reporting ---")
        reporter_agent(self.project_path)

        print("\n--- Pipeline Finished ---\"")
        print("Review the generated artifacts in the project directory.")

def run_orchestrator(project_path, delegate_task_func=None, dry_run=True, check_health=True):
    """
    Run the KMP migration pipeline.
    
    Args:
        project_path: Path to Android project
        delegate_task_func: LLM invoker or None for mock mode
        dry_run: Skip git operations
        check_health: Run LLM health check before migration (default: True)
    """
    # Run health check if no invoker provided and check is enabled
    if check_health and delegate_task_func is None:
        print("\n" + "="*60)
        print("LLM HEALTH CHECK")
        print("="*60)
        
        health_result = check_llm_health(timeout_seconds=10, print_report=True)
        
        # Get recommended invoker if available
        if health_result.is_healthy:
            print("\n✓ Using recommended LLM provider...")
            delegate_task_func = get_recommended_invoker(health_result)
        else:
            print("\n⚠ No LLM available. Running in MOCK mode.")
            print("   For better results, configure an LLM provider:")
            print("   - Ollama: ollama pull qwen2.5-coder:7b")
            print("   - Dashscope: export DASHSCOPE_API_KEY=sk-...")
            print("   - OpenAI: export OPENAI_API_KEY=sk-...")
            print()
    
    pipeline = KmpMigrationPipeline(project_path, delegate_task_func, dry_run)
    pipeline.run()
