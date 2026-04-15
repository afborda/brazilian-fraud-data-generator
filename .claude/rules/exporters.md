---
description: ExporterProtocol interface, batching strategy, streaming write patterns
paths:
  - "src/fraud_generator/exporters/**"
---

# Exporter Rules

## ExporterProtocol
- Base: `exporters/base.py`
- Required: `export_batch(batch)`, `extension`, `format_name`
- Register in `__init__.py` via `get_exporter(format_name)`

## Batching
- JSON: line-by-line streaming (lowest memory)
- CSV: ~5k records per batch via pandas
- Parquet: ~10k records per batch via pyarrow

## Memory (P3)
- NEVER accumulate entire dataset before writing
- Files >1GB: numbered parts (`_00000.jsonl`, `_00001.jsonl`)
- Current P3 issue: CSV/Parquet still accumulate

## New Exporter Checklist
1. Create `exporters/{name}_exporter.py`
2. Implement ExporterProtocol
3. Register in `exporters/__init__.py`
4. Add to CLI args in `cli/args.py`
5. Test small (<1MB) and large (>100MB)
6. Update CHANGELOG.md
