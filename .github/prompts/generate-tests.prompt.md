---
description: "Generate pytest tests for a specific module or audit test coverage"
agent: "test-generator"
tools:
  - changes
  - editFiles
  - terminalLastCommand
---

# Generate Tests

Generate pytest tests for synthfin-data modules.

## Context

Target module: **${{ input "Module path (e.g., validators/cpf, config/banks, generators/customer)" }}**

Type: **${{ input "Type: unit | integration | coverage-audit" }}**

## Instructions

1. Read the source module at `src/fraud_generator/{module}.py`
2. Read `tests/conftest.py` for available fixtures
3. Read existing tests in `tests/unit/` for style reference
4. Generate tests following project conventions:
   - pytest functions (not unittest)
   - Use `generate_valid_cpf()` for CPF (never mock)
   - Set `random.seed()` before generator construction
   - Test behavior, not implementation
5. Run `pytest tests/unit/test_{module}.py -v` to verify
6. Fix any failures
7. Report: tests created, coverage areas, remaining gaps
