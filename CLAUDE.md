# synthfin-data

## WHAT — Project Context

High-performance synthetic data generator for **Brazilian banking & ride-share fraud detection**. Generates realistic labeled datasets (JSONL, CSV, Parquet, MinIO/S3) at MB–TB scale for ML training, system testing, and fraud research. Current score: 9.70/10 (A+), AUC-ROC 0.9991.

## WHAT — Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Data | Faker, pandas, pyarrow, numpy |
| Streaming | kafka-python, requests (webhook) |
| Storage | boto3 (MinIO/S3), SQLAlchemy |
| Testing | pytest (unit + integration) |
| Deploy | Docker, GitHub Actions |

## WHAT — Project Map

```
generate.py          # Batch entry point (→ BatchRunner/MinIORunner/SchemaRunner)
stream.py            # Streaming entry point (→ stdout/kafka/webhook)
src/fraud_generator/
├── generators/      # Entity creation (customer → device → transaction/ride)
├── enrichers/       # Fraud signal pipeline (11 enrichers, 17+ signals)
├── exporters/       # Output formats (Strategy: ExporterProtocol)
├── connections/     # Stream targets (Strategy: ConnectionProtocol)
├── config/          # Domain configs (*_LIST + *_WEIGHTS + get_*() pattern)
├── profiles/        # Behavioral profiles (7 TX types, ride preferences)
├── models/          # Data classes (Customer, Device, Transaction, Ride)
├── schema/          # Declarative JSON schema system
├── validators/      # CPF validation (Brazilian ID)
├── utils/           # WeightCache, compression, parallel, streaming
├── cli/             # CLI args, runners, workers (multiprocessing)
└── licensing/       # Tier validation
benchmarks/          # Quality (9.70/10), format, streaming, multiprocessing
tests/               # pytest: unit/ (11 files) + integration/ (2 files)
schemas/             # JSON schema definitions
```

## WHY — Key Decisions

- **Entity chain pattern**: Customer → Device → Transaction (never generate TX without parent entities)
- **Profile stickiness**: Once assigned, a customer's behavioral profile is fixed for all transactions
- **Fraud injection**: Fraud is field combinations on normal records, NOT separate record types
- **Config convention**: Every config exports `*_LIST`, `*_WEIGHTS`, `get_*()` — never hardcode values
- **CPF always valid**: Use `validators/cpf.py` — store as string, validate on generation
- **Batch ≠ Stream**: Generators initialized in one mode cannot be reused in the other
- **Random seed order**: Set `random.seed()` early, before any generator construction

## HOW — Commands

```bash
# Generate batch
python generate.py --size 100MB --format jsonl --output ./data --seed 42
python generate.py --size 1GB --type rides --format parquet --output ./data

# Stream
python stream.py --target stdout --rate 5
python stream.py --target kafka --kafka-topic transactions --rate 100

# Validate schema
python check_schema.py output/transactions_00000.jsonl

# Run quality benchmark
python benchmarks/data_quality_benchmark.py

# Tests
pytest tests/ -v
```

## HOW — Verification

IMPORTANT: Always run after changes:
```bash
pytest tests/ -v --tb=short
```

## HOW — Configuration

See `.github/instructions/` for scoped coding rules per domain.
See `.claude/kb/` for knowledge base (Brazilian banking, synthetic data patterns).

## Scoped Rules

| Rule File | Scope | Content |
|-----------|-------|---------|
| `generators.md` | `src/**/generators/**` | Entity chain, fraud injection, profiles, WeightCache |
| `exporters.md` | `src/**/exporters/**` | ExporterProtocol, batching, streaming writes |
| `config.md` | `src/**/config/**` | *_LIST + *_WEIGHTS + get_*() convention |
| `testing.md` | `tests/**` | pytest, fixtures, CPF handling, seed management |
| `cicd.md` | `.github/workflows/**` | Workflows, triggers, secrets, Docker |
| `performance.md` | `benchmarks/**` | WeightCache, streaming IO, profiling |
| `documentation.md` | `docs/**` | Governance rules, CHANGELOG, versioning |

## Agent Routing

The **orchestrator** is the default entry point. See `AGENTS.md` for full registry.

| Keywords | → Agent |
|----------|---------|
| fraud, pattern, enricher, PIX, risk | fraud-pattern-engineer |
| quality, benchmark, AUC-ROC, distribution | data-quality-analyst |
| explore, architecture, impact, health | synthfin-explorer |
| test, pytest, coverage, fixture | test-generator |
| workflow, CI/CD, pipeline, lint, gate | ci-cd-specialist |
| slow, memory, OOM, optimize, profile | performance-optimizer |
| config, bank, merchant, *_LIST, weight | config-architect |
| changelog, version, bump, docs, INDEX | documentation-keeper |

## Active Work

- P1: Evolving fraud patterns (enricher pipeline approach, 25 banking + 11 ride-share)
- P3: CSV/Parquet streaming export (OOM on >1GB needs fix)
- Agent architecture: 9 dual-platform agents (VS Code + Claude Code) with orchestrator
