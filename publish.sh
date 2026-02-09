#!/bin/bash

# Exit on error
set -e

# Help message
usage() {
    echo "Usage: $0 {patch|minor|major} [-d|--dry-run]"
    echo "  patch: 0.1.0 -> 0.1.1"
    echo "  minor: 0.1.0 -> 0.2.0"
    echo "  major: 0.1.0 -> 1.0.0"
    echo "  -d, --dry-run: Skip actual update and publication"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

BUMP_TYPE=$1
DRY_RUN=false

# Check for dry-run flag
for arg in "$@"; do
    if [ "$arg" == "-d" ] || [ "$arg" == "--dry-run" ]; then
        DRY_RUN=true
    fi
done

PYPROJECT="pyproject.toml"

if [ ! -f "$PYPROJECT" ]; then
    echo "Error: $PYPROJECT not found."
    exit 1
fi

# 1. Read current version
CURRENT_VERSION=$(grep -m 1 'version = "' "$PYPROJECT" | sed -E 's/version = "([^"]+)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo "Error: Could not find version in $PYPROJECT"
    exit 1
fi

echo "Current version: $CURRENT_VERSION"

# 2. Calculate new version
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case $BUMP_TYPE in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        usage
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "New version: $NEW_VERSION"

if [ "$DRY_RUN" = true ]; then
    echo "⚠️ DRY RUN: Skipping version update and publication."
else
    # 3. Update pyproject.toml
    # Use different sed syntax for macOS compatibility if needed, but assuming standard GNU sed for now:
    # sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "$PYPROJECT"
    # To be safer across platforms, use a temp file:
    sed "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" "$PYPROJECT" > "$PYPROJECT.tmp" && mv "$PYPROJECT.tmp" "$PYPROJECT"
    echo "✅ Updated $PYPROJECT to version $NEW_VERSION"

    # 4. Build package
    echo ">> Building package..."
    rm -rf dist
    uv build

    # 5. Publish to PyPI
    echo ">> Publishing to PyPI..."
    uv run --with twine twine upload dist/*
    
    echo "✅ Published version $NEW_VERSION to PyPI!"
fi
