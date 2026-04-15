# Test Suite

Comprehensive test coverage for synthfin-data.

## Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── __init__.py                    # Test package initialization
├── fixtures/                      # Test data and reusable test files
│   └── .gitkeep
├── unit/                          # Unit tests for individual modules
│   ├── __init__.py
│   └── test_phase_1_optimizations.py
└── integration/                   # Integration tests for complete workflows
    ├── __init__.py
    └── test_workflows.py
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Specific Test File
```bash
pytest tests/unit/test_phase_1_optimizations.py -v
```

### With Coverage
```bash
pytest tests/ --cov=src/fraud_generator --cov-report=html
```

## Test Categories

### Unit Tests (`tests/unit/`)
Test individual modules and components in isolation.

**Current Coverage:**
- `test_phase_1_optimizations.py`: Tests for Phase 1 optimizations
  - `TestWeightCache`: O(log n) sampling tests
  - `TestSkipNone`: JSON field filtering tests
  - `TestMinIOGzip`: Compression extension tests

**To Run:**
```bash
pytest tests/unit/ -v
```

### Integration Tests (`tests/integration/`)
Test complete workflows and component interactions.

**Current Coverage:**
- `test_workflows.py`: End-to-end workflow tests
  - `TestTransactionGeneration`: Full transaction pipeline
  - `TestExportFormats`: Export format compatibility
  - `TestFraudInjection`: Fraud rate validation

**To Run:**
```bash
pytest tests/integration/ -v
```

## Fixtures

Shared test fixtures defined in `conftest.py`:

| Fixture | Purpose |
|---------|---------|
| `temp_output_dir` | Temporary directory for test outputs (auto-cleanup) |
| `test_seed` | Standard seed (42) for reproducible tests |
| `small_batch_size` | Small batch size (100) for unit tests |
| `sample_customer_data` | Sample customer record |
| `sample_transaction_data` | Sample transaction record |
| `sample_ride_data` | Sample ride-share record |

**Usage Example:**
```python
def test_something(temp_output_dir, test_seed, sample_customer_data):
    # Test code here
    pass
```

## Adding New Tests

### Unit Test Template
```python
import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from fraud_generator.module import Component

class TestComponentName(unittest.TestCase):
    """Test component functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.component = Component()
    
    def test_basic_functionality(self):
        """Test basic feature."""
        result = self.component.method()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test Template
```python
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

class TestWorkflow:
    """Test complete workflow."""
    
    def test_full_pipeline(self, temp_output_dir, test_seed):
        """Test end-to-end workflow."""
        # Test code here
        assert True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## Testing Best Practices

1. **Use Fixtures**: Leverage pytest fixtures for setup/teardown
2. **Reproducibility**: Always use `test_seed=42` for deterministic tests
3. **Isolation**: Each test should be independent
4. **Cleanup**: Fixtures handle temporary file cleanup automatically
5. **Clear Names**: Use descriptive test method names
6. **Documentation**: Add docstrings explaining test purpose

## Test Dependencies

Tests require:
- `pytest` (testing framework)
- `pytest-cov` (coverage reporting)
- All dependencies from `requirements.txt`

Install with:
```bash
pip install pytest pytest-cov -r requirements.txt
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```bash
# Run with coverage reporting
pytest tests/ --cov=src/fraud_generator --cov-report=xml

# Run with JUnit output
pytest tests/ --junit-xml=test-results.xml
```

## Known Issues & Limitations

- **MinIO Tests**: MinIO connection tests require environment variables (MINIO_ACCESS_KEY, MINIO_SECRET_KEY)
- **Streaming Tests**: Kafka/Webhook tests may require external services
- **Mock Data**: Current fixtures use sample data; consider expanding with faker integration

## Future Test Plans

- [ ] Expand unit test coverage to 80%+
- [ ] Add async/await tests for streaming scenarios
- [ ] Implement performance regression testing
- [ ] Add property-based tests with hypothesis
- [ ] Mock external services (MinIO, Kafka) for isolated testing

## Troubleshooting

### Test Discovery Issues
```bash
# Ensure __init__.py files exist in all test directories
find tests -type d -exec touch {}/__init__.py \;
```

### Import Errors
```bash
# Verify src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/ -v
```

### Slow Tests
```bash
# Run only fast tests
pytest tests/ -v -m "not slow"

# Identify slowest tests
pytest tests/ --durations=10
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest tests/ -v`
3. Verify coverage: `pytest tests/ --cov=src/fraud_generator`
4. Add documentation to this file if needed

---

**Last Updated**: January 30, 2025  
**Version**: 3.3.0 "Turbo"
