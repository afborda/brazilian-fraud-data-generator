---
description: "Use when editing test files: pytest conventions, fixture patterns, conftest.py, test naming, seed management, CPF handling in tests."
applyTo: "tests/**"
---

# Testing Rules

## Conventions
- Use pytest functions, NOT `unittest.TestCase` classes
- Test file naming: `tests/unit/test_{module}.py` or `tests/integration/test_{workflow}.py`
- Test function naming: `test_{behavior}_when_{condition}` or `test_{behavior}_{expected_result}`

## Fixtures
- Project-wide fixtures in `tests/conftest.py`: `temp_output_dir`, `test_seed`, `sample_customer_data`, `sample_transaction_data`
- Module-specific fixtures in local `conftest.py` files
- Use `tmp_path` (pytest built-in) for temporary file operations
- Use `monkeypatch` for environment variable manipulation

## CPF Handling
- NEVER mock CPF validation — always use real `generate_valid_cpf()` from `validators/cpf.py`
- CPF must be a valid 11-digit string
- Import: `from fraud_generator.validators.cpf import generate_valid_cpf`

## Seed Management
- Always set `random.seed()` in test setup for reproducibility
- Use `test_seed` fixture (value: 42) for consistent results
- When testing generators, set seed BEFORE constructing the generator

## Test Structure
```python
def test_behavior_when_condition(test_seed):
    # Arrange
    random.seed(test_seed)
    # Act
    result = function_under_test()
    # Assert
    assert result.field == expected_value
```

## What to Test
- Public API behavior, not internal implementation
- Config contracts: `*_LIST` non-empty, `*_WEIGHTS` same length, `get_*()` returns valid
- Generator outputs: required fields present, types correct, ranges valid
- Edge cases: empty input, boundary values, invalid data

## What NOT to Test
- Private methods directly (test via public API)
- Third-party library behavior (Faker, pandas)
- Exact random output values (test distribution properties instead)
