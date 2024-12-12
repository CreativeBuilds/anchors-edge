from commit import main as commit
from sync import main as sync

def main():
    # First commit
    if not commit():
        return
    
    # Then sync
    if sync():
        print("Successfully committed and synced changes")
    else:
        print("Changes committed but server sync failed")

if __name__ == "__main__":
    main() 