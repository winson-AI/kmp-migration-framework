plugins {
    kotlin("multiplatform")
    id("com.android.library")
}

kotlin {
    androidTarget()
    iosX64()
    iosArm64()
    iosSimulatorArm64()
    jvm("desktop")

    sourceSets {
        val commonMain by getting {
            dependencies {
                // Common dependencies here
            }
        }
        val androidMain by getting {
            dependencies {
                // Android-specific dependencies here
            }
        }
        val iosX64Main by getting
        val iosArm64Main by getting
        val iosSimulatorArm64Main by getting
        val iosMain by creating {
            dependsOn(commonMain)
            iosX64Main.dependsOn(this)
            iosArm64Main.dependsOn(this)
            iosSimulatorArm64Main.dependsOn(this)
        }
        val desktopMain by getting {
            dependencies {
                // Desktop-specific dependencies here
            }
        }
    }
}

android {
    namespace = "com.example.shared"
    compileSdk = 33
    defaultConfig {
        minSdk = 24
    }
}
