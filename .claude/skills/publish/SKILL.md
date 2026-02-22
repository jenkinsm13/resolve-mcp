---
name: publish
description: Bump patch version, build, publish to PyPI, commit, and push to GitHub
disable-model-invocation: true
---

# Publish to PyPI

Automates the full release cycle for this package.

## Steps

1. **Bump version**: Increment the patch version in `pyproject.toml` (e.g., 0.1.5 → 0.1.6)
2. **Build**: Run `uv build` to create sdist and wheel
3. **Publish**: Run `uv publish` to upload to PyPI (will prompt for token if not cached)
4. **Commit**: Stage all changes and commit with message "Release vX.Y.Z"
5. **Push**: Push to `origin main`

## Usage

```
/publish
```

If you want to bump minor or major version instead of patch, say so:
```
/publish minor
/publish major
```
