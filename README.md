# KMP Migration Framework v3.1

**Automated Android to Kotlin Multiplatform Migration**

Transform your Android projects into Kotlin Multiplatform (KMP) projects with a single command. This framework uses AI-powered code translation, comprehensive testing, and intelligent learning to ensure high-quality migrations.

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Technology Stack](#technology-stack)
3. [Architecture](#architecture)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Quick Start (3 Steps)](#quick-start-3-steps)
7. [Configuration](#configuration)
8. [Input Requirements](#input-requirements)
9. [Files & Scripts](#files--scripts)
10. [Migration Process](#migration-process)
11. [Output](#output)
12. [Troubleshooting](#troubleshooting)
13. [Examples](#examples)

---

## Introduction

### What is This?

The **KMP Migration Framework** automatically converts Android applications to Kotlin Multiplatform (KMP) projects. It analyzes your Android code, migrates it to KMP with shared code across platforms (Android, iOS, Desktop), and verifies the migration with comprehensive testing.

### Why KMP?

Kotlin Multiplatform allows you to:
- ✅ **Share business logic** across Android, iOS, Web, and Desktop
- ✅ **Reduce code duplication** by 40-60%
- ✅ **Maintain single source of truth** for business logic
- ✅ **Platform-specific UI** where it matters
- ✅ **Gradual adoption** - migrate incrementally

### What Does This Framework Do?

```
┌─────────────────────────────────────────────────────────────┐
│                    KMP MIGRATION                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Android Project                                      │
│  ├── Java/Kotlin source files                               │
│  ├── Gradle build files                                     │
│  └── Android-specific code                                  │
│                                                              │
│  PROCESS: AI-Powered Migration                               │
│  ├── Analyze architecture & dependencies                    │
│  ├── Generate KMP-compatible code                           │
│  ├── Create shared & platform modules                       │
│  └── Verify with Gradle build                               │
│                                                              │
│  OUTPUT: KMP Project                                         │
│  ├── shared/ (common code)                                  │
│  ├── androidApp/ (Android UI)                               │
│  ├── iosApp/ (iOS UI placeholder)                           │
│  └── Complete Gradle build system                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Agent System** | 5 specialized AI agents (Explorer, Planner, Generator, Evaluator, Refiner) |
| **Batch Migration** | Process files in groups (3-5x faster than file-by-file) |
| **Checkpoint/Resume** | Recover from failures without starting over |
| **Skills Hub** | 7+ pre-built migration skills (Retrofit→Ktor, Room→SQLDelight, etc.) |
| **Comprehensive Testing** | 4-method verification (Metrics, LLM, Multi-Modal, Gradle) |
| **Learning Loop** | Improves from every migration |
| **Gradle Build Script** | Self-contained bash script for building |

---

## Technology Stack

### Core Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Framework runtime |
| **Kotlin** | 1.9.20 | Target language |
| **Gradle** | 8.4 | Build system |
| **Bash** | 4.0+ | Build scripts |

### AI/LLM Support

| Provider | Models | Cost | Status |
|----------|--------|------|--------|
| **Ollama** | qwen2.5-coder, llama | Free (local) | ✓ Recommended |
| **Dashscope** | qwen-turbo, qwen-max | Paid | ✓ Supported |
| **OpenAI** | gpt-3.5, gpt-4 | Paid | ✓ Supported |
| **Anthropic** | claude-3-haiku/sonnet/opus | Paid | ✓ Supported |
| **Mock Mode** | N/A | Free | ✓ Works without LLM |

### KMP Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Ktor** | 2.3.6 | Networking (replaces Retrofit) |
| **SQLDelight** | 2.0.0 | Database (replaces Room) |
| **Kotlinx Coroutines** | 1.7.3 | Async (replaces LiveData/ViewModel) |
| **Kotlinx Serialization** | 1.6.0 | JSON (replaces Gson/Moshi) |
| **Koin** | 3.5.0 | Dependency Injection |

### Framework Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KMP MIGRATION FRAMEWORK                       │
│                         v3.1.0                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CORE PILLARS                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   HARNESS   │  │    MEMORY   │  │    TOOLS    │             │
│  │  - Checkpoint│  │  - Patterns │  │  - Registry │             │
│  │  - Parallel  │  │  - History  │  │  - Fallback │             │
│  │  - Recovery  │  │  - Lessons  │  │  - Health   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  AGENTS (Prompt/Tools/Author Separated)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ EXPLORER │  │ PLANNER  │  │GENERATOR │  │EVALUATOR │        │
│  │ +REFINER │  │          │  │          │  │          │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  TESTING (4-Method Verification)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  METRICS    │  │  LLM JUDGE  │  │  MULTI-MODAL│             │
│  │ - Coverage  │  │ - 10 Scores │  │ - UI Analysis│             │
│  │ - Complexity│  │ - Review    │  │ - A11y      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  GRADLE BUILD (bash script)                         │        │
│  │  - Auto-generates build files                       │        │
│  │  - Runs: gradle compileKotlinMetadata               │        │
│  │  - Reports errors with suggestions                  │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux/macOS/Windows | Linux/macOS |
| **Python** | 3.9 | 3.11+ |
| **Java** | 11 | 17+ |
| **RAM** | 4GB | 8GB+ |
| **Disk** | 1GB free | 5GB+ free |

### Check Your System

```bash
# Check Python
python3 --version  # Should be 3.9 or higher

# Check Java
java -version  # Should be 11 or higher

# Check disk space
df -h ~/  # Should have 1GB+ free
```

### Install Missing Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip openjdk-11-jdk git curl
```

**macOS:**
```bash
brew install python3 openjdk@11 git curl
```

**Windows:**
```powershell
# Install Python from https://www.python.org/
# Install Java from https://adoptium.net/
# Install Git from https://git-scm.com/
```

---

## Installation

### Step 1: Clone or Download Framework

```bash
# Clone from repository (if available)
git clone https://github.com/your-repo/kmp-migration-framework.git
cd kmp-migration-framework

# OR download and extract
# Download ZIP and extract to ~/kmp-migration-framework
```

### Step 2: Install Python Dependencies

```bash
cd ~/kmp-migration-framework
pip3 install PyYAML
```

### Step 3: (Optional) Set Up LLM

**Option A: Ollama (Free, Local) - RECOMMENDED**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull qwen2.5-coder:7b

# Start server (usually auto-starts)
ollama serve
```

**Option B: Dashscope (Paid, Cloud)**
```bash
# Get API key from https://dashscope.aliyun.com/
export DASHSCOPE_API_KEY="sk-your-key-here"
```

**Option C: Mock Mode (No LLM)**
```bash
# No setup needed - works out of the box
# Code will be migrated with mock responses
```

### Step 4: Verify Installation

```bash
python3 -c "
import sys
sys.path.append('~/kmp-migration-framework')
from orchestrator import run_orchestrator
print('✓ Framework installed successfully')
"
```

---

## Quick Start (3 Steps)

### Step 1: Prepare Your Android Project

Your project should have this structure:

```
MyAndroidApp/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/ or kotlin/    ← Your code here
│   │   │   │   └── com/example/
│   │   │   │       ├── MainActivity.kt
│   │   │   │       └── OtherFile.kt
│   │   │   └── AndroidManifest.xml
│   │   ├── test/                   ← Unit tests (optional)
│   │   └── androidTest/            ← Instrumented tests (optional)
│   └── build.gradle                ← Required
├── settings.gradle                  ← Required
└── build.gradle                     ← Required
```

**Find your project path:**
```bash
cd /path/to/your/AndroidProject
pwd
# Copy this path (e.g., /Users/yourname/CodeBase/MyApp)
```

### Step 2: Run Migration

**Basic (Mock Mode):**
```bash
python3 -c "
import sys
sys.path.append('~/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/path/to/your/android/project')
"
```

**With LLM (Better Quality):**
```bash
python3 -c "
import sys
sys.path.append('~/kmp-migration-framework')
from orchestrator import run_orchestrator
from llm import get_enhanced_invoker

invoker = get_enhanced_invoker('ollama', 'qwen2.5-coder:7b')
run_orchestrator('/path/to/your/android/project', delegate_task_func=invoker)
"
```

### Step 3: Check Results

After migration completes (1-5 minutes), check:

```bash
cd /path/to/your/android/project
ls -la
```

You should see:
```
migrated_kmp_project/     ← Your new KMP project
SPEC.md                    ← Migration specification
COMPREHENSIVE_TEST_REPORT.md  ← Quality report
test_results.json         ← Detailed results
```

**View migrated code:**
```bash
cd migrated_kmp_project/shared/src/commonMain/kotlin
ls -la
```

**That's it! Your KMP project is ready!** 🎉

---

## Configuration

### Configuration File

Create `~/.hermes/kmp-migration/config.json`:

```json
{
  "project_path": "/path/to/default/project",
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5-coder:7b",
    "base_url": "http://localhost:11434"
  },
  "gradle": {
    "version": "8.4",
    "kotlin_version": "1.9.20",
    "min_sdk": 21,
    "target_sdk": 34
  },
  "migration": {
    "dry_run": true,
    "enable_testing": true,
    "enable_learning": true
  }
}
```

### Command Line Options

```python
from orchestrator import run_orchestrator

run_orchestrator(
    project_path='/path/to/project',
    delegate_task_func=invoker,  # LLM invoker or None for mock
    dry_run=True,                 # Don't create git commits
    check_health=True             # Check LLM health first
)
```

### Environment Variables

```bash
# LLM API Keys
export DASHSCOPE_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."

# Ollama
export OLLAMA_HOST="localhost:11434"

# Framework
export KMP_MIGRATION_CONFIG="~/.hermes/kmp-migration/config.json"
```

---

## Input Requirements

### Required Input

| Input | Format | How to Get | Validation |
|-------|--------|------------|------------|
| **Project Path** | Absolute path | `cd /path && pwd` | Must exist, must be Android project |
| **Python 3.9+** | Version | `python3 --version` | Checked automatically |
| **Framework** | Directory | Clone/download | Checked automatically |

### Optional Input

| Input | Default | How to Set |
|-------|---------|------------|
| **LLM Provider** | Mock mode | Config file or env var |
| **API Key** | None | Environment variable |
| **Output Path** | `migrated_kmp_project/` | Config file |
| **Gradle Version** | 8.4 | Config file |
| **Kotlin Version** | 1.9.20 | Config file |

### Validate Before Migration

```bash
python3 -c "
import sys
sys.path.append('~/kmp-migration-framework')
from core import validate_inputs

if validate_inputs('/path/to/project'):
    print('✓ All checks passed - ready to migrate')
else:
    print('✗ Fix errors before migrating')
"
```

---

## Files & Scripts

### Framework Structure

```
~/kmp-migration-framework/
├── core/                      # Core modules
│   ├── harness.py            # Checkpoint/Resume system
│   ├── memory.py             # Cross-project learning
│   ├── tool_registry.py      # Tool management
│   ├── state.py              # Session state
│   ├── hooks.py              # Side-effect management
│   └── config.py             # Configuration
├── agents/                    # AI agents
│   ├── base.py               # Agent base class
│   └── planner.json          # Planner agent config
├── llm/                       # LLM integration
│   ├── invoker.py            # LLM invoker
│   ├── enhanced_invoker.py   # Health monitoring + stats
│   ├── health_checker.py     # Provider health checks
│   └── prompts.py            # Prompt management
├── skills/                    # Migration skills
│   └── hub.py                # Skills registry (7+ skills)
├── comprehension/             # Project analysis
│   └── spec_generator.py     # SPEC.md generator (PRD+DESIGN+PLAN)
├── generation/                # Code generation
│   └── batch_migration.py    # Batch migration system
├── testing/                   # Testing & verification
│   ├── metrics.py            # Traditional metrics
│   ├── llm_judge.py          # LLM-as-a-Judge
│   ├── multimodal.py         # Multi-modal evaluation
│   ├── gradle_verifier.py    # Gradle build verification
│   ├── gradle_build_script.py# Gradle script generator
│   └── build_kmp.sh          # Bash build script
├── learning/                  # Learning system
│   └── refine_skills.py      # Skill refinement
├── orchestrator.py            # Main pipeline runner
└── README.md                  # This file
```

### Key Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `orchestrator.py` | Main migration pipeline | `run_orchestrator('/path')` |
| `testing/build_kmp.sh` | Build KMP projects | `./build_kmp.sh /path` |
| `core/config.py` | Configuration management | `python -m core.config --wizard` |

### Generated Files

After migration, each project has:

| File | Purpose |
|------|---------|
| `SPEC.md` | PRD + DESIGN + PLAN (comprehensive specification) |
| `migrated_kmp_project/` | Complete KMP project |
| `COMPREHENSIVE_TEST_REPORT.md` | Quality report with scores |
| `test_results.json` | Machine-readable results |
| `MIGRATION_REPORT.md` | Migration summary |

---

## Migration Process

### 7-Phase Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: COMPREHENSION                                      │
├─────────────────────────────────────────────────────────────┤
│ • Analyze project structure                                 │
│ • Detect architecture (MVVM, MVI, Clean)                    │
│ • Identify dependencies                                     │
│ • Generate SPEC.md (PRD + DESIGN + PLAN)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: BATCH MIGRATION                                    │
├─────────────────────────────────────────────────────────────┤
│ • Group files by type (ViewModel, Activity, etc.)           │
│ • Migrate in batches (3-5x faster)                          │
│ • Apply skills (Retrofit→Ktor, Room→SQLDelight)             │
│ • Generate shared utilities                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: TEST MIGRATION                                     │
├─────────────────────────────────────────────────────────────┤
│ • Migrate unit tests                                        │
│ • Migrate instrumented tests                                │
│ • Create test plan                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3.5: GENERATE GRADLE BUILD                            │
├─────────────────────────────────────────────────────────────┤
│ • Generate settings.gradle.kts                              │
│ • Generate build.gradle.kts                                 │
│ • Generate shared/build.gradle.kts                          │
│ • Generate gradle.properties                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: COMPREHENSIVE EVALUATION                           │
├─────────────────────────────────────────────────────────────┤
│ [1/4] Traditional Metrics (compilation, coverage)           │
│ [2/4] LLM-as-a-Judge (10-criteria scoring)                  │
│ [3/4] Multi-Modal UI (accessibility, cross-platform)        │
│ [4/4] Gradle Build Verification (runs build_kmp.sh)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: LEARNING                                           │
├─────────────────────────────────────────────────────────────┤
│ • Analyze failures                                          │
│ • Update skills                                             │
│ • Record patterns                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: DELIVERY                                           │
├─────────────────────────────────────────────────────────────┤
│ • Create git branch                                         │
│ • Commit changes                                            │
│ • Create PR (optional)                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: REPORTING                                          │
├─────────────────────────────────────────────────────────────┤
│ • Generate final report                                     │
│ • Export results                                            │
│ • Save state                                                │
└─────────────────────────────────────────────────────────────┘
```

### Timeline

| Project Size | Files | Time (Mock) | Time (LLM) |
|--------------|-------|-------------|------------|
| Small | <20 | <1 min | 5-10 min |
| Medium | 20-50 | 1-2 min | 10-20 min |
| Large | 50-100 | 2-5 min | 20-40 min |
| Enterprise | 100+ | 5-10 min | 40-60 min |

---

## Output

### Migrated Project Structure

```
migrated_kmp_project/
├── shared/                          # Shared code (all platforms)
│   ├── build.gradle.kts
│   └── src/
│       ├── commonMain/kotlin/       # Common code
│       │   ├── viewmodel/
│       │   ├── data/
│       │   └── model/
│       ├── androidMain/kotlin/      # Android-specific
│       ├── iosMain/kotlin/          # iOS-specific
│       └── desktopMain/kotlin/      # Desktop-specific
├── androidApp/                      # Android application
│   ├── build.gradle.kts
│   └── src/main/
│       ├── java/
│       ├── res/
│       └── AndroidManifest.xml
├── iosApp/                          # iOS application (placeholder)
│   └── README.md
├── gradle/                          # Gradle wrapper
├── gradlew                          # Gradle wrapper script
├── settings.gradle.kts
└── build.gradle.kts
```

### Quality Scores

| Score Range | Status | Action |
|-------------|--------|--------|
| 80-100 | ✅ Excellent | Ready for production |
| 60-79 | ⚠️ Good | Minor fixes needed |
| 40-59 | ⚡ Needs Work | Significant improvements |
| 0-39 | ❌ Critical | Major refactoring required |

### Reports

**SPEC.md** - Comprehensive specification:
- PRD (Features, Models, Screens, User Flows)
- DESIGN (Architecture, Layers, KMP Structure)
- PLAN (Phases, Timeline, Risks)

**COMPREHENSIVE_TEST_REPORT.md** - Quality report:
- Traditional metrics
- LLM-as-a-Judge scores
- Multi-modal evaluation
- Gradle build results

**test_results.json** - Machine-readable:
```json
{
  "overall_score": 75.3,
  "gradle_build": {
    "success": true,
    "duration_seconds": 45.2
  },
  "llm_judge": {...},
  "traditional_metrics": {...}
}
```

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `python3: command not found` | Python not installed | Install from python.org |
| `No module named 'orchestrator'` | Wrong path | Use absolute path to framework |
| `SPEC.md not found` | Comprehension failed | Check project structure |
| `Gradle wrapper not found` | No gradlew | Script auto-downloads it |
| `Build timed out` | Large project | Increase `--timeout` |
| `Unresolved reference` | Missing dependency | Check build.gradle.kts |

### Get Help

```bash
# Validate project
python3 -c "
from core import validate_inputs
validate_inputs('/path/to/project')
"

# Check LLM health
python3 -c "
from llm import check_llm_health
check_llm_health()
"

# View build log
cat /tmp/kmp_build.log
```

---

## Examples

### Example 1: Simple App (DiceRoller)

**Input:**
```
DiceRoller/
├── app/src/main/java/com/example/diceroller/
│   ├── MainActivity.kt
│   └── Dice.kt
└── build.gradle
```

**Command:**
```bash
python3 -c "
from orchestrator import run_orchestrator
run_orchestrator('/Users/yourname/examples/DiceRoller')
"
```

**Output:**
```
✓ Migrated 3 files in 2 batches
✓ Gradle build PASSED (45.2s)
✓ Overall Score: 85.3/100
```

### Example 2: Complex App (BookKeeper)

**Input:**
```
BookKeeper/
├── app/src/main/java/com/example/bookkeeper/
│   ├── MainActivity.kt
│   ├── BookViewModel.kt
│   ├── BookRepository.kt
│   ├── BookDAO.kt
│   └── Book.kt (@Entity)
└── build.gradle (Room, Retrofit, ViewModel)
```

**Command:**
```bash
python3 -c "
from orchestrator import run_orchestrator
from llm import get_enhanced_invoker

invoker = get_enhanced_invoker('ollama', 'qwen2.5-coder:7b')
run_orchestrator('/path/to/BookKeeper', delegate_task_func=invoker)
"
```

**Output:**
```
✓ SPEC.md generated (PRD + DESIGN + PLAN)
✓ Migrated 12 files in 5 batches
✓ Skills applied: Room→SQLDelight, ViewModel→Flow
✓ Gradle build PASSED (78.5s)
✓ Overall Score: 72.1/100
```

---

## Additional Resources

| Document | Purpose |
|----------|---------|
| `README.md` | This guide |
| `BUILD_SCRIPT_GUIDE.md` | Bash build script documentation |
| `AGENTS_AND_LLM_REFINEMENT.md` | Agent & LLM system |
| `FRAMEWORK_REFINEMENT_V3.md` | Harness/Memory/Tools |
| `MIGRATE_A2K_SESSION_REVIEW.md` | Complete session review |

---

**KMP Migration Framework v3.1** - Production Ready

*Last Updated: 2026-04-13*
