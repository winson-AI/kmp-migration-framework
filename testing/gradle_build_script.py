"""
Gradle Build Script Generator

Generates configurable Gradle build scripts for KMP projects with:
- Configurable default versions (Gradle, Kotlin, etc.)
- Basic Gradle setup (no wrapper required)
- Platform-specific configurations
- Dependency management

Usage:
    from testing.gradle_build_script import GradleBuildGenerator
    
    generator = GradleBuildGenerator()
    generator.generate_for_project('/path/to/migrated_kmp_project')
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class GradleVersions:
    """Default versions for Gradle build."""
    gradle: str = "8.4"
    kotlin: str = "1.9.20"
    android_gradle: str = "8.1.0"
    kmp_plugin: str = "1.9.20"
    
    # KMP libraries
    kotlinx_coroutines: str = "1.7.3"
    kotlinx_serialization: str = "1.6.0"
    sql_delight: str = "2.0.0"
    ktor: str = "2.3.6"
    koin: str = "3.5.0"
    
    # Android
    min_sdk: int = 21
    target_sdk: int = 34
    compile_sdk: int = 34
    
    # Testing
    junit: str = "4.13.2"
    kotlin_test: str = "1.9.20"
    
    def to_dict(self) -> Dict:
        return {
            'gradle': self.gradle,
            'kotlin': self.kotlin,
            'android_gradle': self.android_gradle,
            'kmp_plugin': self.kmp_plugin,
            'kotlinx_coroutines': self.kotlinx_coroutines,
            'kotlinx_serialization': self.kotlinx_serialization,
            'sql_delight': self.sql_delight,
            'ktor': self.ktor,
            'koin': self.koin,
            'min_sdk': self.min_sdk,
            'target_sdk': self.target_sdk,
            'compile_sdk': self.compile_sdk,
            'junit': self.junit,
            'kotlin_test': self.kotlin_test
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GradleVersions':
        return cls(**data)


@dataclass
class BuildConfig:
    """Build configuration for a KMP project."""
    project_name: str
    group_id: str = "com.example"
    version: str = "1.0.0"
    versions: GradleVersions = field(default_factory=GradleVersions)
    enable_android: bool = True
    enable_ios: bool = True
    enable_desktop: bool = False
    enable_web: bool = False
    custom_dependencies: List[Dict] = field(default_factory=list)


class GradleBuildGenerator:
    """
    Generate Gradle build scripts for KMP projects.
    """
    
    def __init__(self, config: Optional[BuildConfig] = None):
        self.config = config or BuildConfig(project_name="KMPProject")
        self.versions = self.config.versions
    
    def generate_for_project(self, project_path: str, config: Optional[BuildConfig] = None):
        """
        Generate all Gradle files for a KMP project.
        
        Args:
            project_path: Path to migrated KMP project
            config: Optional build configuration
        """
        if config:
            self.config = config
            self.versions = config.versions
        
        logger.info(f"Generating Gradle files for {project_path}")
        
        # Generate root build files
        self._generate_settings_gradle(project_path)
        self._generate_root_build_gradle(project_path)
        self._generate_gradle_properties(project_path)
        
        # Generate shared module
        self._generate_shared_module(project_path)
        
        # Generate Android app module (if enabled)
        if self.config.enable_android:
            self._generate_android_module(project_path)
        
        # Generate iOS project (placeholder)
        if self.config.enable_ios:
            self._generate_ios_placeholder(project_path)
        
        # Generate Desktop module (if enabled)
        if self.config.enable_desktop:
            self._generate_desktop_module(project_path)
        
        logger.info(f"Gradle files generated successfully")
        print(f"✓ Gradle build scripts generated for {project_path}")
    
    def _generate_settings_gradle(self, project_path: str):
        """Generate settings.gradle.kts."""
        content = f'''pluginManagement {{
    repositories {{
        google()
        gradlePluginPortal()
        mavenCentral()
    }}
    
    plugins {{
        kotlin("multiplatform") version "{self.versions.kmp_plugin}" apply false
        kotlin("android") version "{self.versions.kmp_plugin}" apply false
        id("com.android.application") version "{self.versions.android_gradle}" apply false
        id("com.android.library") version "{self.versions.android_gradle}" apply false
    }}
}}

dependencyResolutionManagement {{
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{self.config.project_name}"

include(":shared")
'''
        
        if self.config.enable_android:
            content += 'include(":androidApp")\n'
        
        if self.config.enable_desktop:
            content += 'include(":desktopApp")\n'
        
        settings_file = os.path.join(project_path, 'settings.gradle.kts')
        with open(settings_file, 'w') as f:
            f.write(content)
        
        # Also create settings.gradle (Groovy version)
        groovy_content = f'''pluginManagement {{
    repositories {{
        google()
        gradlePluginPortal()
        mavenCentral()
    }}
}}

include ':shared'
'''
        if self.config.enable_android:
            groovy_content += "include ':androidApp'\n"
        
        groovy_file = os.path.join(project_path, 'settings.gradle')
        with open(groovy_file, 'w') as f:
            f.write(groovy_content)
    
    def _generate_root_build_gradle(self, project_path: str):
        """Generate root build.gradle.kts."""
        content = f'''// Top-level build file
plugins {{
    kotlin("multiplatform") version "{self.versions.kmp_plugin}" apply false
    kotlin("android") version "{self.versions.kmp_plugin}" apply false
    id("com.android.application") version "{self.versions.android_gradle}" apply false
    id("com.android.library") version "{self.versions.android_gradle}" apply false
}}

tasks.register("clean", Delete::class) {{
    delete(rootProject.buildDir)
}}
'''
        build_file = os.path.join(project_path, 'build.gradle.kts')
        with open(build_file, 'w') as f:
            f.write(content)
        
        # Also create build.gradle (Groovy version)
        groovy_content = f'''// Top-level build file
buildscript {{
    ext.kotlin_version = '{self.versions.kotlin}'
    ext.android_gradle_version = '{self.versions.android_gradle}'
    
    repositories {{
        google()
        mavenCentral()
    }}
    dependencies {{
        classpath "com.android.tools.build:gradle:$android_gradle_version"
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }}
}}

allprojects {{
    repositories {{
        google()
        mavenCentral()
    }}
}}

task clean(type: Delete) {{
    delete rootProject.buildDir
}}
'''
        groovy_file = os.path.join(project_path, 'build.gradle')
        with open(groovy_file, 'w') as f:
            f.write(groovy_content)
    
    def _generate_gradle_properties(self, project_path: str):
        """Generate gradle.properties."""
        content = f'''# Project-wide Gradle settings
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.caching=true

# Android settings
android.useAndroidX=true
android.nonTransitiveRClass=true

# Kotlin settings
kotlin.code.style=official
kotlin.mpp.enableCInteropCommonization=true
kotlin.mpp.androidSourceSetLayoutVersion=2

# KMP settings
kotlin.mpp.stability.nowarn=true
kotlin.native.ignoreDisabledTargets=true
'''
        properties_file = os.path.join(project_path, 'gradle.properties')
        with open(properties_file, 'w') as f:
            f.write(content)
    
    def _generate_shared_module(self, project_path: str):
        """Generate shared module build.gradle.kts."""
        shared_path = os.path.join(project_path, 'shared')
        os.makedirs(os.path.join(shared_path, 'src', 'commonMain', 'kotlin'), exist_ok=True)
        os.makedirs(os.path.join(shared_path, 'src', 'androidMain', 'kotlin'), exist_ok=True)
        os.makedirs(os.path.join(shared_path, 'src', 'iosMain', 'kotlin'), exist_ok=True)
        os.makedirs(os.path.join(shared_path, 'src', 'commonTest', 'kotlin'), exist_ok=True)
        
        content = f'''plugins {{
    kotlin("multiplatform")
    id("com.android.library")
    kotlin("plugin.serialization") version "{self.versions.kotlinx_serialization}"
}}

kotlin {{
    androidTarget {{
        compilations.all {{
            kotlinOptions {{
                jvmTarget = "11"
            }}
        }}
    }}
    
    iosX64()
    iosArm64()
    iosSimulatorArm64()
    
    sourceSets {{
        val commonMain by getting {{
            dependencies {{
                // KMP Core
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:{self.versions.kotlinx_coroutines}")
                
                // Serialization
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:{self.versions.kotlinx_serialization}")
                
                // Ktor (Networking)
                implementation("io.ktor:ktor-client-core:{self.versions.ktor}")
                implementation("io.ktor:ktor-client-content-negotiation:{self.versions.ktor}")
                implementation("io.ktor:ktor-serialization-kotlinx-json:{self.versions.ktor}")
                
                // Koin (DI)
                implementation("io.insert-koin:koin-core:{self.versions.koin}")
            }}
        }}
        
        val commonTest by getting {{
            dependencies {{
                implementation(kotlin("test"))
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:{self.versions.kotlinx_coroutines}")
            }}
        }}
        
        val androidMain by getting {{
            dependencies {{
                // Ktor Android Engine
                implementation("io.ktor:ktor-client-android:{self.versions.ktor}")
                
                // Koin Android
                implementation("io.insert-koin:koin-android:{self.versions.koin}")
            }}
        }}
        
        val iosX64Main by getting
        val iosArm64Main by getting
        val iosSimulatorArm64Main by getting
        
        val iosMain by creating {{
            dependsOn(commonMain)
            iosX64Main.dependsOn(this)
            iosArm64Main.dependsOn(this)
            iosSimulatorArm64Main.dependsOn(this)
            
            dependencies {{
                // Ktor iOS Engine
                implementation("io.ktor:ktor-client-darwin:{self.versions.ktor}")
            }}
        }}
    }}
}}

android {{
    namespace = "{self.config.group_id}.shared"
    compileSdk = {self.versions.compile_sdk}
    
    defaultConfig {{
        minSdk = {self.versions.min_sdk}
    }}
    
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }}
}}
'''
        build_file = os.path.join(shared_path, 'build.gradle.kts')
        with open(build_file, 'w') as f:
            f.write(content)
        
        # Also create Groovy version
        groovy_content = f'''plugins {{
    id 'org.jetbrains.kotlin.multiplatform'
    id 'com.android.library'
    id 'org.jetbrains.kotlin.plugin.serialization' version '{self.versions.kotlinx_serialization}'
}}

kotlin {{
    androidTarget {{}}
    
    iosX64()
    iosArm64()
    iosSimulatorArm64()
    
    sourceSets {{
        commonMain {{
            dependencies {{
                implementation "org.jetbrains.kotlinx:kotlinx-coroutines-core:{self.versions.kotlinx_coroutines}"
                implementation "org.jetbrains.kotlinx:kotlinx-serialization-json:{self.versions.kotlinx_serialization}"
                implementation "io.ktor:ktor-client-core:{self.versions.ktor}"
                implementation "io.insert-koin:koin-core:{self.versions.koin}"
            }}
        }}
        
        commonTest {{
            dependencies {{
                implementation kotlin('test')
            }}
        }}
        
        androidMain {{
            dependencies {{
                implementation "io.ktor:ktor-client-android:{self.versions.ktor}"
            }}
        }}
        
        iosMain {{
            dependencies {{
                implementation "io.ktor:ktor-client-darwin:{self.versions.ktor}"
            }}
        }}
    }}
}}

android {{
    namespace '{self.config.group_id}.shared'
    compileSdk {self.versions.compile_sdk}
    
    defaultConfig {{
        minSdk {self.versions.min_sdk}
    }}
    
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_11
        targetCompatibility JavaVersion.VERSION_11
    }}
}}
'''
        groovy_file = os.path.join(shared_path, 'build.gradle')
        with open(groovy_file, 'w') as f:
            f.write(groovy_content)
    
    def _generate_android_module(self, project_path: str):
        """Generate Android app module."""
        android_path = os.path.join(project_path, 'androidApp')
        os.makedirs(os.path.join(android_path, 'src', 'main', 'java'), exist_ok=True)
        os.makedirs(os.path.join(android_path, 'src', 'main', 'res'), exist_ok=True)
        
        content = f'''plugins {{
    id("com.android.application")
    kotlin("android")
}}

android {{
    namespace = "{self.config.group_id}.androidapp"
    compileSdk = {self.versions.compile_sdk}
    
    defaultConfig {{
        applicationId = "{self.config.group_id}.androidapp"
        minSdk = {self.versions.min_sdk}
        targetSdk = {self.versions.target_sdk}
        versionCode = 1
        versionName = "{self.config.version}"
    }}
    
    buildTypes {{
        release {{
            isMinifyEnabled = false
        }}
    }}
    
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }}
    
    kotlinOptions {{
        jvmTarget = "11"
    }}
}}

dependencies {{
    implementation(project(":shared"))
    
    // Android Core
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.10.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    
    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.2")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:{self.versions.kotlinx_coroutines}")
    
    // Testing
    testImplementation("junit:junit:{self.versions.junit}")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}}
'''
        build_file = os.path.join(android_path, 'build.gradle.kts')
        with open(build_file, 'w') as f:
            f.write(content)
        
        # Create AndroidManifest.xml
        manifest_content = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.KMPApp">
        
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        
    </application>

</manifest>
'''
        manifest_file = os.path.join(android_path, 'src', 'main', 'AndroidManifest.xml')
        with open(manifest_file, 'w') as f:
            f.write(manifest_content)
    
    def _generate_ios_placeholder(self, project_path: str):
        """Generate iOS placeholder."""
        ios_path = os.path.join(project_path, 'iosApp')
        os.makedirs(ios_path, exist_ok=True)
        
        readme_content = '''# iOS Application

This directory will contain the iOS application.

## Setup

1. Open `iosApp.xcodeproj` in Xcode
2. Build and run

## Structure

- `iosApp/` - iOS application
  - `iosApp/` - Main app target
  - `Shared/` - Shared KMP module (linked from ../shared)

## Requirements

- Xcode 15.0+
- iOS 14.0+
- CocoaPods (if using)

## Next Steps

1. Create Xcode project
2. Link shared KMP module as framework
3. Implement iOS UI
'''
        readme_file = os.path.join(ios_path, 'README.md')
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def _generate_desktop_module(self, project_path: str):
        """Generate Desktop module."""
        desktop_path = os.path.join(project_path, 'desktopApp')
        os.makedirs(os.path.join(desktop_path, 'src', 'jvmMain', 'kotlin'), exist_ok=True)
        
        content = f'''plugins {{
    kotlin("jvm")
    application
}}

application {{
    mainClass.set("{self.config.group_id}.desktopapp.MainKt")
}}

dependencies {{
    implementation(project(":shared"))
    
    // Compose Desktop (optional)
    // implementation("org.jetbrains.compose.desktop:desktop:1.5.10")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:{self.versions.kotlinx_coroutines}")
}}

java {{
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
}}
'''
        build_file = os.path.join(desktop_path, 'build.gradle.kts')
        with open(build_file, 'w') as f:
            f.write(content)
    
    def get_versions_config(self) -> Dict:
        """Get current versions configuration."""
        return self.versions.to_dict()
    
    def update_versions(self, **kwargs):
        """Update specific versions."""
        for key, value in kwargs.items():
            if hasattr(self.versions, key):
                setattr(self.versions, key, value)
        
        logger.info(f"Updated versions: {kwargs}")


def generate_gradle_build(project_path: str, config: Optional[BuildConfig] = None):
    """
    Generate Gradle build for KMP project.
    
    Args:
        project_path: Path to migrated KMP project
        config: Optional build configuration
    """
    generator = GradleBuildGenerator(config)
    generator.generate_for_project(project_path)


def get_default_versions() -> Dict:
    """Get default version configuration."""
    return GradleVersions().to_dict()


def save_versions_config(config_path: str, versions: Dict):
    """Save versions configuration to file."""
    with open(config_path, 'w') as f:
        json.dump(versions, f, indent=2)
    logger.info(f"Saved versions config to {config_path}")


def load_versions_config(config_path: str) -> GradleVersions:
    """Load versions configuration from file."""
    with open(config_path, 'r') as f:
        data = json.load(f)
    return GradleVersions.from_dict(data)
