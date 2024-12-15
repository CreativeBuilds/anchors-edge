#!/bin/bash

# git-changes.sh

# Check if a commit hash was provided
if [ -z "$1" ]; then
    echo "Usage: ./git-changes.sh <commit-hash>"
    echo "Example: ./git-changes.sh 4aa11d27"
    exit 1
fi

# Verify we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Verify the commit hash exists
if ! git cat-file -e "$1" 2> /dev/null; then
    echo "Error: Invalid commit hash"
    exit 1
fi

# Calculate changes
echo "Calculating changes since commit: $1"
echo "----------------------------------------"
git log $1..HEAD --shortstat | grep -E "files? changed" | \
awk '{files+=$1; inserted+=$4; deleted+=$6} 
     END {
         print "Total:", files, "files changed"
         print "       ", inserted, "insertions(+)"
         print "       ", deleted, "deletions(-)"
         print "        net:", inserted-deleted, "lines"
     }'