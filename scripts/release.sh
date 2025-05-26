#!/bin/bash

# Check if version argument is provided
if [ -z "$1" ]; then
    echo "Usage: ./release.sh <version>"
    echo "Example: ./release.sh 1.0.0"
    exit 1
fi

VERSION=$1

# Create release first
echo "📦 Creating GitHub release..."
gh release create "v$VERSION" \
    --title "Release v$VERSION" \
    --notes "Release v$VERSION" \
    --draft

# Create and push tag
echo "📝 Creating release tag..."
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

echo "✅ Tag v$VERSION created and pushed to GitHub"
echo "🚀 GitHub Actions will automatically build and upload executables for all platforms" 