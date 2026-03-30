---
description: "Run full quality assessment and generate report for synthfin-data output"
agent: "data-quality-analyst"
tools:
  - terminal
  - changes
---

# Quality Report

Generate a comprehensive quality report for the synthfin-data output.

## Context

Scope: **${{ input "Scope: full | transactions_only | rides_only | field:{field_name}" }}**

Seed: **${{ input "Random seed for reproducibility (default: 42)" }}**

## Instructions

1. Generate a fresh sample:
   ```bash
   python generate.py --size 10MB --output /tmp/quality_check --seed {seed} --format json
   ```
2. Run the quality benchmark:
   ```bash
   python benchmarks/data_quality_benchmark.py
   ```
3. Run schema validation:
   ```bash
   python check_schema.py /tmp/quality_check/transactions_00000.jsonl
   ```
4. Compare results against baseline:
   - Overall score baseline: 9.70/10 (A+)
   - AUC-ROC baseline: 0.9991
   - Reference: `REALISM_METRICS.json`
5. For field-specific scope, also analyze:
   - Distribution shape (reference: `.claude/kb/synthetic-data/concepts/distributions.md`)
   - Statistical tests (KS-test for continuous, chi-squared for categorical)
6. Generate report with:
   - Overall score and grade
   - Per-battery breakdown table
   - Regressions flagged with severity
   - Specific recommendations
