# KMP Migration Framework - Freshman Guide

**No experience needed. Just follow these steps.**

---

## What You'll Do (3 Steps)

```
Step 1: Check your computer has what we need (2 minutes)
   ↓
Step 2: Find your Android project path (1 minute)
   ↓
Step 3: Run one command (wait 1-5 minutes)
   ↓
Done! You have a KMP project!
```

---

## Step 1: Check Your Computer

### Open Terminal

**Mac:** Press `Command + Space`, type "Terminal", press Enter

**Windows:** Press `Windows + R`, type "cmd", press Enter

**Linux:** Press `Ctrl + Alt + T`

### Check Python

Copy and paste this into terminal:

```bash
python3 --version
```

**You should see:**
```
Python 3.9.x  (or higher like 3.10, 3.11, 3.12)
```

**If you see an error** like "command not found":
- Go to https://www.python.org/
- Download and install Python
- Come back and try again

### Check Framework

Copy and paste this:

```bash
ls ~/kmp-migration-framework/orchestrator.py
```

**You should see:**
```
/Users/yourname/kmp-migration-framework/orchestrator.py
```

**If you see "No such file":**
- The framework is not installed
- Ask your instructor or clone from repository

---

## Step 2: Find Your Project Path

### What You Need

You need an **Android project**. It should look like this:

```
MyAndroidApp/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/          ← Your code is here
│   │       │   └── com/
│   │       │       └── example/
│   │       │           ├── MainActivity.kt
│   │       │           └── OtherFile.kt
│   │       └── AndroidManifest.xml
│   └── build.gradle
├── settings.gradle
└── build.gradle
```

### Find the Path

**Method 1: If you know where your project is**

1. Open terminal
2. Type: `cd ` (with space after cd)
3. Drag your project folder into terminal window
4. Press Enter
5. Type: `pwd`
6. Press Enter
7. **Copy the path it shows**

**Example:**
```bash
cd /Users/yourname/CodeBase/BookKeeper
pwd
# Output: /Users/yourname/CodeBase/BookKeeper
# ← COPY THIS!
```

**Method 2: If you're not sure**

Look for a folder that has:
- `app/` folder inside
- `build.gradle` file
- `settings.gradle` file

Common locations:
- `~/AndroidStudioProjects/YourApp/`
- `~/CodeBase/YourApp/`
- `~/projects/YourApp/`

---

## Step 3: Run the Migration

### Copy This Command

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('YOUR_PATH_HERE')
"
```

### Replace YOUR_PATH_HERE

Replace `YOUR_PATH_HERE` with the path you copied in Step 2.

**Example:**

If your path is `/Users/yourname/CodeBase/BookKeeper`

Change the command to:

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/Users/yourname/CodeBase/BookKeeper')
"
```

### Run the Command

1. Copy the entire command (all 5 lines)
2. Paste into terminal
3. Press Enter

### Wait for It to Finish

You'll see output like this:

```
============================================================
INPUT VALIDATION
============================================================

✓ PASSED:
  • Python Version: Python 3.11 ✓
  • Framework Installation: All required files present ✓
  • Project Path: /Users/yourname/CodeBase/BookKeeper ✓
  • Project Structure: app/ directory ✓, 24 files ✓

STATUS: ✓ ALL CHECKS PASSED - Ready to migrate!
============================================================

--- Phase 1: Comprehension ---
SPEC.md generated successfully

--- Phase 2: Batch Code Migration ---
✓ Found 24 source files
✓ Identified 7 file groups
✓ Migrated 24 files in 7 batches

--- Phase 3: Test Migration ---
Test migration plan generated

--- Phase 4: Comprehensive Evaluation ---
Overall Score: 75.3/100

--- Phase 5: Learning ---

--- Phase 6: Delivery ---

--- Phase 7: Reporting ---
Migration report generated

--- Pipeline Finished ---
```

**This takes 1-5 minutes depending on project size.**

---

## Step 4: Check Your KMP Project

### Find the Migrated Project

After migration finishes, you'll have a **new folder**:

```
YourOriginalProject/
├── migrated_kmp_project/    ← NEW! Your KMP project is here
│   ├── shared/
│   │   └── src/
│   │       └── commonMain/
│   │           └── kotlin/   ← Your migrated code
│   └── androidApp/
├── SPEC.md
└── COMPREHENSIVE_TEST_REPORT.md
```

### Check It

```bash
cd /Users/yourname/CodeBase/BookKeeper/migrated_kmp_project
ls -la
```

You should see:
```
shared/
androidApp/
ARCHITECTURE.md
```

### View Migrated Files

```bash
find shared/src/commonMain/kotlin -name "*.kt"
```

This shows all your migrated Kotlin files!

---

## Common Problems & Fixes

### Problem 1: "python3: command not found"

**Fix:**
```bash
# Try python instead
python --version
```

If that works, use `python` instead of `python3` in all commands.

If both fail:
- Install Python from https://www.python.org/

### Problem 2: "No module named 'orchestrator'"

**Fix:** The framework path is wrong.

Check if framework exists:
```bash
ls ~/kmp-migration-framework/orchestrator.py
```

If it shows "No such file":
- The framework is not at the expected location
- Find where it is: `find ~ -name "orchestrator.py"`
- Use the correct path in your command

### Problem 3: "Path does not exist"

**Fix:** Your project path is wrong.

1. Navigate to your project:
   ```bash
   cd /path/to/your/project
   ```

2. Check it's the right place:
   ```bash
   ls
   # Should show: app/ build.gradle settings.gradle
   ```

3. Get the correct path:
   ```bash
   pwd
   ```

4. Use that path in the migration command

### Problem 4: "No LLM available"

**This is OK!** It just means you're using mock mode.

The migration will still work, but with placeholder code.

**To use real AI (optional):**

Option A - Ollama (free):
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
```

Option B - Dashscope (paid):
```bash
export DASHSCOPE_API_KEY="sk-your-key-here"
```

### Problem 5: Migration takes too long

**Normal time:** 1-5 minutes for typical projects

**If it's stuck:**
- Press `Ctrl + C` to stop
- Check your project size (large projects take longer)
- Try with a smaller project first

---

## Quick Reference

### The One Command You Need

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/path/to/your/android/project')
"
```

### What You Get

| File | What It Is |
|------|------------|
| `migrated_kmp_project/` | **Your new KMP project!** |
| `SPEC.md` | What was found in your project |
| `COMPREHENSIVE_TEST_REPORT.md` | Quality score and issues |
| `test_results.json` | Detailed results |

### Where to Find Things

| What | Where |
|------|-------|
| Your KMP code | `migrated_kmp_project/shared/src/commonMain/kotlin/` |
| Android code | `migrated_kmp_project/androidApp/src/main/java/` |
| Reports | Original project folder |

---

## Example: Complete Session

Here's what a real migration looks like:

```bash
# 1. Open terminal

# 2. Check Python
winson@MacBook ~ % python3 --version
Python 3.11.6

# 3. Find project
winson@MacBook ~ % cd CodeBase/Offline/BookKeeper
winson@MacBook BookKeeper % pwd
/Users/winson/CodeBase/Offline/BookKeeper

# 4. Run migration (COPY THIS, REPLACE PATH)
winson@MacBook BookKeeper % python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/Users/winson/CodeBase/Offline/BookKeeper')
"

# 5. Wait for output...
============================================================
INPUT VALIDATION
============================================================
STATUS: ✓ ALL CHECKS PASSED - Ready to migrate!

--- Phase 1: Comprehension ---
SPEC.md generated successfully

--- Phase 2: Batch Code Migration ---
✓ Found 24 source files
✓ Migrated 24 files in 7 batches

--- Pipeline Finished ---

# 6. Check results
winson@MacBook BookKeeper % ls
SPEC.md  migrated_kmp_project/  COMPREHENSIVE_TEST_REPORT.md

# 7. Done! Your KMP project is in migrated_kmp_project/
```

---

## Summary

| What | Value |
|------|-------|
| **Input** | Path to your Android project |
| **Command** | `python3 -c "from orchestrator import run_orchestrator; run_orchestrator('/path')"` |
| **Output** | `migrated_kmp_project/` folder |
| **Time** | 1-5 minutes |
| **Difficulty** | Easy (just copy-paste) |

---

## Need Help?

1. **Check Python:** `python3 --version` (need 3.9+)
2. **Check Framework:** `ls ~/kmp-migration-framework/orchestrator.py`
3. **Check Project:** `ls /your/project/path` (should show app/, build.gradle)
4. **Validate:** Run the validation command before migration

---

*Freshman Guide v3.0 - Just 3 Steps: Check, Find Path, Run Command*
