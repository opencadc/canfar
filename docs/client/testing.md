# Testing

This document provides comprehensive information about testing [opencadc/canfar](https://github.com/opencadc/canfar).

## Overview

Canfar uses [pytest](https://pytest.org/) as its testing framework. The test suite includes unit tests, integration tests, and end-to-end tests that verify the functionality of the client library.

## Prerequisites

To run tests for Canfar, you need:

1. **Valid CANFAR Account**: Access to the CANFAR Science Platform
2. **X.509 Certificate**: For authentication with CANFAR services
3. **Python Environment**: Set up with uv

For certificate generation, refer to the [get started](get-started.md) section.

## Running Tests

### Basic Test Execution

Run all tests:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run tests with coverage report:
```bash
uv run pytest --cov
```

### Test Categories

Canfar tests are organised with markers to help you run specific subsets:

#### Slow Tests

Some tests are marked as "slow" because they involve:
- Network operations with CANFAR services
- Waiting for session state changes
- Authentication timeouts
- Long-running operations

**Skip slow tests for faster development:**
```bash
uv run pytest -m "not slow"
```

**Run only slow tests:**
```bash
uv run pytest -m "slow"
```

#### Integration Tests

Tests that interact with external services:
```bash
uv run pytest -m "integration"
```

#### Unit Tests

Fast, isolated tests:
```bash
uv run pytest -m "unit"
```

### Test Methodology

Tests are organised in the `tests/` directory and follow a specific naming convention that mirrors the source code structure. This approach ensures that tests are easy to locate and maintain.

The naming convention is as follows:

- If the source file is `canfar/path/to/file.py`, the corresponding test file will be `tests/test_path_to_file.py`.
- If the source file is `canfar/module.py`, the corresponding test file will be `tests/test_module.py`.

For example:

- The tests for `canfar/client.py` are located in `tests/test_client.py`.
- The tests for `canfar/auth/oidc.py` are located in `tests/test_auth_oidc.py`.

This structure makes it straightforward to find the tests associated with a particular module or file.

## Development Workflow

For efficient development, follow this testing workflow:

1. **During Development**: Run fast tests only
   ```bash
   uv run pytest -m "not slow"
   ```

2. **Before Committing**: Run the full test suite
   ```bash
   uv run pytest
   ```

3. **Debugging Specific Issues**: Run individual test files
   ```bash
   uv run pytest tests/test_session.py
   ```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "order: marks tests that need to run in a specific order",
]
```

## Continuous Integration

In CI environments, all tests (including slow ones) are executed to ensure complete validation. The CI pipeline:

1. Sets up authentication with CANFAR
2. Runs the complete test suite
3. Generates coverage reports
4. Cleans up authentication artifacts

## Writing Tests

When contributing new tests:

1. **Follow the naming convention**: Create a test file that mirrors the source file's path and name.
2. **Mark slow tests**: Add `@pytest.mark.slow` to any test that involves network operations, interacts with external services, or has long execution times. This allows developers to skip these tests for a faster development cycle.
3. **Use appropriate markers**: Mark tests as `unit`, `integration`, etc.
4. **Add docstrings**: Document what each test verifies.

Example of a slow test:
```python
import pytest

@pytest.mark.slow
def test_long_running_operation():
    """Test that involves waiting or network operations."""
    # Test implementation
    pass
```


## Troubleshooting

### Authentication Issues
- Ensure your X.509 certificate is valid and not expired
- Check that you have access to the CANFAR Science Platform
- Verify your certificate is in the correct location (`~/.ssl/`)

### Slow Test Timeouts
- Slow tests have built-in timeouts (typically 60 seconds)
- If tests consistently timeout, check your network connection
- Platform availability may affect test execution times

### Test Failures
- Check if the CANFAR Science Platform is accessible
- Verify your authentication credentials
- Review test logs for specific error messages
