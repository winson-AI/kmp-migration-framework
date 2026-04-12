import os
import argparse
import yaml
import json
import time

def load_skills(framework_path):
    skills = {}
    skills_dir = os.path.join(framework_path, "skills")
    if not os.path.exists(skills_dir):
        return skills

    for skill_name in os.listdir(skills_dir):
        skill_dir = os.path.join(skills_dir, skill_name)
        if os.path.isdir(skill_dir):
            manifest_path = os.path.join(skill_dir, "skill.yaml")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r") as f:
                    skill_data = yaml.safe_load(f)
                    guide_path = os.path.join(skill_dir, "guide.md")
                    if os.path.exists(guide_path):
                        with open(guide_path, "r") as g:
                            skill_data["guide"] = g.read()
                    skills[skill_data["android_dependency"]] = skill_data
    return skills

def save_evaluation(project_path, file_path, generated_code, evaluation):
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "knowledge_base")
    if not os.path.exists(kb_dir):
        os.makedirs(kb_dir)

    status = "passed" if "approve" in evaluation.lower() else "failed"

    evaluation_data = {
        "timestamp": time.time(),
        "project": os.path.basename(project_path),
        "file": file_path,
        "status": status,
        "generated_code": generated_code,
        "evaluation": evaluation
    }

    file_name = f"{os.path.basename(file_path)}_{int(time.time())}.json"
    with open(os.path.join(kb_dir, file_name), "w") as f:
        json.dump(evaluation_data, f, indent=4)

def generate_kmp_code(project_path, delegate_task):
    framework_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    skills = load_skills(framework_path)

    spec_path = os.path.join(project_path, "SPEC.md")
    if not os.path.exists(spec_path):
        print(f"Error: SPEC.md not found in {project_path}. Please run the comprehension script first.")
        return

    with open(spec_path, "r") as f:
        spec_content = f.read()

    planner_goal = f"""
    You are an expert KMP architect. Your task is to create a migration plan from an Android project to a KMP project.
    Analyze the following migration specification and create a detailed, step-by-step plan for the migration.
    The plan should be a list of file paths, ordered by dependency.
    For each file, specify the original file path and the target KMP module.
    Also, identify any dependencies that can be migrated using the available skills.

    SPECIFICATION:
    {spec_content}

    AVAILABLE SKILLS:
    {list(skills.keys())}
    """
    plan = delegate_task(goal=planner_goal)

    files_to_migrate = [line.strip("- ") for line in spec_content.split("## 2. Dependencies")[0].split("\n") if line.startswith("-")]

    for file_path in files_to_migrate:
        with open(os.path.join(project_path, file_path), "r") as f:
            file_content = f.read()

        target_module = "shared/src/commonMain/kotlin"
        
        generator_goal = f"""
        You are an expert KMP developer. Your task is to migrate a single file from Android to KMP.
        Translate the following Android code to Kotlin Multiplatform, following the provided plan and best practices.
        - The translated code should be placed in the specified target KMP module.
        - Use KMP-compatible libraries (e.g., Ktor for networking, SQLDelight for database, kotlinx.coroutines for concurrency).
        - Use the 'expect' and 'actual' keywords for platform-specific code.
        - The generated code should be clean, idiomatic, and well-documented.

        FILE TO MIGRATE: {file_path}

        FILE CONTENT:
        {file_content}

        TARGET KMP MODULE: {target_module}
        """

        if any(skill in file_content for skill in skills.keys()):
            skill_context = ""
            for skill_name, skill_data in skills.items():
                if skill_name in file_content:
                    skill_context += f"SKILL: {skill_data['name']}\n"
                    skill_context += f"GUIDE:\n{skill_data['guide']}\n\n"
            
            generator_goal += f"\nAPPLICABLE SKILLS:\n{skill_context}"
        
        generated_code = delegate_task(goal=generator_goal)

        evaluator_goal = f"""
        You are an expert KMP code reviewer. Your task is to review a file that has been migrated from Android to KMP.
        Review the following KMP code for correctness, performance, and adherence to KMP best practices.
        Provide specific, actionable feedback. If there are errors, explain how to fix them.
        If the code is good, approve it.

        GENERATED CODE:
        {generated_code}
        """
        evaluation = delegate_task(goal=evaluator_goal)

        save_evaluation(project_path, file_path, generated_code, evaluation)

        print(f"File: {file_path}")
        print(f"Generated Code: {generated_code}")
        print(f"Evaluation: {evaluation}")
        print("-" * 20)
