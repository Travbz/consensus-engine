# Consensus Engine Tests

## Overview
This directory contains the test suite for the Consensus Engine. The tests cover unit testing, integration testing, and interface testing.

## Setup

1. Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

2. Set up environment variables for API testing:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Test Structure
- `test_engine.py` - Core engine unit tests
- `test_models.py` - LLM model implementation tests
- `test_integration.py` - Full system integration tests
- `test_interfaces.py` - CLI and web interface tests

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test types:
```bash
# Unit tests only
pytest -m "not integration"

# Integration tests only
pytest -m integration

# Interface tests only
pytest tests/test_interfaces.py
```

### Run with coverage:
```bash
pytest --cov=consensus_engine --cov-report=term-missing
```

### Run with logging:
```bash
pytest --log-cli-level=INFO
```

### Run a specific test:
```bash
pytest tests/test_engine.py::test_basic_consensus
```

## Test Categories

### Unit Tests
Basic component testing without external dependencies:
- Engine functionality
- Model implementations
- Configuration handling
- Response parsing

### Integration Tests
Full system testing with real API calls:
- Complete discussion flows
- Multiple concurrent discussions
- Error recovery
- Long-form discussions

### Interface Tests
Testing user interfaces:
- CLI commands
- Web interface functionality
- Error handling
- Port management

## Test Configuration

The `pytest.ini` file contains settings for:
- Test discovery patterns
- Marker definitions
- Logging configuration
- Default execution options

## Skipping Tests

### Skip integration tests (no API keys):
```bash
pytest -m "not integration"
```

### Skip specific test:
```bash
pytest -k "not test_name"
```

## Writing New Tests

### Adding a unit test:
```python
@pytest.mark.unit
def test_new_feature():
    # Test implementation
    assert expected == actual
```

### Adding an integration test:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_new_integration():
    # Integration test implementation
    result = await some_async_operation()
    assert result is not None
```

### Adding an interface test:
```python
@pytest.mark.interface
def test_new_interface_feature(cli_runner):
    result = cli_runner.invoke(command, ["--arg"])
    assert result.exit_code == 0
```

## Common Issues

### API Rate Limits
Integration tests may fail due to API rate limits. Solutions:
1. Add delays between tests
2. Use the `@pytest.mark.skipif` decorator
3. Mock the API calls for development

### Database Tests
Tests use SQLite in-memory database by default. To test with a different database:
1. Set the `CONSENSUS_ENGINE_DB_URL` environment variable
2. Update the database fixture in conftest.py

### Async Tests
Remember to:
1. Use the `@pytest.mark.asyncio` decorator
2. Make async test functions coroutines
3. Use `await` with async operations

## Contributing Tests

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate markers
3. Include docstrings explaining test purpose
4. Update this README if adding new test types

## Test Coverage

Monitor test coverage:
```bash
pytest --cov=consensus_engine --cov-report=html
```

This generates a coverage report in `htmlcov/index.html`