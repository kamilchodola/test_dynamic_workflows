import os
import subprocess
import time
import sys
import json
from datetime import datetime, timedelta

dependencies_json = os.getenv("DEPENDENCIES_JSON", "[]")
dependencies = json.loads(dependencies_json)
run_id = os.getenv("GITHUB_RUN_ID")

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        return False

for dep_info in dependencies:
    dep_name = dep_info["dependency"]
    timeout_minutes = dep_info.get("timeout", 60)  # Default to 60 minutes if not provided
    timeout_seconds = timeout_minutes * 60

    print(f"Waiting for artifact from {dep_name} with a timeout of {timeout_minutes} minutes...")

    start_time = datetime.now()
    success = False

    while (datetime.now() - start_time).total_seconds() < timeout_seconds:
        print(f"Attempting to download artifact from {dep_name} with run ID {run_id}...")

        command = f'gh run download --name "{dep_name}-output-{run_id}" --dir "artifacts/" --repo "{os.getenv("GITHUB_REPOSITORY")}"'
        
        if run_command(command):
            print(f"Successfully downloaded {dep_name} artifact.")
            success = True
            break
        else:
            print(f"Artifact from {dep_name} not available yet, retrying in 10 seconds...")
            time.sleep(10)  # Check every 10 seconds on dependency
            
    if not success:
        print(f"Timeout reached for {dep_name} after {timeout_minutes} minutes. Exiting...")
        sys.exit(1)

    try:
        with open(f"artifacts/output.txt", "r") as f:
            contents = f.read().strip()
            if "FAILURE" in contents:
                print(f"Dependency job {dep_name} failed, skipping this job.")
                sys.exit(78) # Means "cancelled/skipped" because is neither fails or success because of dependency failure
    except FileNotFoundError:
        print(f"Artifact for {dep_name} was not found after download.")
        sys.exit(1)

print("All dependencies succeeded, continuing with the job...")
