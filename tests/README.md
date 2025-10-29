# Tabcorp MCP Server - Testing Infrastructure

Comprehensive testing suite for the Tabcorp MCP Server with 28 deployed tools.

## Overview

This testing infrastructure provides:
- **Unit Tests**: Fast, isolated tests with mocked HTTP responses
- **Integration Tests**: Real API calls with actual Tabcorp endpoints
- **Performance Tests**: Load testing and benchmarking
- **CI/CD Automation**: GitHub Actions workflows for continuous testing

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and utilities
├── unit/                    # Unit tests (mocked)
│   ├── oauth/
│   │   └── test_oauth_tools.py       # OAuth authentication tests
│   ├── racing/
│   │   └── test_racing_tools.py      # Racing API tests
│   └── sports/
│       └── test_sports_tools.py      # Sports API tests
├── integration/             # Integration tests (real API)
│   └── test_real_api.py              # End-to-end API tests
└── performance/             # Performance tests
    └── test_performance.py           # Load and benchmark tests
```

## Setup

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

Or with uv:

```bash
uv pip install -r requirements-test.txt
```

### Configure Credentials (for integration tests)

Set environment variables:

```bash
export TAB_CLIENT_ID="your_client_id"
export TAB_CLIENT_SECRET="your_client_secret"
export TAB_USERNAME="your_username"
export TAB_PASSWORD="your_password"
```

## Running Tests

### Run All Unit Tests

```bash
pytest tests/unit -v
```

### Run Specific Category

```bash
# OAuth tests only
pytest tests/unit/oauth -v -m oauth

# Racing tests only
pytest tests/unit/racing -v -m racing

# Sports tests only
pytest tests/unit/sports -v -m sports
```

### Run Integration Tests

```bash
# Requires credentials in environment
pytest tests/integration -v -m integration
```

### Run Performance Tests

```bash
pytest tests/performance -v -m performance
```

### Run Smoke Tests (Quick Validation)

```bash
pytest -v -m smoke
```

### Skip Integration Tests

```bash
pytest -v -m "not integration"
```

### Run with Coverage Report

```bash
pytest tests/unit --cov=src/tab_mcp --cov-report=html --cov-report=term
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests with mocked responses
- `@pytest.mark.integration` - Integration tests requiring real API access
- `@pytest.mark.mock` - Tests using mocked HTTP responses
- `@pytest.mark.performance` - Performance and load tests
- `@pytest.mark.oauth` - OAuth authentication tests
- `@pytest.mark.racing` - Racing API tests
- `@pytest.mark.sports` - Sports API tests
- `@pytest.mark.footytab` - FootyTAB API tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.smoke` - Quick validation tests

## CI/CD Integration

GitHub Actions workflows automatically run tests on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

### Workflows

1. **Unit Tests** - Run on all Python versions (3.10, 3.11, 3.12)
2. **Integration Tests** - Run on push/manual with credentials from secrets
3. **Smoke Tests** - Quick validation on every run
4. **Code Quality** - Black formatting and Ruff linting
5. **Security Scan** - Bandit security analysis

## Writing New Tests

### Unit Test Template

```python
import pytest
import respx
from httpx import Response
from tab_mcp.server import create_server

@pytest.mark.unit
@pytest.mark.your_category
class TestYourFeature:
    def test_success_case(self, mock_context, respx_mock):
        # Mock HTTP response
        route = respx_mock.get("https://api.beta.tab.com.au/your/endpoint")
        route.return_value = Response(200, json={"result": "success"})
        
        # Call tool
        server = create_server()
        result = server.tool_manager.tools["your_tool"].fn(
            mock_context,
            access_token="test_token"
        )
        
        # Verify
        assert route.called
        assert result["result"] == "success"
```

### Integration Test Template

```python
import pytest
from tab_mcp.server import create_server

@pytest.mark.integration
@pytest.mark.slow
class TestRealAPI:
    def test_real_endpoint(self, real_context, access_token):
        server = create_server()
        result = server.tool_manager.tools["your_tool"].fn(
            real_context,
            access_token=access_token
        )
        
        assert isinstance(result, dict)
        # Add assertions based on expected response
```

## Test Coverage Goals

- **Overall Coverage**: Target 80%+
- **Critical Paths**: 100% (OAuth, error handling)
- **Tool Functions**: 90%+
- **Helper Functions**: 85%+

## Current Test Coverage

### OAuth Tools (3/3 tools tested)
- ✅ `tab_oauth_password_grant`
- ✅ `tab_oauth_refresh`
- ✅ `tab_oauth_client_credentials`

### Racing Tools (11/11 major tools tested)
- ✅ `racing_get_all_meeting_dates`
- ✅ `racing_get_meetings`
- ✅ `racing_get_all_races_in_meeting`
- ✅ `racing_get_race`
- ✅ `racing_get_next_to_go`
- ✅ `racing_get_race_form`
- ✅ `racing_get_runner_form`
- ✅ `racing_get_approximates`
- ✅ `racing_get_open_jackpots`
- ✅ `racing_get_jackpot_pools`

### Sports Tools (10/10 major tools tested)
- ✅ `sports_get_all_open`
- ✅ `sports_get_open_sport`
- ✅ `sports_get_open_competition`
- ✅ `sports_get_open_tournament`
- ✅ `sports_get_open_match_in_competition`
- ✅ `sports_get_open_match_in_tournament`
- ✅ `sports_get_next_to_go`
- ✅ `sports_get_all_results`
- ✅ `sports_get_resulted_sport`
- ✅ `sports_get_resulted_competition`

## Troubleshooting

### Integration Tests Fail

If integration tests fail:
1. Verify credentials are set in environment
2. Check Tabcorp API is accessible
3. Verify account has necessary permissions
4. Check if test data (races, sports) is available

### Mock Tests Fail

If mock tests fail:
1. Verify respx is installed
2. Check mock response format matches expected structure
3. Ensure fixtures are imported correctly

### Performance Tests Slow

If performance tests are slow:
1. Run with fewer iterations
2. Use `pytest -k "not slow"` to skip slow tests
3. Check system resources

## Best Practices

1. **Fast Tests**: Keep unit tests under 0.1s each
2. **Isolated**: Each test should be independent
3. **Clear Names**: Use descriptive test function names
4. **Arrange-Act-Assert**: Follow AAA pattern
5. **DRY**: Use fixtures for common setup
6. **Comprehensive**: Test success, error, and edge cases

## Performance Benchmarks

| Operation | Target | Current |
|-----------|--------|----------|
| OAuth token request | < 500ms | TBD |
| Racing dates query | < 200ms | TBD |
| Race details query | < 300ms | TBD |
| Sports list query | < 200ms | TBD |
| Error handling | < 100ms | TBD |

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Ensure >80% coverage for new code
3. Add integration test if API interaction
4. Update this README with test coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [respx documentation](https://lundberg.github.io/respx/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [MCP Server documentation](https://modelcontextprotocol.io/)
