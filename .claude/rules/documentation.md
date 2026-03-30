---
description: CHANGELOG format, INDEX.md sync, governance rules, version consistency, permanent vs ephemeral docs
paths:
  - "docs/**"
  - "VERSION"
  - "pyproject.toml"
---

# Documentation Rules

## 5 Governance Rules
1. Changelog mandatory — every behavioral change → `docs/CHANGELOG.md`
2. INDEX.md in sync — doc created/renamed/deleted → update INDEX
3. Planning docs ephemeral — delivered → CHANGELOG → delete → update INDEX
4. No duplicates — check INDEX before creating
5. Deprecation header — outdated → `> ⚠️ DEPRECATED: [reason]`

## Permanent (NEVER delete)
- `CHANGELOG.md`, `INDEX.md`, `ARCHITECTURE.md`, `README.md`, `docs/README.md`

## Permanent Reference (update, NEVER delete)
- `ANALISE_PROFUNDA.md`, `ARQUITETURA.md`, `fraudes/`, `pesquisa_mercado/`, `documentodeestudos/`

## Version
- Must match in: VERSION, pyproject.toml, docs/CHANGELOG.md
- Always update all three atomically
