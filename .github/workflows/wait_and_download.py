import os
import subprocess
import time
import sys
import json
from datetime import datetime, timedelta

# Get the list of dependencies and their timeouts from the environment
dependencies_json = os.getenv("DEPENDENCIES_JSON", "[]")
dependencies = json.loads(dependencies_json)

# Get the current GitHub Run ID from the environment
run_id = os.getenv("GITHUB_RUN_ID")

# Function to run a command and return success or failure
def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        return False

# Iterate through dependencies and attempt to download each artifact
for dep_info in dependencies:
    dep_name = dep_info["dependency"]
    timeout_minutes = dep_info.get("timeout", 60)  # Default to 60 minutes if not provided
    timeout_seconds = timeout_minutes * 60

    print(f"Waiting for artifact from {dep_name} with a timeout of {timeout_minutes} minutes...")

    start_time = datetime.now()
    success = False

    while (datetime.now() - start_time).total_seconds() < timeout_seconds:
        print(f"Attempting to download artifact from {dep_name} with run ID {run_id}...")

        # Command to download the artifact using the GitHub CLI
        command = f'gh run download --name "{dep_name}-output-{run_id}" --dir "artifacts/" --repo "{os.getenv("GITHUB_REPOSITORY")}"'
        
        if run_command(command):
            print(f"Successfully downloaded {dep_name} artifact.")
            success = True
            break
        else:
            print(f"Artifact from {dep_name} not available yet, retrying in 30 seconds...")
            time.sleep(30)  # Sleep for 30 seconds before retrying

    if not success:
        print(f"Timeout reached for {dep_name} after {timeout_minutes} minutes. Exiting...")
        sys.exit(1)

    # Check the contents of the artifact for the word "FAILURE"
    try:
        with open(f"artifacts/output.txt", "r") as f:
            contents = f.read().strip()
            if "FAILURE" in contents:
                print(f"Dependency job {dep_name} failed, skipping this job.")
                sys.exit(1)  # Exit with 0 to skip further job execution
    except FileNotFoundError:
        print(f"Artifact for {dep_name} was not found after download.")
        sys.exit(1)

# Continue with the rest of the job if no "FAILURE" was detected
print("All dependencies succeeded, continuing with the job...")
