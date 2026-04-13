# Custom Inputs Guide

What you need to provide to use the KMP Migration Framework.

---

## Quick Reference

| Input | Required? | Default | How to Provide |
|-------|-----------|---------|----------------|
| **Project Path** | ✓ Required | None | Command line argument |
| **Python 3.9+** | ✓ Required | N/A | Install from python.org |
| **Framework Path** | ✓ Required | `~/kmp-migration-framework/` | Clone or download |
| **LLM Provider** | Optional | Mock mode | Environment variable or config |
| **API Key** | Optional | N/A | Environment variable |
| **Output Path** | Optional | `migrated_kmp_project/` | Config file |

---

## Required Inputs

### 1. Project Path

**What:** Path to your Android project directory

**Format:** Absolute path (full path from root)

**Examples:**
```
/Users/yourname/CodeBase/MyAndroidApp
/home/yourname/projects/MyApp
C:\Users\yourname\CodeBase\MyAndroidApp
```

**How to get:**
```bash
cd /path/to/your/project
pwd  # Mac/Linux
cd   # Windows (shows current directory)
```

**Validation:**
- Must exist
- Must be a directory (not a file)
- Must have `app/` subdirectory
- Must have `build.gradle` and `settings.gradle`
- Must have `.kt` or `.java` files

**Validate:**
```bash
python3 -c "
from core.input_validator import validate_inputs
validate_inputs('/your/project/path')
"
```

### 2. Python 3.9+

**What:** Python interpreter version

**Required:** 3.9 or higher

**Check:**
```bash
python3 --version
# Should show: Python 3.9.x or higher
```

**Install:**
- Mac: `brew install python@3.9`
- Windows: Download from https://www.python.org/
- Linux: `sudo apt install python3.9`

### 3. Framework Installation

**What:** KMP Migration Framework files

**Default Location:** `~/kmp-migration-framework/`

**Check:**
```bash
ls ~/kmp-migration-framework/orchestrator.py
```

**Required Files:**
```
~/kmp-migration-framework/
├── orchestrator.py          ✓ Required
├── core/
│   ├── config.py            ✓ Required
│   ├── state.py             ✓ Required
│   ├── hooks.py             ✓ Required
│   └── input_validator.py   ✓ Required
├── generation/
│   └── batch_migration.py   ✓ Required
└── testing/
    └── comprehensive.py     ✓ Required
```

---

## Optional Inputs

### 4. LLM Provider

**What:** AI provider for code migration

**Options:**

| Provider | Cost | Setup | Speed |
|----------|------|-------|-------|
| **Ollama** | Free | `ollama pull qwen2.5-coder:7b` | Fast |
| **Dashscope** | Paid | Get API key | Medium |
| **OpenAI** | Paid | Get API key | Medium |
| **Anthropic** | Paid | Get API key | Medium |
| **Mock** | Free | None | Instant |

**Configure:**

Option A - Environment Variable:
```bash
export KMP_LLM_PROVIDER=ollama
export KMP_LLM_MODEL=qwen2.5-coder:7b
```

Option B - Config File:
```bash
python3 -m core.config --wizard
```

Option C - Command Line:
```python
from llm import LLMInvoker, LLMProvider
invoker = LLMInvoker(provider=LLMProvider.OLLAMA)
```

**Default:** Ollama (if available), otherwise Mock

### 5. API Key

**What:** Authentication for cloud LLM providers

**Required For:**
- Dashscope (Alibaba Cloud)
- OpenAI
- Anthropic

**Not Required For:**
- Ollama (local)
- Mock mode

**Set:**
```bash
# Dashscope
export DASHSCOPE_API_KEY="sk-your-key-here"

# OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Security:**
- Never commit API keys to git
- Use environment variables
- Keys are masked in logs (`***`)

### 6. Output Path

**What:** Where to save migrated KMP project

**Default:** `{project_path}/migrated_kmp_project/`

**Customize:**
```python
from core.config import MigrationConfig

config = MigrationConfig()
config.output_path = '/custom/output/path'
```

---

## Configuration File

### Location

```
~/.hermes/kmp-migration/config.json
```

### Create Config

```bash
# Interactive wizard
python3 -m core.config --wizard

# Show current config
python3 -m core.config --show

# Reset to defaults
python3 -m core.config --reset
```

### Config File Format

```json
{
  "project_path": "/Users/yourname/CodeBase/MyApp",
  "output_path": null,
  "llm": {
    "provider": "ollama",
    "model": "qwen2.5-coder:7b",
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "mode": "full",
  "dry_run": true,
  "check_health": true,
  "enable_testing": true,
  "enable_learning": true,
  "skip_patterns": ["build/", "*.java"],
  "include_patterns": ["*.kt"]
}
```

---

## Command Line Inputs

### Basic Migration

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/path/to/project')
"
```

### With Custom Config

```python
from orchestrator import run_orchestrator
from core.config import MigrationConfig, LLMProvider

config = MigrationConfig()
config.project_path = '/path/to/project'
config.llm.provider = LLMProvider.DASHSCOPE
config.llm.model = 'qwen-max'
config.dry_run = False

run_orchestrator('/path/to/project', config=config)
```

### With Custom LLM Invoker

```python
from orchestrator import run_orchestrator
from llm import LLMInvoker, LLMProvider

invoker = LLMInvoker(
    provider=LLMProvider.OLLAMA,
    model='qwen2.5-coder:7b',
    base_url='http://localhost:11434'
)

run_orchestrator('/path/to/project', delegate_task_func=invoker)
```

---

## Input Validation

### Validate Before Migration

```bash
python3 -c "
from core.input_validator import validate_inputs
validate_inputs('/path/to/project')
"
```

### Validation Checks

| Check | Severity | Fix |
|-------|----------|-----|
| Python version | Error | Install Python 3.9+ |
| Framework files | Error | Reinstall framework |
| Project path exists | Error | Check path |
| Project structure | Error | Ensure Android project |
| Gradle files | Warning | Add build.gradle |
| LLM availability | Warning | Configure LLM or use mock |

### Validation Output

**Pass:**
```
STATUS: ✓ ALL CHECKS PASSED - Ready to migrate!
```

**Fail:**
```
❌ ERRORS (must fix):
  • Python Version: Python 3.8 (need 3.9+)
    Fix: Install Python 3.9+ from https://www.python.org/
  • Project Path: Path does not exist: /wrong/path
    Fix: Check path: cd /wrong/path

STATUS: ❌ 2 error(s) - Must fix before migrating
```

---

## Troubleshooting Inputs

### "Project path not found"

**Cause:** Wrong path

**Fix:**
```bash
cd /path/to/project
pwd  # Copy this exact path
```

### "Python version too old"

**Cause:** Python < 3.9

**Fix:**
```bash
# Mac
brew install python@3.9

# Ubuntu
sudo apt install python3.9

# Check
python3 --version
```

### "Framework not installed"

**Cause:** Missing framework files

**Fix:**
```bash
# Clone framework
git clone https://github.com/your-repo/kmp-migration-framework
cd kmp-migration-framework

# Verify
ls orchestrator.py
```

### "No LLM available"

**Cause:** No LLM configured

**Fix (Option 1 - Use Mock):**
```bash
# Just proceed - mock mode works fine
python3 -c "from orchestrator import run_orchestrator; run_orchestrator('/path')"
```

**Fix (Option 2 - Install Ollama):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
```

**Fix (Option 3 - Use Cloud):**
```bash
export DASHSCOPE_API_KEY="sk-your-key"
```

---

## Summary

### Minimum Required

```
1. Project path (absolute path to Android project)
2. Python 3.9+
3. Framework installed
```

### Recommended

```
4. LLM provider (Ollama recommended for free local use)
5. Configuration file (for repeated use)
```

### Optional

```
6. Custom output path
7. Custom library mappings
8. Custom skip/include patterns
```

---

*Custom Inputs Guide v1.0 - Know What You Need*
