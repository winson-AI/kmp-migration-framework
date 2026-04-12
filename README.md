# KMP Migration Framework

A fully automated, multi-agent powered pipeline for migrating Android projects to Kotlin Multiplatform (KMP).

## Overview

This framework uses an intelligent agentic workflow to:
1. **Comprehend** your Android project structure and dependencies
2. **Generate** KMP-compatible code using AI agents
3. **Migrate** tests and create evaluation reports
4. **Learn** from failures to improve future migrations
5. **Deliver** results as a ready-to-use KMP project

## Quick Start

### Prerequisites

```bash
# Python 3.9+
python3 --version

# Required Python packages
pip3 install PyYAML
```

### Directory Structure

```
~/kmp-migration-framework/          # Framework root
├── comprehension/                   # Project analysis
├── generation/                      # Code translation
├── testing/                         # Test migration
├── learning/                        # Self-improvement
├── delivery/                        # Git/PR creation
├── supervisor/                      # Pipeline monitoring
├── reporting/                       # Final reports
├── skills/                          # Library mappings
├── templates/                       # KMP project template
└── orchestrator.py                  # Main runner
```

## Usage

### Step 1: Prepare Your Android Project

Place your Android project in any directory. The framework expects a standard Android project structure:

```
/path/to/your/android-project/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/ or kotlin/
│   │   │   └── AndroidManifest.xml
│   │   ├── test/
│   │   └── androidTest/
│   └── build.gradle or build.gradle.kts
├── settings.gradle or settings.gradle.kts
└── build.gradle
```

### Step 2: Run the Migration Pipeline

```python
import sys
sys.path.append('/path/to/kmp-migration-framework')

from orchestrator import run_orchestrator

# Run migration (dry_run=True for testing without git operations)
run_orchestrator(
    project_path='/path/to/your/android-project',
    dry_run=True
)
```

### Step 3: Batch Migration (Multiple Projects)

```python
import sys
import os
sys.path.append('/path/to/kmp-migration-framework')

from orchestrator import run_orchestrator

projects = [
    '/path/to/project1',
    '/path/to/project2',
    '/path/to/project3',
]

for project_path in projects:
    if os.path.exists(project_path):
        print(f"\n{'='*60}")
        print(f"MIGRATING: {os.path.basename(project_path)}")
        print(f"{'='*60}\n")
        run_orchestrator(project_path, dry_run=True)
```

## Input

### Required Input

| Item | Description | Example |
|------|-------------|---------|
| `project_path` | Absolute path to Android project root | `/Users/username/examples/BookKeeper` |
| `dry_run` | Skip git operations (True/False) | `True` for testing |

### Expected Project Structure

The framework analyzes these files automatically:

| File | Purpose |
|------|---------|
| `settings.gradle` | Discovers project modules |
| `build.gradle` | Identifies dependencies |
| `src/**/*.kt` | Kotlin source files to migrate |
| `src/**/*.java` | Java source files to migrate |
| `src/test/**` | Unit tests to migrate |
| `src/androidTest/**` | Instrumented tests to migrate |

### Supported Dependencies

The framework currently includes skills for:

| Android Library | KMP Equivalent | Status |
|-----------------|----------------|--------|
| Retrofit | Ktor Client | ✅ Mapped |
| Room | SQLDelight | 🔄 Coming Soon |
| ViewModel | Kotlinx Coroutines | 🔄 Coming Soon |
| LiveData | Kotlinx Flow | 🔄 Coming Soon |

To add new skills, create a folder in `skills/` with:
- `skill.yaml` - Dependency mapping
- `guide.md` - Migration instructions

## Output

### Generated Artifacts

After running the pipeline, each project will have:

| File | Location | Description |
|------|----------|-------------|
| `SPEC.md` | `{project_path}/` | Migration specification |
| `TEST_MIGRATION_PLAN.md` | `{project_path}/` | Test migration strategy |
| `EVALUATION_REPORT.md` | `{project_path}/` | Code evaluation results |
| `MIGRATION_REPORT.md` | `{project_path}/` | Final migration summary |
| `migrated_kmp_project/` | `{project_path}/` | **Complete KMP project** |

### Migrated Project Structure

```
{project_path}/migrated_kmp_project/
└── shared/
    ├── build.gradle.kts          # KMP build configuration
    └── src/
        ├── commonMain/
        │   └── kotlin/           # Shared KMP code
        │       ├── YourFile.kt
        │       └── ...
        ├── androidMain/          # Android-specific code (template)
        ├── iosMain/              # iOS-specific code (template)
        └── desktopMain/          # Desktop-specific code (template)
```

### Example Output

```
--- Phase 1: Comprehension ---
SPEC.md generated successfully at /path/to/project/SPEC.md

--- Phase 2: Code Generation ---
Saved migrated file to: /path/to/project/migrated_kmp_project/shared/src/commonMain/kotlin/MainActivity.kt
File: /path/to/project/app/src/main/java/com/example/MainActivity.kt
Generated Code: [KMP code]
Evaluation: approve
--------------------

--- Phase 3: Test Migration ---
Test migration plan generated at /path/to/project/TEST_MIGRATION_PLAN.md

--- Phase 4: Evaluation ---
Evaluation report generated at /path/to/project/EVALUATION_REPORT.md

--- Phase 5: Learning ---
[Learning from any failures]

--- Phase 6: Delivery ---
git checkout -b kmp-migration
git add .
git commit -m 'feat: Migrate to KMP'

--- Phase 7: Reporting ---
Migration report generated at /path/to/project/MIGRATION_REPORT.md

--- Pipeline Finished ---
```

## Results

### Migration Statistics

| Metric | Description |
|--------|-------------|
| Files Migrated | All `.kt` and `.java` files in `src/` directories |
| Dependencies Analyzed | All dependencies from `build.gradle` files |
| Tests Migrated | Unit tests + Instrumented tests |
| Success Rate | Tracked in `EVALUATION_REPORT.md` |

### Example: BookKeeper Project

**Before (Android):**
```
BookKeeper/
├── app/src/main/java/com/example/bookkeeper/
│   ├── MainActivity.kt
│   ├── Book.kt
│   ├── BookDAO.kt
│   ├── BookViewModel.kt
│   └── BookRoomDatabase.kt
└── app/build.gradle
```

**After (KMP):**
```
BookKeeper/
├── migrated_kmp_project/
│   └── shared/
│       ├── build.gradle.kts
│       └── src/commonMain/kotlin/
│           ├── MainActivity.kt
│           ├── Book.kt
│           ├── BookDAO.kt
│           ├── BookViewModel.kt
│           └── BookRoomDatabase.kt
├── SPEC.md
├── MIGRATION_REPORT.md
└── EVALUATION_REPORT.md
```

## Configuration

### Customizing the Pipeline

Edit `orchestrator.py` to customize phases:

```python
class KmpMigrationPipeline:
    def __init__(self, project_path, dry_run=True):
        self.project_path = project_path
        self.dry_run = dry_run  # Set False for real git operations

    def run(self):
        # Enable/disable phases by commenting out:
        analyze_android_project(self.project_path)      # Phase 1
        generate_kmp_code(self.project_path, ...)       # Phase 2
        migrate_tests(self.project_path)                # Phase 3
        evaluate_code(self.project_path)                # Phase 4
        refine_skills(...)                              # Phase 5
        delivery_agent(...)                             # Phase 6
        reporter_agent(self.project_path)               # Phase 7
```

### Adding AI Model Integration

To use Ollama or Dashscope for real code generation:

```python
# In orchestrator.py, replace the mock delegate_task:

# Current (mock):
generate_kmp_code(self.project_path, lambda goal, toolsets=None: "approve")

# Ollama integration:
import requests

def ollama_delegate(goal, toolsets=None):
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "qwen2.5-coder",
        "prompt": goal,
        "stream": False
    })
    return response.json()['response']

generate_kmp_code(self.project_path, ollama_delegate)

# Dashscope (Qwen) integration:
import dashscope

def dashscope_delegate(goal, toolsets=None):
    response = dashscope.Generation.call(
        model='qwen-max',
        prompt=goal
    )
    return response.output.text

generate_kmp_code(self.project_path, dashscope_delegate)
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `SPEC.md not found` | Run Phase 1 (Comprehension) first |
| `IsADirectoryError` | Ensure project has standard Android structure |
| `ModuleNotFoundError` | Add framework to Python path: `sys.path.append()` |
| `AttributeError: 'NoneType'` | Check delegate_task returns a value |

### Logs and Debugging

All pipeline output is printed to stdout. For detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
run_orchestrator('/path/to/project', dry_run=True)
```

## Examples

### Migrated Projects

All 11 projects from [Android-Beginner-Projects](https://github.com/akebu6/Android-Beginner-Projects) have been migrated:

| Project | Files | Location |
|---------|-------|----------|
| BookKeeper | 12 | `~/examples/BookKeeper/migrated_kmp_project/` |
| ComposeArticle | 7 | `~/examples/ComposeArticle/migrated_kmp_project/` |
| NoteKeeper | 14 | `~/examples/NoteKeeper/migrated_kmp_project/` |
| QuotesApp | 5 | `~/examples/QuotesApp/migrated_kmp_project/` |
| TicTacToe | 4 | `~/examples/TicTacToe/migrated_kmp_project/` |
| + 6 more | - | `~/examples/*/migrated_kmp_project/` |

### Viewing Results

```bash
# View migration report
cat ~/examples/BookKeeper/MIGRATION_REPORT.md

# View generated KMP code
cat ~/examples/BookKeeper/migrated_kmp_project/shared/src/commonMain/kotlin/Book.kt

# View evaluation results
cat ~/examples/BookKeeper/EVALUATION_REPORT.md
```

## License

This framework is provided as-is for educational and production use.

## Contributing

To contribute new skills, tests, or improvements:

1. Fork the repository
2. Create a new skill in `skills/`
3. Test with sample projects
4. Submit a pull request

---

**Framework Version:** 1.0.0  
**Last Updated:** 2026-04-12  
**Tested With:** Python 3.9+, Android Gradle Plugin 7.0+
