#!/bin/bash

# KMP Project Build Script
# Automatically builds Kotlin Multiplatform projects with Gradle wrapper
#
# Usage:
#   ./build_kmp.sh [project_path] [options]
#
# Options:
#   --clean         Clean build
#   --test          Run tests
#   --verbose       Verbose output
#   --timeout SEC   Build timeout (default: 300)
#   --help          Show this help

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_PATH=""
CLEAN_BUILD=false
RUN_TESTS=false
VERBOSE=false
TIMEOUT=300
GRADLE_VERSION="8.4"
KOTLIN_VERSION="1.9.20"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            head -15 $0 | tail -12
            exit 0
            ;;
        *)
            if [[ -z "$PROJECT_PATH" ]]; then
                PROJECT_PATH="$1"
            fi
            shift
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_java() {
    if ! command -v java &> /dev/null; then
        log_error "Java is not installed. Please install Java 11 or higher."
        echo "  Ubuntu: sudo apt install openjdk-11-jdk"
        echo "  macOS:  brew install openjdk@11"
        exit 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [[ $JAVA_VERSION -lt 11 ]]; then
        log_warning "Java version is $JAVA_VERSION, but Java 11+ is recommended"
    fi
    
    log_info "Java version: $JAVA_VERSION"
}

setup_gradle_wrapper() {
    local project_dir=$1
    
    # Check if gradlew exists
    if [[ -f "$project_dir/gradlew" ]]; then
        log_info "Gradle wrapper found"
        chmod +x "$project_dir/gradlew"
        return 0
    fi
    
    # Check if gradle is installed
    if command -v gradle &> /dev/null; then
        log_info "Generating Gradle wrapper..."
        cd "$project_dir"
        gradle wrapper --gradle-version $GRADLE_VERSION
        chmod +x gradlew
        cd - > /dev/null
        return 0
    fi
    
    # Download Gradle wrapper
    log_info "Downloading Gradle wrapper..."
    
    # Create gradle/wrapper directory
    mkdir -p "$project_dir/gradle/wrapper"
    
    # Download gradle-wrapper.jar
    WRAPPER_JAR="$project_dir/gradle/wrapper/gradle-wrapper.jar"
    if [[ ! -f "$WRAPPER_JAR" ]]; then
        log_info "Downloading gradle-wrapper.jar..."
        curl -L -o "$WRAPPER_JAR" \
            "https://github.com/gradle/gradle/raw/v$GRADLE_VERSION/gradle/wrapper/gradle-wrapper.jar" \
            2>/dev/null || {
            log_error "Failed to download gradle-wrapper.jar"
            return 1
        }
    fi
    
    # Create gradlew script
    GRADLEW="$project_dir/gradlew"
    if [[ ! -f "$GRADLEW" ]]; then
        cat > "$GRADLEW" << 'GRADLEW_SCRIPT'
#!/bin/sh
# Gradle wrapper script
APP_NAME="Gradle"
APP_BASE_NAME=`basename "$0"`
DIRNAME=`dirname "$0"`
JAR_PATH="$DIRNAME/gradle/wrapper/gradle-wrapper.jar"
exec java -jar "$JAR_PATH" "$@"
GRADLEW_SCRIPT
        chmod +x "$GRADLEW"
    fi
    
    # Create gradle-wrapper.properties
    PROPS_FILE="$project_dir/gradle/wrapper/gradle-wrapper.properties"
    cat > "$PROPS_FILE" << PROPS
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-$GRADLE_VERSION-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
PROPS
    
    log_success "Gradle wrapper setup complete"
}

generate_build_files() {
    local project_dir=$1
    
    # Check if build files exist
    if [[ -f "$project_dir/shared/build.gradle.kts" ]]; then
        log_info "Build files already exist"
        return 0
    fi
    
    log_info "Generating build files..."
    
    # Create directory structure
    mkdir -p "$project_dir/shared/src/commonMain/kotlin"
    mkdir -p "$project_dir/shared/src/androidMain/kotlin"
    mkdir -p "$project_dir/shared/src/iosMain/kotlin"
    mkdir -p "$project_dir/androidApp/src/main/java"
    
    # Generate settings.gradle.kts
    cat > "$project_dir/settings.gradle.kts" << SETTINGS
pluginManagement {
    repositories {
        google()
        gradlePluginPortal()
        mavenCentral()
    }
    plugins {
        kotlin("multiplatform") version "$KOTLIN_VERSION" apply false
        kotlin("android") version "$KOTLIN_VERSION" apply false
        id("com.android.application") version "8.1.0" apply false
        id("com.android.library") version "8.1.0" apply false
    }
}

dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "$(basename $project_dir)"
include(":shared")
include(":androidApp")
SETTINGS
    
    # Generate build.gradle.kts (root)
    cat > "$project_dir/build.gradle.kts" << 'ROOT_BUILD'
plugins {
    kotlin("multiplatform") version "1.9.20" apply false
    kotlin("android") version "1.9.20" apply false
    id("com.android.application") version "8.1.0" apply false
    id("com.android.library") version "8.1.0" apply false
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}
ROOT_BUILD
    
    # Generate gradle.properties
    cat > "$project_dir/gradle.properties" << 'GRADLE_PROPS'
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official
kotlin.mpp.enableCInteropCommonization=true
GRADLE_PROPS
    
    # Generate shared/build.gradle.kts
    cat > "$project_dir/shared/build.gradle.kts" << 'SHARED_BUILD'
plugins {
    kotlin("multiplatform")
    id("com.android.library")
}

kotlin {
    androidTarget()
    iosX64()
    iosArm64()
    iosSimulatorArm64()
    
    sourceSets {
        commonMain {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
                implementation("io.ktor:ktor-client-core:2.3.6")
            }
        }
        androidMain {
            dependencies {
                implementation("io.ktor:ktor-client-android:2.3.6")
            }
        }
        iosMain {
            dependencies {
                implementation("io.ktor:ktor-client-darwin:2.3.6")
            }
        }
    }
}

android {
    namespace = "com.example.shared"
    compileSdk = 34
    
    defaultConfig {
        minSdk = 21
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}
SHARED_BUILD
    
    log_success "Build files generated"
}

build_project() {
    local project_dir=$1
    local gradle_cmd="$project_dir/gradlew"
    
    # Build command
    local build_cmd="$gradle_cmd compileKotlinMetadata --no-daemon --stacktrace"
    
    if [[ "$CLEAN_BUILD" == true ]]; then
        build_cmd="$gradle_cmd clean compileKotlinMetadata --no-daemon --stacktrace"
        log_info "Running clean build..."
    else
        log_info "Running build..."
    fi
    
    if [[ "$RUN_TESTS" == true ]]; then
        build_cmd="$build_cmd test"
        log_info "Tests will be run..."
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        build_cmd="$build_cmd --info"
    fi
    
    # Run build with timeout
    log_info "Executing: $build_cmd"
    log_info "Timeout: ${TIMEOUT}s"
    
    cd "$project_dir"
    
    if timeout $TIMEOUT bash -c "$build_cmd" 2>&1 | tee /tmp/kmp_build.log; then
        log_success "Build completed successfully!"
        
        # Show summary
        if [[ -f /tmp/kmp_build.log ]]; then
            BUILD_TIME=$(grep -i "BUILD SUCCESSFUL" /tmp/kmp_build.log | head -1 || echo "Build successful")
            echo ""
            log_info "$BUILD_TIME"
        fi
        
        cd - > /dev/null
        return 0
    else
        EXIT_CODE=$?
        cd - > /dev/null
        
        if [[ $EXIT_CODE -eq 124 ]]; then
            log_error "Build timed out after ${TIMEOUT}s"
        else
            log_error "Build failed with exit code $EXIT_CODE"
        fi
        
        # Show errors
        if [[ -f /tmp/kmp_build.log ]]; then
            echo ""
            log_error "Compilation errors:"
            grep -E "^e:|error:|FAILED" /tmp/kmp_build.log | head -20
            echo ""
            log_info "Full log: /tmp/kmp_build.log"
        fi
        
        return 1
    fi
}

# Main
main() {
    echo "========================================"
    echo "KMP Project Build Script"
    echo "========================================"
    echo ""
    
    # Validate project path
    if [[ -z "$PROJECT_PATH" ]]; then
        log_error "No project path specified"
        echo "Usage: $0 <project_path> [options]"
        echo "Use --help for options"
        exit 1
    fi
    
    if [[ ! -d "$PROJECT_PATH" ]]; then
        log_error "Project path does not exist: $PROJECT_PATH"
        exit 1
    fi
    
    log_info "Project: $PROJECT_PATH"
    log_info "Clean build: $CLEAN_BUILD"
    log_info "Run tests: $RUN_TESTS"
    log_info "Timeout: ${TIMEOUT}s"
    echo ""
    
    # Check Java
    check_java
    echo ""
    
    # Setup Gradle wrapper
    setup_gradle_wrapper "$PROJECT_PATH" || exit 1
    echo ""
    
    # Generate build files if needed
    generate_build_files "$PROJECT_PATH"
    echo ""
    
    # Build project
    build_project "$PROJECT_PATH"
    BUILD_RESULT=$?
    
    echo ""
    echo "========================================"
    if [[ $BUILD_RESULT -eq 0 ]]; then
        log_success "BUILD SUCCESSFUL"
    else
        log_error "BUILD FAILED"
    fi
    echo "========================================"
    
    exit $BUILD_RESULT
}

# Run main
main
