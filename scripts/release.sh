#!/bin/bash

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

VERSION=$1

# Create and push tag
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

echo "Release v$VERSION created and pushed to GitHub"
echo "The GitHub Actions workflow will automatically create the release with executables" 