import os
import argparse
import sys

# Add the subdirectories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'comprehension'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'generation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'testing'))

from analyze_project import analyze_android_project
from generate_code import generate_kmp_code
from migrate_tests import migrate_tests
from evaluate_code import evaluate_code

class KmpMigrationPipeline:
    def __init__(self, project_path):
        self.project_path = project_path

    def run(self):
        """
        Runs the full KMP migration pipeline.
        """
        # Phase 1: Comprehension
        print("\n--- Phase 1: Comprehension ---")
        analyze_android_project(self.project_path)

        # Phase 2: Code Generation
        print("\n--- Phase 2: Code Generation ---")
        generate_kmp_code(self.project_path)

        # Phase 3: Test Migration
        print("\n--- Phase 3: Test Migration ---")
        migrate_tests(self.project_path)

        # Phase 4: Evaluation
        print("\n--- Phase 4: Evaluation ---")
        evaluate_code(self.project_path)

        print("\n--- Pipeline Finished ---")
        print("Review the generated artifacts in the project directory.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the KMP migration pipeline.")
    parser.add_argument("project_path", help="The absolute path to the Android project.")
    args = parser.parse_args()

    pipeline = KmpMigrationPipeline(args.project_path)
    pipeline.run()
