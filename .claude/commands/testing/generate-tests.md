# Generate Tests

Generate pytest tests for a specific synthfin-data module.

## Arguments

- `$MODULE` — Module path relative to `src/fraud_generator/` (e.g., `validators/cpf`, `config/banks`, `generators/customer`)
- `$TYPE` — Test type: `unit`, `integration`, or `coverage-audit`

## Process

1. Read the source module at `src/fraud_generator/$MODULE.py`
2. Read `tests/conftest.py` for available fixtures
3. Read existing tests in `tests/unit/` for style reference
4. Generate test file at `tests/unit/test_{module_name}.py`:
   - Use pytest functions (not unittest.TestCase)
   - Use `generate_valid_cpf()` for CPF (never mock)
   - Set `random.seed()` before generator construction
   - Test behavior, not implementation details
   - Include: happy path, edge cases, error cases
5. Run `pytest tests/unit/test_{module_name}.py -v`
6. Fix any failures — iterate until green
7. Report: tests created, coverage, gaps
