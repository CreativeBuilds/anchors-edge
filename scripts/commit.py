import os
import subprocess
import sys
from typing import Optional
import requests

def get_git_diff() -> str:
    """Get the current git diff output"""
    try:
        result = subprocess.run(['git', 'diff'], capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        sys.exit(1)

def generate_commit_message(diff: str) -> Optional[str]:
    """Generate a commit message using OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:4001",
        "X-Title": "Git Commit Generator"
    }

    data = {
        "model": "anthropic/claude-3-sonnet",
        "messages": [
            {
                "role": "user",
                "content": f"{diff}\n\nConvert to a git commit message. Respond with only the commit message, no other text. Start with things like 'feat(title):' 'fix(title):' 'docs(title):' 'refactor(title):' etc. Along with the title, add a short list of descriptions of the changes."
            }
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error generating commit message: {e}")
        return None

def commit_changes(message: str) -> bool:
    """Commit changes to git"""
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', message], check=True)
        # Push changes after commit
        subprocess.run(['git', 'push'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error committing changes: {e}")
        return False

def main():
    # Get git diff
    diff = get_git_diff()
    if not diff:
        print("No changes to commit")
        return False

    # Generate commit message
    commit_message = generate_commit_message(diff)
    if not commit_message:
        return False

    # Show the proposed commit message and ask for confirmation
    print("\nProposed commit message:")
    print(f"\n{commit_message}\n")
    
    confirm = input("Proceed with commit? (y/n): ").lower()
    if confirm != 'y':
        print("Commit cancelled")
        return False

    # Commit changes
    if not commit_changes(commit_message):
        return False
        
    return True

if __name__ == "__main__":
    main() 