import os
import subprocess
from typing import Optional

def sync_with_server() -> bool:
    """Sync changes with the Evennia server via gcloud CLI"""
    instance_name = os.getenv("EVENNIA_INSTANCE")
    zone = os.getenv("EVENNIA_ZONE", "us-central1-a")  # Default to us-central1-a if not specified
    project = os.getenv("EVENNIA_PROJECT")
    
    if not instance_name or not project:
        print("Error: EVENNIA_INSTANCE and EVENNIA_PROJECT environment variables must be set")
        return False

    try:
        # Execute the update script via gcloud compute ssh
        subprocess.run([
            'gcloud',
            'compute',
            'ssh',
            instance_name,
            f'--zone={zone}',
            f'--project={project}',
            '--',  # Separates gcloud flags from SSH command
            'bash',  # Explicitly use bash to execute the script
            '/home/nick/anchors-edge/server/update_evennia.sh'
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error syncing with server: {e}")
        return False

def main():
    if sync_with_server():
        print("Successfully synced with server")
        return True
    else:
        print("Server sync failed")
        return False

if __name__ == "__main__":
    main() 