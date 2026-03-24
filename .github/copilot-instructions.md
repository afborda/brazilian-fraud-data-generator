# AI Agent Instructions for synthfin-data

## Project Overview

A high-performance synthetic data generator for **Brazilian banking & ride-share fraud detection**. Generates realistic transaction/ride datasets in multiple formats (JSONL, CSV, Parquet, MinIO/S3) at scale (MB–TB). Primary use: ML model training, system testing, fraud research.

## Architecture Patterns

### Three Core Execution Modes (Fundamental to All Work)

1. **Batch Mode** (`generate.py`): In-memory parallel generation → file export
   - Entry point: `generate.py` with `--type {transactions|rides|all}`
   - Pipeline: Generator → Exporter → Disk
   - Key constraint: Memory-efficient streaming for large datasets

2. **Streaming Mode** (`stream.py`): Continuous event generation → target output
   - Entry point: `stream.py` with `--target {stdout|kafka|webhook}`
   - Pipeline: Generator → Connection → Network/Stdout
   - Key pattern: Graceful shutdown signal handling (`_running` flag)

3. **Command-Line Configuration**: Both tools share similar arg patterns
   - Common: `--seed`, `--fraud-rate`, `--workers` (batch only)
   - Type selection: `--type {transactions|rides|all}`
   - Format/Target: `--format {json|csv|parquet}` vs `--target {stdout|kafka|webhook}`

### Strategy Pattern for Extensibility

**Exporters** ([src/fraud_generator/exporters/](src/fraud_generator/exporters/)): Interchangeable export formats
- Abstract base: `ExporterProtocol` defines `export_batch()`, `extension`, `format_name`
- Implementations: `JSONExporter`, `CSVExporter`, `ParquetExporter`, `MinIOExporter`
- Registry: `get_exporter(format_name)` factory returns correct class
- **Key design**: Exporters handle batching; don't assume single-record writes

**Connections** ([src/fraud_generator/connections/](src/fraud_generator/connections/)): Interchangeable streaming targets
- Abstract base: `ConnectionProtocol` defines `connect()`, `send()`, `close()`
- Implementations: `KafkaConnection`, `WebhookConnection`, `StdoutConnection`
- Registry: `get_connection(target_name)` + `is_target_available(target)` checks
- **Key design**: Connections are stateful; manage initialization in `connect()`

### Data Generation Pipeline

**Three Entity Types** with distinct generators:

1. **Transaction Data** (`TransactionGenerator`, config in [src/fraud_generator/config/transactions.py](src/fraud_generator/config/transactions.py))
   - Entities: `Customer` → `Device` → `Transaction`
   - Profile-aware: behavioral profiles determine transaction type/value/channel
   - Fraud injection: Configurable rate, explicit patterns per fraud type (PIX cloning, card takeover, etc.)
   - Key distributions: Weighted random for banks, merchants (MCC), transaction channels

2. **Ride-Share Data** (`RideGenerator`, config in [src/fraud_generator/config/rideshare.py](src/fraud_generator/config/rideshare.py))
   - Entities: `Customer` (passenger) → `Driver` → `Ride`
   - Ride-specific logic: Haversine distance calculation, surge pricing, weather impact
   - Fraud types: GPS spoofing, fake rides, driver collusion
   - Key complexity: Spatial calculations, multi-entity relationships

3. **Behavioral Profiles**: Two systems
   - **Transaction Profiles** ([src/fraud_generator/profiles/behavioral.py](src/fraud_generator/profiles/behavioral.py)): 7 types (young_digital, business_owner, etc.) define transaction behavior
   - **Ride Profiles** ([src/fraud_generator/profiles/ride_behavioral.py](src/fraud_generator/profiles/ride_behavioral.py)): Map customer profiles to ride app preferences, category choice, surge acceptance
   - **Key pattern**: Profiles use `get_*_for_profile()` functions for deterministic behavior per profile type

### Critical Performance Constraints

- **Problem P2**: `random.choices()` called per-record = 25% overhead
  - Solution: Pre-cache weights as numpy arrays, batch decision-making
  - Example: [src/fraud_generator/generators/transaction.py#get_transaction_type_for_profile](src/fraud_generator/generators/transaction.py) calls config weights repeatedly

- **Problem P3**: CSV/Parquet exporters accumulate entire list before writing
  - Solution: Use streaming write pattern (`export_batch()` processes chunks)
  - Avoid: `[item for item in generator]` → list in memory

- **Streaming memory**: JSONL exporter works line-by-line; CSV/Parquet must batch by size, not count

## Key Developer Workflows

### Running Locally

```bash
# Install
pip install -r requirements.txt

# Generate transactions (batch)
python3 generate.py --size 100MB --output ./data

# Generate rides
python3 generate.py --size 100MB --type rides --output ./data

# Stream to terminal
python3 stream.py --target stdout --rate 5
```

### Docker Execution

```bash
# No local Python needed
docker run --rm -v $(pwd)/output:/output \
  afborda/synthfin-data:latest \
  generate.py --size 1GB --output /output
```

### Schema/Format Inspection

Run `python3 check_schema.py` to validate output files match expected structure.

## Conventions & Patterns

### CPF Validation

Brazilian ID (`CPF`) must pass validation algorithm. Use [src/fraud_generator/validators/cpf.py](src/fraud_generator/validators/cpf.py):
- `validate_cpf(cpf_string)`: True/False check
- `generate_valid_cpf()`: Create random valid CPF
- **Convention**: Always store as string, validate on generation, never mock

### Configuration Architecture

Separate config modules for each data domain:
- [src/fraud_generator/config/banks.py](src/fraud_generator/config/banks.py): Bank codes, weights
- [src/fraud_generator/config/merchants.py](src/fraud_generator/config/merchants.py): MCC codes, merchant names, weights
- [src/fraud_generator/config/geography.py](src/fraud_generator/config/geography.py): Brazilian states, cities, coordinates
- [src/fraud_generator/config/rideshare.py](src/fraud_generator/config/rideshare.py): Apps (Uber, 99, InDriver), categories, surge rules

**Pattern**: Config modules export `*_LIST` (all values), `*_WEIGHTS` (distribution), and helper functions `get_*(value)`. Never hardcode values; always reference config.

### Index/Cache Objects

For ride-share: `RideIndex` groups drivers by state for fast lookup. For transactions: `CustomerIndex`/`DeviceIndex` enable stateful generation.
- **Usage**: Pass index to generator constructor; generator calls `index.get()` during loop
- **Memory model**: Index is in-memory lookup table; generators don't store customer state

### Fraud Type Declarations

Transaction fraud types: PIX cloning, card takeover, social engineering, account takeover (config.transactions.FRAUD_TYPES_LIST)
Ride fraud types: GPS spoofing, fake ride, driver collusion, payment fraud (config.rideshare.RIDESHARE_FRAUD_TYPES)
- **Pattern**: Each type has probability weights; frauds are injected as field combinations, not as separate record types

### Timestamp & Timezone

All timestamps are naive datetime (no timezone). Brazilian context assumed.
- Use `datetime.now()` or `datetime.fromtimestamp()` from current wall-clock time
- For reproducibility: Seed `random` module, timestamps are derived from customer/device generation, not absolute time

## Testing & Validation

No automated test suite found in repo. Validation approach:
- `check_schema.py`: Inspect output file structure
- `docs/*.md`: Architecture docs (ANALISE_PROFUNDA.md, PLANO_IMPLEMENTACAO.md) explain design decisions
- Manual testing: Generate small datasets, inspect field distributions with `pandas`

**Future work**: Add pytest tests for fraud injection, profile assignment, schema compliance.

## Cross-Component Dependencies

### Required External Packages (requirements.txt)
- `Faker` (3.8+): Customer names, addresses, phone numbers
- `pandas` (2.0+): CSV operations, data inspection
- `pyarrow` (14.0+): Parquet format
- `boto3` (1.28+): MinIO/S3 upload

### Optional for Streaming (requirements-streaming.txt)
- `kafka-python`: Kafka connections
- Plus base requirements

### Docker Context
- Base image: Python 3.8+
- Volume: `/output` for file export
- Entrypoint: `generate.py` or `stream.py`

## Common Pitfalls & Anti-Patterns

1. **Random seed order matters**: Set `random.seed()` early, before any generator construction. Different seed timing = different datasets.
2. **Profile assignment is sticky**: Once a customer is assigned a profile, it's fixed for all transactions. Don't regenerate per-record.
3. **Weights must be normalized**: Config weights are proportions; `random.choices()` handles unnormalized weights, but pre-caching requires sum=1.0.
4. **Ride distance calculation**: Always use Haversine (great-circle), never Euclidean. See [src/fraud_generator/generators/ride.py#haversine_distance](src/fraud_generator/generators/ride.py).
5. **MinIO URL format**: `s3://bucket/path/prefix` parsed by exporter; credentials via env vars `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`.
6. **Batch vs. stream modes are independent**: A generator initialized in batch mode cannot be reused for streaming; each mode owns its I/O layer.

## Project Status & Known Gaps

**Version**: 3.2.0 (check [VERSION](VERSION) file)

**Known High-Priority Issues** (from RESUMO_EXECUTIVO.md):
- P1: Fraud patterns too simplistic (no sequential patterns, velocity checks)
- P2: Random weight lookup overhead (fixable with caching)
- P3: CSV/Parquet out-of-memory on >1GB (needs streaming export refactor)

**In-Progress**: Ride-share feature expansion (docs/RIDESHARE_TASKS.md)

## Documentation Governance

Rules that apply to **every change** made in this repository. Enforced by the AI agent on every task.

### 1. Changelog is mandatory

Every change that affects observable behavior (code, config, schema, CLI args, output format) **must** generate an entry in [docs/CHANGELOG.md](docs/CHANGELOG.md).
- Follow existing format: version section → themed subsection → bullet describing what changed and why
- Excluded: typo fixes, whitespace, comment-only changes with no behavioral impact
- **Anti-pattern**: completing a task without updating CHANGELOG

### 2. Keep `docs/INDEX.md` in sync

[docs/INDEX.md](docs/INDEX.md) is the master documentation index. Any time a doc is **created, renamed, or deleted**, update INDEX.md accordingly.
- **Anti-pattern**: creating a new `.md` file in `docs/` without registering it in INDEX.md

### 3. Planning/release docs are ephemeral — delete when done

Docs under `docs/planning/`, `docs/release/`, and root-level status reports (`STATUS_FINAL.md`, `ORGANIZATION_COMPLETE.md`, `PHASE_*_INTEGRATION_COMPLETE.md`, `RIDESHARE_TASKS.md`) exist to guide active work. Once the task/phase is **fully delivered**:
1. Record relevant decisions/outcomes in CHANGELOG.md
2. Delete the planning doc
3. Update INDEX.md to remove the reference
- **Do not accumulate**: completed planning docs must not remain in the repo

### 4. Update existing docs — do not duplicate

Before creating a new doc, check if one already covers the same topic using [docs/INDEX.md](docs/INDEX.md).
- If a doc exists: update it
- If the scope is genuinely new: create a new file AND update INDEX.md
- **Anti-pattern**: creating `ANALISE_V2.md` alongside an existing `ANALISE.md`

### 5. Mark before remove — deprecation header

When a doc is identified as outdated but removal is deferred, add this header at the top before anything else:

```markdown
> ⚠️ DEPRECATED: [reason]. Replaced by [link to current doc].
```

Remove the file at the next opportunity (next PR/task touching the same area).

### Permanent docs — never delete

These docs must always exist and stay up to date:
- [docs/CHANGELOG.md](docs/CHANGELOG.md)
- [docs/INDEX.md](docs/INDEX.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [README.md](README.md)
- [docs/README.md](docs/README.md)

### Permanent reference docs — update, never delete

- [docs/analysis/ANALISE_PROFUNDA.md](docs/analysis/ANALISE_PROFUNDA.md)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md)
- [docs/fraudes/](docs/fraudes/) — fraud analysis reference
- [docs/pesquisa_mercado/](docs/pesquisa_mercado/) — market research archive
- [docs/documentodeestudos/](docs/documentodeestudos/) — historical research artifacts

## Documentation References

- **Architecture deep-dive**: [docs/ANALISE_PROFUNDA.md](docs/ANALISE_PROFUNDA.md) (Portuguese)
- **Implementation roadmap**: [PLANO_IMPLEMENTACAO.md](PLANO_IMPLEMENTACAO.md) (Portuguese)
- **Docker publishing**: [docs/DOCKER_HUB_PUBLISHING.md](docs/DOCKER_HUB_PUBLISHING.md)
- **Feature definitions**: [docs/RIDESHARE_TASKS.md](docs/RIDESHARE_TASKS.md)
