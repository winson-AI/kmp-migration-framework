import os

def delivery_agent(project_path, delegate_task, dry_run=True):
    """
    Creates a new branch, commits the generated code, and opens a pull request.
    """
    
    delivery_goal = f"""
    You are a Delivery agent. Your task is to create a pull request with the migrated KMP code.
    You will be working in the following directory: {project_path}
    
    Your tasks are:
    1.  Create a new branch called "kmp-migration".
    2.  Add all the generated files to the staging area.
    3.  Commit the changes with the message "feat: Migrate to KMP".
    4.  Push the new branch to the remote repository.
    5.  Create a pull request with the title "KMP Migration" and a body that summarizes the changes.
    
    If `dry_run` is True, you should only print the commands that you would execute.
    If `dry_run` is False, you should execute the commands using the `terminal` tool.
    """
    
    if dry_run:
        print("--- DRY RUN ---")
        print("git checkout -b kmp-migration")
        print("git add .")
        print("git commit -m 'feat: Migrate to KMP'")
        print("git push origin kmp-migration")
        print("gh pr create --title 'KMP Migration' --body 'This pull request contains the migrated KMP code.'")
    else:
        delegate_task(goal=delivery_goal, toolsets=["terminal"])

