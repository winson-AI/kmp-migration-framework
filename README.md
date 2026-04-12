# KMP Migration Framework

This framework provides a reusable pipeline for migrating existing Android projects to Kotlin Multiplatform (KMP). It follows a structured, multi-agent, and test-driven approach to ensure a high-quality migration.

## Components

- **/comprehension**: Contains scripts to analyze an Android project and generate a detailed migration specification (SPEC.md).
- **/generation**: Contains scripts for the initial, tool-assisted code translation from Android to KMP common code. This component will use a multi-agent approach.
- **/testing**: Contains scripts for migrating and implementing the test suite in the KMP project to drive development, as well as scripts for the evaluation and feedback loop.
- **/templates**: Contains project templates, starting with a basic KMP project structure.
- **/skills**: Contains reusable "skills" for mapping Android-specific libraries to their KMP equivalents (e.g., Retrofit to Ktor).
