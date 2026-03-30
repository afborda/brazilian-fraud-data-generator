# AI Agent Instructions for synthfin-data

## Project Overview

High-performance synthetic data generator for **Brazilian banking & ride-share fraud detection**. Generates realistic transaction/ride datasets (JSONL, CSV, Parquet, MinIO/S3) at MB–TB scale. Primary use: ML model training, system testing, fraud research.

## Architecture

**Two execution modes** — both share `--seed`, `--fraud-rate`, `--type {transactions|rides|all}`:

| Mode | Entry | Pipeline | Key Args |
|------|-------|----------|----------|
| Batch | `generate.py` | Generator → Exporter → Disk | `--size`, `--format`, `--workers` |
| Stream | `stream.py` | Generator → Connection → Network | `--target {stdout\|kafka\|webhook}`, `--rate` |

**Strategy pattern**: Exporters (`ExporterProtocol`) and Connections (`ConnectionProtocol`) are interchangeable via registries (`get_exporter()`, `get_connection()`).

**Entity chain**: `Customer` → `Device` → `Transaction` (banking) or `Customer` → `Driver` → `Ride` (ride-share). Profiles are assigned once per customer and stay sticky.

> Domain-specific rules are in scoped instructions: see `.github/instructions/generators.instructions.md`, `exporters.instructions.md`, `config.instructions.md`.

## Quick Commands

```bash
pip install -r requirements.txt
python3 generate.py --size 100MB --output ./data          # batch transactions
python3 generate.py --size 100MB --type rides --output ./data  # batch rides
python3 stream.py --target stdout --rate 5                 # stream to terminal
python3 check_schema.py                                    # validate output
docker run --rm -v $(pwd)/output:/output afborda/synthfin-data:latest generate.py --size 1GB --output /output
```

## Key Conventions

- **CPF**: Always valid (use `validators/cpf.py`), store as string, never mock
- **Config pattern**: Modules export `*_LIST`, `*_WEIGHTS`, `get_*()` — never hardcode values
- **Timestamps**: Naive datetime, no timezone. Brazilian context assumed
- **Fraud injection**: Fraud = modified normal record (field combinations), not separate record type
- **Seed order**: Set `random.seed()` early, before any generator construction

## Critical Pitfalls

1. Profile assignment is sticky — don't regenerate per-record
2. Weights: `random.choices()` handles unnormalized, but pre-caching requires sum=1.0
3. Ride distance: always Haversine, never Euclidean
4. Batch ≠ stream: generators initialized for one mode cannot be reused in the other
5. P2: `random.choices()` per-record = 25% overhead (use WeightCache)
6. P3: CSV/Parquet OOM on >1GB (use streaming `export_batch()` chunks)

## Documentation Governance

Rules enforced on **every change**:

1. **Changelog mandatory**: Every behavioral change → entry in [docs/CHANGELOG.md](docs/CHANGELOG.md)
2. **INDEX.md in sync**: Doc created/renamed/deleted → update [docs/INDEX.md](docs/INDEX.md)
3. **Planning docs are ephemeral**: Once delivered → record in CHANGELOG → delete → update INDEX
4. **No duplicates**: Check INDEX.md before creating new docs
5. **Deprecation header**: Outdated docs get `> ⚠️ DEPRECATED: [reason]` before deletion

**Permanent docs** (never delete): `docs/CHANGELOG.md`, `docs/INDEX.md`, `ARCHITECTURE.md`, `README.md`, `docs/README.md`

**Permanent reference** (update, never delete): `docs/analysis/ANALISE_PROFUNDA.md`, `docs/ARQUITETURA.md`, `docs/fraudes/`, `docs/pesquisa_mercado/`, `docs/documentodeestudos/`

## Agent Architecture

This project uses a dual-platform agent system:

| Platform | Agents | Instructions | Commands | KB |
|----------|--------|-------------|----------|----|
| VS Code Copilot | `.github/agents/*.agent.md` | `.github/instructions/*.instructions.md` | `.github/prompts/*.prompt.md` | — |
| Claude Code | `.claude/agents/{domain}/*.md` | `.claude/rules/*.md` | `.claude/commands/{domain}/*.md` | `.claude/kb/{domain}/` |

**Active agents**: orchestrator (default), fraud-pattern-engineer, data-quality-analyst, synthfin-explorer, test-generator, ci-cd-specialist, performance-optimizer, config-architect, documentation-keeper

See `AGENTS.md` for the full routing table and multi-agent patterns.
