import os
import re
import argparse

def analyze_android_project(project_path):
    """
    Analyzes an Android project to generate a migration specification.
    """
    spec_content = "# KMP Migration Specification\n\n"

    # 1. List project modules
    spec_content += "## 1. Project Modules\n\n"
    modules = get_project_modules(project_path)
    for module in modules:
        spec_content += f"- {module}\n"

    # 2. Identify dependencies
    spec_content += "\n## 2. Dependencies\n\n"
    dependencies = get_project_dependencies(project_path)
    for dep in dependencies:
        spec_content += f"- {dep}\n"

    # Write the spec file
    with open(os.path.join(project_path, "SPEC.md"), "w") as f:
        f.write(spec_content)

    print(f"SPEC.md generated successfully at {os.path.join(project_path, 'SPEC.md')}")

def get_project_modules(project_path):
    """
    Finds all modules in the settings.gradle file.
    """
    modules = []
    settings_file = os.path.join(project_path, "settings.gradle")
    if not os.path.exists(settings_file):
        settings_file = os.path.join(project_path, "settings.gradle.kts")

    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            content = f.read()
            # A simple regex to find included modules
            matches = re.findall(r"include\s*['\"]:(.*?)['\"]", content)
            modules = [m.replace(":", "") for m in matches]
    return modules

def get_project_dependencies(project_path):
    """
    Parses all build.gradle and build.gradle.kts files to find dependencies.
    """
    dependencies = set()
    dependency_pattern = re.compile(r"""
        (?:implementation|api|testImplementation|androidTestImplementation)
        \s*
        \(?
        \s*
        ['"]
        ([^'"]+)
        ['"]
        \s*
        \)?
    """, re.VERBOSE)

    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith((".gradle", ".gradle.kts")):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()
                    matches = dependency_pattern.findall(content)
                    for match in matches:
                        dependencies.add(match)
    return list(dependencies)




