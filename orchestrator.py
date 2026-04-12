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

from analyze_project import analyze_android_project
from generate_code import generate_kmp_code
from migrate_tests import migrate_tests
from evaluate_code import evaluate_code
from refine_skills import refine_skills
from delivery_agent import delivery_agent
from supervisor_agent import supervisor_agent
from reporter_agent import reporter_agent

class KmpMigrationPipeline:
    def __init__(self, project_path, delegate_task_func, dry_run=True):
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

        # Phase 2: Code Generation
        print("\n--- Phase 2: Code Generation ---")
        generate_kmp_code(self.project_path, self.delegate_task)

        # Phase 3: Test Migration
        print("\n--- Phase 3: Test Migration ---")
        migrate_tests(self.project_path)

        # Phase 4: Evaluation
        print("\n--- Phase 4: Evaluation ---")
        evaluate_code(self.project_path)

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

def run_orchestrator(project_path, delegate_task_func, dry_run=True):
    pipeline = KmpMigrationPipeline(project_path, delegate_task_func, dry_run)
    pipeline.run()
