#!/bin/bash

# git-first-commit.sh

# Default to today if no days specified
DAYS_AGO=${1:-0}

# Verify we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository" >&2
    exit 1
fi

# Validate input is a number
if ! [[ "$DAYS_AGO" =~ ^[0-9]+$ ]]; then
    echo "Usage: ./git-first-commit.sh [days_ago]" >&2
    echo "Example: ./git-first-commit.sh 3    # Get first commit from 3 days ago" >&2
    echo "         ./git-first-commit.sh      # Get first commit from today" >&2
    exit 1
fi

# Get the date in ISO format (YYYY-MM-DD)
TARGET_DATE=$(date -v-${DAYS_AGO}d +%Y-%m-%d)

# Get the first commit of the target date
FIRST_COMMIT=$(git log --since="$TARGET_DATE 00:00:00" --until="$TARGET_DATE 23:59:59" --format="%H" | tail -n 1)

if [ -z "$FIRST_COMMIT" ]; then
    echo "No commits found on ${TARGET_DATE}" >&2
    exit 1
else
    echo "$FIRST_COMMIT"
fi