# New Fraud Pattern

Create a new fraud pattern type with enricher signals for synthfin-data.

## Arguments

- `$PATTERN_NAME` — Fraud pattern key (snake_case, e.g., pix_social_engineering)
- `$CATEGORY` — One of: banking_transaction, banking_account, banking_pix, rideshare
- `$DESCRIPTION` — Brief description of the fraud behavior

## Process

1. Load context:
   - `.claude/kb/brazilian-banking/specs/fraud-types.yaml` — existing patterns
   - `src/fraud_generator/config/fraud_patterns.py` — current implementation
   - `.claude/kb/brazilian-banking/patterns/fraud-injection.md` — injection pipeline

2. Validate:
   - Pattern key `$PATTERN_NAME` must not already exist
   - Category `$CATEGORY` must be valid
   - At least 2 enricher signals must be identified

3. Create pattern entry in `src/fraud_generator/config/fraud_patterns.py`:
   ```python
   "$PATTERN_NAME": {
       "name": "Human-readable name",
       "category": "$CATEGORY",
       "weight": 0.XX,  # proportional to category
       "signals": ["signal_1", "signal_2"],
       "anomaly_multiplier": X.X,  # 1.5 to 5.0
       "description": "$DESCRIPTION",
   }
   ```

4. Map enricher signals — if new signal needed, create enricher module

5. Update `docs/CHANGELOG.md`

6. Report confidence score and summary
