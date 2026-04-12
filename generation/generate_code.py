import os
import yaml
import json
import time

# Import the new LLM system
try:
    from llm import LLMInvoker, PromptManager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM module not available. Using mock responses.")

def load_skills(framework_path):
    """Load migration skills from the skills directory."""
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
    """Save evaluation results to the knowledge base."""
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

def generate_kmp_code(project_path, delegate_task=None):
    """
    Generate KMP code using the LLM system.
    
    Args:
        project_path: Path to the Android project
        delegate_task: Optional LLMInvoker or callable for backward compatibility
    """
    framework_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    skills = load_skills(framework_path)

    # Initialize LLM system if available
    if LLM_AVAILABLE and isinstance(delegate_task, LLMInvoker):
        invoker = delegate_task
        prompt_manager = PromptManager()
        use_llm = True
    elif callable(delegate_task):
        invoker = None
        prompt_manager = None
        use_llm = False
    else:
        # Auto-initialize with default provider
        if LLM_AVAILABLE:
            invoker = LLMInvoker(provider='ollama', model='qwen2.5-coder')
            prompt_manager = PromptManager()
            use_llm = True
        else:
            invoker = None
            prompt_manager = None
            use_llm = False

    spec_path = os.path.join(project_path, "SPEC.md")
    if not os.path.exists(spec_path):
        print(f"Error: SPEC.md not found in {project_path}. Please run the comprehension script first.")
        return

    with open(spec_path, "r") as f:
        spec_content = f.read()

    # Phase 1: Get migration plan using LLM
    if use_llm and prompt_manager:
        plan_result = prompt_manager.invoke(
            'architecture_analysis',
            invoker,
            project_structure=spec_content,
            file_list="N/A"
        )
        plan = plan_result.content
        print("✓ Architecture analysis complete")
    else:
        plan = "Standard migration plan"
        if callable(delegate_task):
            plan = delegate_task(goal=f"Create migration plan for: {spec_content}", toolsets=None)

    # Phase 2: Migrate each file
    modules_to_migrate = [line.strip("- ") for line in spec_content.split("## 2. Dependencies")[0].split("\n") if line.startswith("-")]

    files_processed = 0
    files_successful = 0

    for module in modules_to_migrate:
        module_path = os.path.join(project_path, module)
        if not os.path.exists(module_path):
            continue
            
        for root, dirs, files in os.walk(module_path):
            for file in files:
                if file.endswith((".kt", ".java")):
                    file_path = os.path.join(root, file)
                    
                    with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()

                    target_module = "shared/src/commonMain/kotlin"
                    
                    # Check for applicable skills
                    skill_context = ""
                    for skill_name, skill_data in skills.items():
                        if skill_name in file_content:
                            skill_context += f"\n## Skill: {skill_data['name']}\n"
                            skill_context += f"Guide:\n{skill_data['guide'][:2000]}\n"  # Truncate guide
                    
                    # Generate code using LLM
                    if use_llm and prompt_manager:
                        try:
                            migration_result = prompt_manager.invoke(
                                'code_migration',
                                invoker,
                                file_path=file_path,
                                source_code=file_content[:8000],  # Truncate if too long
                                target_module=target_module
                            )
                            
                            if skill_context:
                                # Follow-up with skill-specific guidance
                                skill_prompt = f"""
Apply this skill guidance to the migration:
{skill_context}

Previous migration output:
{migration_result.content[:4000]}

Provide the final migrated code incorporating the skill guidance.
"""
                                skill_result = invoker.invoke(skill_prompt)
                                generated_code = skill_result.content
                            else:
                                generated_code = migration_result.content
                            
                            files_successful += 1
                            
                        except Exception as e:
                            print(f"Error migrating {file_path}: {e}")
                            generated_code = f"// Migration failed: {e}\n{file_content}"
                    elif callable(delegate_task):
                        generator_goal = f"""
You are an expert KMP developer. Migrate this Android code to Kotlin Multiplatform.

FILE: {file_path}
TARGET: {target_module}

CODE:
{file_content}

{skill_context if skill_context else ""}

Provide the complete migrated KMP code.
"""
                        generated_code = delegate_task(goal=generator_goal, toolsets=None)
                    else:
                        # Mock for testing
                        generated_code = f"// Mock migration of {file_path}\n// Original content preserved\n{file_content}"

                    # Evaluate the generated code
                    if use_llm and prompt_manager:
                        try:
                            review_result = prompt_manager.invoke(
                                'code_review',
                                invoker,
                                file_path=file_path,
                                source_code=generated_code[:8000]
                            )
                            evaluation = review_result.content
                        except Exception as e:
                            evaluation = f"Review failed: {e}"
                    elif callable(delegate_task):
                        evaluator_goal = f"""
Review this migrated KMP code. Provide JSON with scores and feedback.

CODE:
{generated_code[:8000]}

Return only JSON.
"""
                        evaluation = delegate_task(goal=evaluator_goal, toolsets=None)
                    else:
                        evaluation = '{"overall_score": 7.0, "feedback": "Mock review"}'

                    # Save evaluation
                    save_evaluation(project_path, file_path, generated_code, evaluation)

                    # Save migrated file if approved
                    if "approve" in evaluation.lower() or '"overall_score":' in evaluation and float(evaluation.split('"overall_score":')[1].split(',')[0]) >= 6:
                        migrated_project_path = os.path.join(project_path, "migrated_kmp_project")
                        if not os.path.exists(migrated_project_path):
                            template_path = os.path.join(framework_path, "templates", "kmp-project")
                            os.system(f"cp -r {template_path} {migrated_project_path}")
                        
                        target_file_path = os.path.join(migrated_project_path, target_module, os.path.basename(file_path))
                        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                        with open(target_file_path, "w") as f:
                            f.write(generated_code)
                        print(f"✓ Saved: {target_file_path}")
                        files_successful += 1
                    else:
                        print(f"⚠ Skipped (low score): {file_path}")

                    files_processed += 1
                    print(f"  [{files_processed}] {os.path.basename(file_path)}")

    print(f"\n{'='*60}")
    print(f"Migration Complete: {files_successful}/{files_processed} files successful")
    print(f"{'='*60}")
