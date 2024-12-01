#!/bin/bash

# Function to increment version number (x.y.z)
increment_version() {
    local version=$1
    local position=$2  # 1=major, 2=minor, 3=patch
    
    # Split version into array
    IFS='.' read -ra ver_parts <<< "$version"
    
    # Increment the specified position
    ver_parts[$((position-1))]=$((ver_parts[$((position-1))]+1))
    
    # Reset all positions after the incremented one
    for ((i=position; i<3; i++)); do
        ver_parts[$i]=0
    done
    
    # Join array back into string
    echo "${ver_parts[0]}.${ver_parts[1]}.${ver_parts[2]}"
}

# Read current version
VERSION=$(cat VERSION)

# Parse command line arguments
case "$1" in
    major)
        NEW_VERSION=$(increment_version "$VERSION" 1)
        ;;
    minor)
        NEW_VERSION=$(increment_version "$VERSION" 2)
        ;;
    patch|"")  # Default to patch if no argument provided
        NEW_VERSION=$(increment_version "$VERSION" 3)
        ;;
    *)
        echo "Usage: $0 [major|minor|patch]"
        exit 1
        ;;
esac

# Update version file
echo "$NEW_VERSION" > VERSION

# Add new section to changelog
echo "Enter changelog entries (one per line, press Ctrl+D when done):"
echo -e "\nv$NEW_VERSION" >> CHANGELOG
while IFS= read -r line; do
    echo "- $line" >> CHANGELOG
done

# Git operations
git add VERSION CHANGELOG
git commit -m "Release version $NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"
git push && git push --tags

echo "Version incremented to $NEW_VERSION" 