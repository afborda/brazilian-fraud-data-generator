---
description: "Use when editing documentation: CHANGELOG format, INDEX.md sync, governance rules, version consistency, permanent vs ephemeral docs."
applyTo: "docs/**"
---

# Documentation Rules

## The 5 Governance Rules
1. **Changelog mandatory**: Every behavioral change → entry in `docs/CHANGELOG.md`
2. **INDEX.md in sync**: Doc created/renamed/deleted → update `docs/INDEX.md`
3. **Planning docs ephemeral**: Delivered → record in CHANGELOG → delete → update INDEX
4. **No duplicates**: Check INDEX.md before creating new docs
5. **Deprecation header**: Outdated docs → `> ⚠️ DEPRECATED: [reason]` before deletion

## Permanent Docs (NEVER delete)
- `docs/CHANGELOG.md`, `docs/INDEX.md`, `ARCHITECTURE.md`, `README.md`, `docs/README.md`

## Permanent Reference (update, NEVER delete)
- `docs/analysis/ANALISE_PROFUNDA.md`, `docs/ARQUITETURA.md`
- `docs/fraudes/`, `docs/pesquisa_mercado/`, `docs/documentodeestudos/`

## CHANGELOG Format
```markdown
## v{X.Y} — {Name} ({date})

### {Theme}

- **{Feature/Fix}**: {description}
```

## Version Consistency
- Version must match in: `VERSION`, `pyproject.toml`, `docs/CHANGELOG.md`
- Always update all three atomically

## Writing Style
- Use Portuguese for CHANGELOG entries (project convention)
- Be specific: what changed, why, and impact
- Reference file paths when applicable
