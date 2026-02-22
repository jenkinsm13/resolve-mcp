---
name: bump-publish
description: Bump the package version in pyproject.toml and publish to PyPI. Handles version increment, git tag, build, and upload in one step.
disable-model-invocation: true
---

# Bump & Publish

Bump the resolve-mcp version, build, and publish to PyPI.

## Arguments

- `<level>` — one of `patch` (default), `minor`, or `major`
- `--dry-run` — show what would happen without making changes

## Procedure

### 1. Read current version

```bash
grep '^version' pyproject.toml
```

### 2. Calculate new version

Parse the current `version = "X.Y.Z"` line.

- `patch` → X.Y.(Z+1)
- `minor` → X.(Y+1).0
- `major` → (X+1).0.0

If `--dry-run` was passed, print the old → new version and stop here.

### 3. Update pyproject.toml

Use the Edit tool to replace the version line:

```
old: version = "X.Y.Z"
new: version = "A.B.C"
```

**IMPORTANT**: This is the ONE case where editing the version field is allowed.
The PreToolUse hook will block generic version edits — this skill has explicit permission because the user invoked `/bump-publish` intentionally.

### 4. Update __init__.py docstring (if version is mentioned)

Check if `resolve_mcp/__init__.py` mentions the old version and update it too.

### 5. Build and publish

```bash
uv build && uv publish --token $PYPI_TOKEN
```

If `PYPI_TOKEN` is not set, remind the user to set it:
```
export PYPI_TOKEN=pypi-...
```

### 6. Git commit and tag

```bash
git add pyproject.toml resolve_mcp/__init__.py
git commit -m "release: v{NEW_VERSION}"
git tag "v{NEW_VERSION}"
git push origin main --tags
```

### 7. Confirm

Print a summary:
```
✅ resolve-mcp v{OLD} → v{NEW}
   Published to PyPI: https://pypi.org/project/resolve-mcp/{NEW}/
   Tagged: v{NEW}
```
