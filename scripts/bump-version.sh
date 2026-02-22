#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/bump-version.sh 0.2.0
# Updates version in all package files, commits, and tags.

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>"
  echo "Example: $0 0.2.0"
  exit 1
fi

VERSION="$1"

# Validate semver format (X.Y.Z)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: Version must be in semver format (X.Y.Z), got: $VERSION"
  exit 1
fi

# Resolve project root (script lives in scripts/)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Portable in-place sed (works on both macOS and Linux)
_sed_i() {
  local file="$1"
  shift
  sed "$@" "$file" > "$file.tmp" && mv "$file.tmp" "$file"
}

echo "Bumping version to $VERSION ..."

# 1. frontend/package.json
_sed_i "$ROOT/frontend/package.json" "s/\"version\": \".*\"/\"version\": \"$VERSION\"/"
echo "  ✓ frontend/package.json"

# 2. desktop/package.json
_sed_i "$ROOT/desktop/package.json" "s/\"version\": \".*\"/\"version\": \"$VERSION\"/"
echo "  ✓ desktop/package.json"

# 3. backend/pyproject.toml
_sed_i "$ROOT/backend/pyproject.toml" "s/^version = \".*\"/version = \"$VERSION\"/"
echo "  ✓ backend/pyproject.toml"

# Commit and tag
cd "$ROOT"
git add frontend/package.json desktop/package.json backend/pyproject.toml
git commit -m "chore: bump version to $VERSION"
git tag "v$VERSION"

echo ""
echo "Done! Version bumped to $VERSION and tagged v$VERSION."
echo "Run 'git push && git push --tags' to trigger the release workflow."
