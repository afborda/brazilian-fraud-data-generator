---
description: "Bump project version atomically across VERSION, pyproject.toml, and CHANGELOG"
agent: "documentation-keeper"
tools:
  - changes
  - editFiles
---

# Version Bump

Bump synthfin-data version atomically across all version files.

## Context

Bump type: **${{ input "Bump type: major | minor | patch" }}**

Release name: **${{ input "Release codename (e.g., Agentes, Qualidade)" }}**

Changes summary: **${{ input "Brief summary of changes in this release" }}**

## Instructions

1. Read current version from `VERSION`, `pyproject.toml`, and `docs/CHANGELOG.md`
2. Calculate next version based on bump type (semver)
3. Update atomically:
   - `VERSION` → new version string
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `docs/CHANGELOG.md` → new version section with table entry and changes
4. Verify all three files show the same version
5. Report: old → new version, files updated
