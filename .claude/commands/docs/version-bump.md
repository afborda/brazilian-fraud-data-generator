# Version Bump

Bump synthfin-data version atomically across all version files.

## Arguments

- `$BUMP_TYPE` — One of: `major`, `minor`, `patch`
- `$RELEASE_NAME` — Release codename (e.g., Agentes, Qualidade)
- `$CHANGES` — Brief summary of changes in this release

## Process

1. Read current version from:
   - `VERSION` — single line version string
   - `pyproject.toml` — `version = "X.Y.Z"`
   - `docs/CHANGELOG.md` — latest version in table and section header

2. Calculate next version (semver):
   - major: X+1.0
   - minor: X.Y+1
   - patch: X.Y.Z+1

3. Update atomically:
   - `VERSION` → new version string
   - `pyproject.toml` → update version field
   - `docs/CHANGELOG.md`:
     - Add to version table: `| v{new} | **{RELEASE_NAME}** | {CHANGES} | {date} |`
     - Add section: `## v{new} — {RELEASE_NAME} ({date})`
     - Add changelog entries

4. Verify: all three files show same version

5. Report: old → new, files changed, verification status
