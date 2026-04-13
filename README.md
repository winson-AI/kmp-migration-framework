# KMP Migration Framework - Freshman Guide

**No experience needed. Just follow these steps.**

---

## What You Need (INPUT)

### 1. Your Android Project

Your project must look like this:

```
/your/project/path/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/          ← Your Kotlin/Java files here
│   │   │   │   └── com/
│   │   │   │       └── example/
│   │   │   │           ├── MainActivity.kt
│   │   │   │           └── OtherFile.kt
│   │   │   └── AndroidManifest.xml
│   │   ├── test/              ← Your tests (optional)
│   │   └── androidTest/       ← Your tests (optional)
│   └── build.gradle           ← Required
├── settings.gradle            ← Required
└── build.gradle               ← Required
```

### 2. Know Your Project Path

Find the **full path** to your project:

**On Mac/Linux:**
```bash
cd /your/project/path
pwd
```

**Output will be like:**
```
/Users/yourname/CodeBase/BookKeeper
```

**Copy this path!** You need it for the command.

---

## What You Get (OUTPUT)

After migration, you will have:

```
/your/project/path/
├── migrated_kmp_project/      ← YOUR NEW KMP PROJECT!
│   ├── shared/
│   │   ├── build.gradle.kts
│   │   └── src/
│   │       ├── commonMain/kotlin/    ← Shared code here
│   │       ├── androidMain/kotlin/   ← Android code here
│   │       └── iosMain/kotlin/       ← iOS code here
│   ├── androidApp/
│   │   └── src/main/java/
│   └── ARCHITECTURE.md
├── SPEC.md                    ← What was found
├── COMPREHENSIVE_TEST_REPORT.md  ← Quality score
└── test_results.json          ← Detailed results
```

---

## Commands to Run (COPY & PASTE)

### Step 1: Open Terminal

**Mac:** Press `Cmd + Space`, type "Terminal", press Enter

**Windows:** Press `Win + R`, type "cmd", press Enter

**Linux:** Press `Ctrl + Alt + T`

### Step 2: Check Python

Copy and paste this command:

```bash
python3 --version
```

**Expected output:**
```
Python 3.9.x  (or higher)
```

If you see an error, install Python from https://www.python.org/

### Step 3: Run the Migration

**Copy this command:**

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/YOUR/PROJECT/PATH/HERE')
"
```

**IMPORTANT:** Replace `/YOUR/PROJECT/PATH/HERE` with your actual project path!

**Example:**
```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from orchestrator import run_orchestrator
run_orchestrator('/Users/winson/CodeBase/Offline/BookKeeper')
"
```

### Step 4: Wait for Completion

You will see output like this:

```
--- Phase 1: Comprehension ---
SPEC.md generated successfully at /Users/winson/CodeBase/Offline/BookKeeper/SPEC.md

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

### Step 5: Check Your KMP Project

```bash
cd /YOUR/PROJECT/PATH/HERE/migrated_kmp_project
ls -la
```

You should see:
```
shared/
androidApp/
ARCHITECTURE.md
```

---

## Quick Troubleshooting

### Error: "python3: command not found"

**Fix:**
```bash
# Try python instead
python --version
```

Then use `python` instead of `python3` in the command.

### Error: "No module named 'orchestrator'"

**Fix:** Make sure the path is correct:

```bash
# Check if framework exists
ls /Users/winson/kmp-migration-framework
```

If not found, update the path in the command to where you installed the framework.

### Error: "SPEC.md not found"

**Fix:** Run comprehension first:

```bash
python3 -c "
import sys
sys.path.append('/Users/winson/kmp-migration-framework')
from comprehension.analyze_project import analyze_android_project
analyze_android_project('/YOUR/PROJECT/PATH/HERE')
"
```

Then run the full migration again.

### Error: "No such file or directory"

**Fix:** Your project path is wrong.

1. Navigate to your project:
   ```bash
   cd /your/project/path
   ```

2. Get the full path:
   ```bash
   pwd
   ```

3. Copy that path into the migration command.

---

## One-Line Command (Simplest)

If you want the absolute simplest command, copy this:

```bash
cd /Users/winson/kmp-migration-framework && python3 -c "from orchestrator import run_orchestrator; run_orchestrator('/YOUR/PROJECT/PATH/HERE')"
```

**Just replace `/YOUR/PROJECT/PATH/HERE` with your actual path!**

---

## Example: Complete Session

Here's what a complete migration session looks like:

```bash
# 1. Open terminal

# 2. Check Python
winson@MacBook ~ % python3 --version
Python 3.9.16

# 3. Find project path
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

| What | Where |
|------|-------|
| **Input** | Your Android project path (e.g., `/Users/name/Project`) |
| **Command** | `python3 -c "from orchestrator import run_orchestrator; run_orchestrator('/path/to/project')"` |
| **Output** | `migrated_kmp_project/` folder in your project directory |

---

## Need Help?

1. **Check your project path** - Most errors are wrong paths
2. **Check Python version** - Must be 3.9 or higher
3. **Check framework path** - Must be `/Users/winson/kmp-migration-framework`

---

*Freshman Guide v1.0 - Just copy, paste, replace path, run!*
