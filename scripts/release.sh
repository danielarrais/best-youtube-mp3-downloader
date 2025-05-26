#!/bin/bash

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

VERSION=$1

# Create and push tag
echo "📝 Creating release tag..."
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

echo "✅ Tag v$VERSION created and pushed to GitHub"
echo "🚀 GitHub Actions will automatically create the release with executables for all platforms" 