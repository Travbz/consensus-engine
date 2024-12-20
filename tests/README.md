# Consensus Engine Tests

This directory contains all tests for the Consensus Engine project. The tests are organized as follows:

## Directory Structure

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── test_models.py    # Tests for LLM model implementations
│   ├── test_interfaces.py# Tests for external interfaces
│   ├── test_cli.py      # Tests for CLI interface
│   ├── test_web.py      # Tests for web interface
│   └── test_engine.py   # Tests for core engine logic
├── integration/          # Integration tests
│   └── test_engine.py   # End-to-end engine tests
├── mocks/               # Mock implementations
│   ├── clients.py       # Mock LLM clients
│   ├── db.py           # Mock database components
│   └── responses.py    # Mock response data
├── fixtures/            # Test fixtures
│   └── conftest.py     # Shared test fixtures
└── conftest.py         # Root fixtures file
```

## Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together
- **Mocks**: Reusable mock implementations
- **Fixtures**: Shared test setup and utilities

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test categories:
```bash
pytest tests/unit            # Run unit tests only
pytest tests/integration     # Run integration tests only
pytest -m "not integration" # Skip integration tests
```

## Writing New Tests

1. Place unit tests in the appropriate file under `unit/`
2. Place integration tests in `integration/`
3. Add new mocks to the `mocks/` directory
4. Add shared fixtures to `fixtures/conftest.py`

## Test Dependencies

The test suite uses:
- pytest for test running
- pytest-asyncio for async tests
- unittest.mock for mocking