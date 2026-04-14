# KMP Build Bash Script

## Overview

The `build_kmp.sh` script provides a **self-contained, portable way** to build KMP projects without requiring:
- Pre-installed Gradle
- Pre-configured Gradle wrapper
- Manual build file creation

The script automatically:
1. ✅ Checks Java installation
2. ✅ Downloads Gradle wrapper if needed
3. ✅ Generates build files if needed
4. ✅ Compiles the KMP project
5. ✅ Reports detailed errors with suggestions

## Usage

### Basic Build

```bash
./build_kmp.sh /path/to/migrated_kmp_project
```

### Options

```bash
# Clean build
./build_kmp.sh /path/to/project --clean

# Run tests
./build_kmp.sh /path/to/project --test

# Verbose output
./build_kmp.sh /path/to/project --verbose

# Custom timeout (seconds)
./build_kmp.sh /path/to/project --timeout 600

# Help
./build_kmp.sh --help
```

### Combined Options

```bash
./build_kmp.sh /path/to/project --clean --test --verbose --timeout 600
```

## Features

### 1. Automatic Gradle Wrapper Setup

If Gradle wrapper is not present, the script will:
- Download `gradle-wrapper.jar`
- Create `gradlew` script
- Create `gradle-wrapper.properties`
- Make everything executable

**No manual setup required!**

### 2. Automatic Build File Generation

If build files are missing, the script generates:
- `settings.gradle.kts`
- `build.gradle.kts` (root)
- `gradle.properties`
- `shared/build.gradle.kts`
- Directory structure

**Default versions:**
- Gradle: 8.4
- Kotlin: 1.9.20
- Ktor: 2.3.6
- Coroutines: 1.7.3
- Min SDK: 21
- Target SDK: 34

### 3. Java Version Check

Automatically checks:
- Java is installed
- Java version (warns if < 11)

### 4. Build Timeout Protection

Prevents hanging builds:
- Default timeout: 300 seconds (5 minutes)
- Configurable via `--timeout`
- Clear error message on timeout

### 5. Detailed Error Reporting

On build failure, shows:
- Compilation errors with file and line numbers
- Error type classification
- Fix suggestions
- Location of full build log

## Output Examples

### Success

```
========================================
KMP Project Build Script
========================================

[INFO] Project: /path/to/project
[INFO] Clean build: false
[INFO] Run tests: false
[INFO] Timeout: 300s

[INFO] Java version: 17
[INFO] Gradle wrapper found
[INFO] Build files already exist
[INFO] Running build...
[INFO] Executing: ./gradlew compileKotlinMetadata --no-daemon --stacktrace
[INFO] Timeout: 300s

> Task :shared:compileKotlinMetadata

[SUCCESS] Build completed successfully!
[INFO] BUILD SUCCESSFUL in 45s

========================================
[SUCCESS] BUILD SUCCESSFUL
========================================
```

### Failure

```
========================================
KMP Project Build Script
========================================

[INFO] Project: /path/to/project
...
[INFO] Running build...

> Task :shared:compileKotlinMetadata FAILED

e: file.kt:15:5 error: unresolved reference: Ktor

[ERROR] Build failed with exit code 1

[ERROR] Compilation errors:
  e: file.kt:15:5 error: unresolved reference: Ktor

[INFO] Full log: /tmp/kmp_build.log

========================================
[ERROR] BUILD FAILED
========================================
```

### Timeout

```
[ERROR] Build timed out after 300s

========================================
[ERROR] BUILD FAILED
========================================
```

## Integration with Python

### From Python Code

```python
import subprocess

result = subprocess.run(
    ['bash', 'build_kmp.sh', '/path/to/project', '--timeout', '300'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✓ Build successful")
else:
    print("✗ Build failed")
    print(result.stdout)
```

### From Testing Pipeline

```python
from testing.gradle_verifier import verify_gradle_build

result = verify_gradle_build('/path/to/project')

if result.success:
    print("✓ Gradle build passed")
else:
    print(f"✗ Build failed: {result.status.value}")
    for error in result.errors:
        print(f"  - {error.error_type}: {error.message}")
```

## Customization

### Change Default Versions

Edit the script variables at the top:

```bash
GRADLE_VERSION="8.5"
KOTLIN_VERSION="1.9.21"
TIMEOUT=600
```

### Add Custom Dependencies

Modify the `generate_build_files()` function to add your dependencies:

```bash
# In shared/build.gradle.kts generation
implementation("io.ktor:ktor-client-logging:2.3.6")
```

### Change Build Task

Modify the `build_project()` function:

```bash
# Full build instead of just metadata
build_cmd="$gradle_cmd build --no-daemon"
```

## Troubleshooting

### "Java is not installed"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install openjdk-11-jdk

# macOS
brew install openjdk@11

# Verify
java -version
```

### "Build timed out"

**Solutions:**
1. Increase timeout: `--timeout 600`
2. Check for infinite loops in build script
3. Run with `--verbose` to see progress

### "Unresolved reference" errors

**Solutions:**
1. Check import statements
2. Ensure dependencies are in `build.gradle.kts`
3. Run `--clean` to force dependency download

### "Gradle wrapper not found"

The script should auto-download it. If not:

```bash
# Manual download
cd /path/to/project
gradle wrapper --gradle-version 8.4
```

## Performance Tips

1. **Use `--clean` sparingly** - Incremental builds are faster
2. **Enable Gradle cache** - Already enabled in generated `gradle.properties`
3. **Use parallel builds** - Already enabled by default
4. **Increase JVM heap** - Set in `gradle.properties`:
   ```
   org.gradle.jvmargs=-Xmx4096m
   ```

## File Locations

| File | Purpose |
|------|---------|
| `build_kmp.sh` | Main build script |
| `/tmp/kmp_build.log` | Build log (on failure) |
| `gradle/wrapper/` | Gradle wrapper files |
| `shared/build.gradle.kts` | KMP module build |

## Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Bash | 3.0 | 4.0+ |
| Java | 11 | 17+ |
| Disk Space | 500MB | 2GB+ |
| Memory | 2GB | 4GB+ |

## License

MIT License - Free to use and modify

---

*build_kmp.sh v1.0 - Portable KMP Build Script*
