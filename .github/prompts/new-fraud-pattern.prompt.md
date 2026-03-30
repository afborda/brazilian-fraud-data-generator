---
description: "Create a new fraud pattern type with enricher signals for synthfin-data"
agent: "fraud-pattern-engineer"
tools:
  - changes
  - editFiles
---

# New Fraud Pattern

Create a new fraud pattern for the synthfin-data generator.

## Context

The user wants to add fraud pattern: **${{ input "Fraud pattern name (e.g., pix_social_engineering)" }}**

Category: **${{ input "Category: banking_transaction | banking_account | banking_pix | rideshare" }}**

Description: **${{ input "Brief description of the fraud behavior" }}**

## Instructions

1. Read `.claude/kb/brazilian-banking/specs/fraud-types.yaml` for existing patterns
2. Read `src/fraud_generator/config/fraud_patterns.py` for current implementation
3. Read `.claude/kb/brazilian-banking/patterns/fraud-injection.md` for injection pipeline
4. Verify the pattern key doesn't already exist
5. Create the pattern following the config convention:
   - key: snake_case unique identifier
   - name: human-readable name (Portuguese)
   - category: one of the categories above
   - weight: proportional to other patterns in same category
   - signals: list of enricher signals that should trigger
   - anomaly_multiplier: between 1.5 and 5.0
6. Map enricher signals — create new enricher if needed
7. Update `docs/CHANGELOG.md` with the new pattern
8. Show confidence score and summary
