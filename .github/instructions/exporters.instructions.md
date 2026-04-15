---
description: "Use when editing exporters: JSON, CSV, Parquet, Arrow IPC, MinIO, or database export modules. Covers ExporterProtocol interface, batching strategy, streaming write patterns."
applyTo: "src/fraud_generator/exporters/**"
---

# Exporter Rules

## ExporterProtocol (MUST implement)
- Abstract base: `src/fraud_generator/exporters/base.py`
- Required: `export_batch(batch: List[dict])`, `extension` property, `format_name` property
- Registry: Register in `__init__.py` via `get_exporter(format_name)` factory

## Batching Strategy
- Exporters handle batching internally — callers pass chunks, not single records
- JSON: Line-by-line streaming (1 record at a time, lowest memory)
- CSV: Accumulate ~5k records → write via pandas DataFrame
- Parquet: Accumulate ~10k records → write via pyarrow Table

## Memory Constraints (P3)
- NEVER accumulate entire dataset in memory before writing
- Use streaming/chunked write pattern for CSV and Parquet
- For files >1GB: write in numbered parts (e.g., `transactions_00000.jsonl`, `_00001.jsonl`)
- Current P3 issue: CSV/Parquet still accumulate — fix needs streaming rewrite

## New Exporter Checklist
1. Create `src/fraud_generator/exporters/{name}_exporter.py`
2. Implement `ExporterProtocol` (export_batch, extension, format_name)
3. Register in `src/fraud_generator/exporters/__init__.py`
4. Add format to CLI args in `src/fraud_generator/cli/args.py`
5. Test with both small (<1MB) and large (>100MB) datasets
6. Update `docs/CHANGELOG.md`
