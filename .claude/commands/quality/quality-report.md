# Quality Report

Run full quality assessment and generate a comprehensive report.

## Arguments

- `$SCOPE` — One of: full, transactions_only, rides_only, field:{field_name}
- `$SEED` — Random seed for reproducibility (default: 42)

## Process

1. Generate fresh sample:
   ```bash
   python generate.py --size 10MB --output /tmp/quality_check --seed $SEED --format json
   ```

2. Run quality benchmark:
   ```bash
   python benchmarks/data_quality_benchmark.py
   ```

3. Run schema validation:
   ```bash
   python check_schema.py /tmp/quality_check/transactions_00000.jsonl
   ```

4. Compare against baselines:
   - Overall score: 9.70/10 (A+)
   - AUC-ROC: 0.9991
   - Reference: `REALISM_METRICS.json`

5. For field-specific scope, analyze:
   - Distribution shape (ref: `.claude/kb/synthetic-data/concepts/distributions.md`)
   - Statistical tests: KS-test (continuous), chi-squared (categorical)

6. Output report:
   ```
   ## Quality Report — synthfin-data v{version}

   **Overall**: {score}/10 ({grade}) | **AUC-ROC**: {value}

   | Battery        | Score | Status |
   |----------------|-------|--------|
   | Completeness   | X.XX  | ✅/⚠️  |
   | Distributions  | X.XX  | ✅/⚠️  |
   | Fraud Signals  | X.XX  | ✅/⚠️  |
   | ...            |       |        |

   **Regressions**: {list or "None"}
   **Recommendations**: {actionable items}
   ```
