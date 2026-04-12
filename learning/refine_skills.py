import os
import json

def refine_skills(delegate_task):
    framework_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    kb_dir = os.path.join(framework_path, "knowledge_base")
    if not os.path.exists(kb_dir):
        print("Knowledge base not found.")
        return

    for file_name in os.listdir(kb_dir):
        if file_name.endswith(".json"):
            file_path = os.path.join(kb_dir, file_name)
            with open(file_path, "r") as f:
                evaluation_data = json.load(f)

            if evaluation_data["status"] == "failed":
                print(f"Found failed evaluation: {file_name}")
                
                refiner_goal = f"""
                You are a Refiner agent. Your task is to analyze a failed code migration and automatically update the relevant skill.
                
                ## Evaluation Details

                - **Project:** {evaluation_data['project']}
                - **File:** {evaluation_data['file']}
                - **Timestamp:** {evaluation_data['timestamp']}

                ## Generated Code

                ```kotlin
                {evaluation_data['generated_code']}
                ```

                ## Evaluation Feedback

                {evaluation_data['evaluation']}

                ## Your Task

                1.  **Analyze the feedback:** Understand why the code failed.
                2.  **Identify the relevant skill:** Determine which skill was most likely used to generate the failed code.
                3.  **Propose a change:** Formulate a specific change to the skill's `guide.md` that would prevent this error in the future.
                4.  **Assess confidence:** Rate your confidence in the proposed change on a scale of 1 to 5.
                5.  **Take action:**
                    - If your confidence is 4 or 5, use the `skill_manage` tool to automatically apply the change.
                    - If your confidence is 3 or less, create a refinement suggestion markdown file for a human to review.
                """
                
                delegate_task(goal=refiner_goal, toolsets=["skill_manage"])
