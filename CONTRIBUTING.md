# Contributing to Tabcorp MCP Server

Thank you for your interest in contributing to the Tabcorp MCP Server! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)
- [Issue Guidelines](#issue-guidelines)
- [Community](#community)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We pledge to:

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Inclusive**: Welcome diverse perspectives and experiences  
- **Be Collaborative**: Work together toward common goals
- **Be Professional**: Maintain constructive and professional communication

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing private information without consent
- Any conduct that would be inappropriate in a professional setting

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed
- **Git** for version control
- **uv** package manager (recommended) or pip
- **Tabcorp API credentials** for testing (optional for documentation)

### Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tab-mcp.git
   cd tab-mcp
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/bencousins22/tab-mcp.git
   ```

### Development Setup

1. **Install dependencies**:
   ```bash
   uv sync  # or: pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (optional for non-API work)
   ```

3. **Verify installation**:
   ```bash
   uv run dev  # Start development server
   # Server should start on http://localhost:8081
   ```

4. **Run tests**:
   ```bash
   pytest tests/unit -v  # Should pass without API credentials
   ```

---

## 💻 Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

**Branch Naming Conventions**:
- `feature/` - New features (e.g., `feature/add-racing-tool`)
- `bugfix/` - Bug fixes (e.g., `bugfix/fix-oauth-refresh`)
- `docs/` - Documentation changes (e.g., `docs/update-api-ref`)
- `test/` - Test improvements (e.g., `test/add-integration-tests`)
- `refactor/` - Code refactoring (e.g., `refactor/optimize-caching`)

### 2. Make Your Changes

- Write clean, readable code following our style guidelines
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Commit Your Changes

**Commit Message Format**:

```
type(scope): brief description

- Detailed explanation of changes
- Why the change was needed
- Any breaking changes or migration notes

Closes #issue_number
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `style`: Code style changes (formatting)
- `chore`: Build/tooling changes

**Examples**:

```bash
git commit -m "feat(racing): add jackpot pool filtering

- Added jurisdiction and date range filters
- Improved error handling for invalid dates
- Updated API reference documentation

Closes #123"
```

### 4. Keep Your Branch Updated

Regularly sync with upstream:

```bash
git fetch upstream
git rebase upstream/main
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## 🎨 Code Style Guidelines

### Python Style

We follow **PEP 8** with some project-specific conventions:

#### Formatting

- **Line Length**: 100 characters (not 88 or 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single for dict keys when appropriate
- **Imports**: Organized (stdlib, third-party, local) with `isort`

**Use Black for automatic formatting**:

```bash
black src/ tests/
```

#### Code Quality

**Run Ruff for linting**:

```bash
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix where possible
```

#### Type Hints

**Always use type hints** for function parameters and return values:

```python
from typing import Dict, List, Optional

async def get_races(
    meeting_id: str,
    race_number: int,
    fixed_odds: bool = False
) -> Dict[str, any]:
    """Get race details with optional fixed odds.

    Args:
        meeting_id: Unique meeting identifier
        race_number: Race number (1-12 typically)
        fixed_odds: Include fixed odds data

    Returns:
        Race details dictionary with runners and markets

    Raises:
        TabcorpAPIError: If API request fails
    """
    pass
```

#### Docstrings

**Use Google-style docstrings**:

```python
def calculate_value(odds: float, probability: float) -> float:
    """Calculate expected value for a bet.

    Args:
        odds: Decimal odds (e.g., 2.50)
        probability: Win probability (0-1)

    Returns:
        Expected value as float

    Examples:
        >>> calculate_value(3.0, 0.4)
        0.2
    """
    return (probability * (odds - 1)) - (1 - probability)
```

#### Naming Conventions

- **Functions/Variables**: `snake_case` (e.g., `get_next_races`, `race_number`)
- **Classes**: `PascalCase` (e.g., `TabcorpAPIError`, `OddsScanner`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TAB_BASE_URL`, `DEFAULT_TIMEOUT`)
- **Private**: Prefix with `_` (e.g., `_validate_token`, `_internal_cache`)

### Code Organization

**File Structure**:

```python
# 1. Module docstring
"""Module description."""

# 2. Imports (grouped and sorted)
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

import httpx
from mcp.server import Server

from .config import Config
from .errors import TabcorpAPIError

# 3. Constants
DEFAULT_TIMEOUT = 30.0
VALID_JURISDICTIONS = {"NSW", "VIC", "QLD"}

# 4. Classes and functions
class MyClass:
    pass

def my_function():
    pass
```

---

## 🧪 Testing Requirements

### Test Coverage

- **Minimum**: 80% code coverage for new features
- **Current**: 31% (we're working to improve this!)
- **Goal**: 90%+ coverage

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only (fast, no API calls)
pytest tests/unit -v

# Integration tests (requires API credentials)
pytest tests/integration -v

# With coverage report
pytest --cov=src/tab_mcp --cov-report=html

# Specific test file
pytest tests/unit/oauth/test_oauth_tools.py -v
```

### Writing Tests

**Test Organization**:

```
tests/
├── unit/              # Unit tests (no external dependencies)
│   ├── oauth/
│   ├── racing/
│   └── sports/
├── integration/       # Integration tests (real API calls)
└── conftest.py        # Shared fixtures
```

**Example Unit Test**:

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tab_mcp.server import tab_oauth_client_credentials

@pytest.mark.asyncio
async def test_client_credentials_success(mock_context):
    """Test successful client credentials authentication."""

    # Arrange
    expected_response = {
        "access_token": "test_token",
        "token_type": "Bearer",
        "expires_in": 3600
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = expected_response
        mock_post.return_value.status_code = 200

        # Act
        result = await tab_oauth_client_credentials(
            mock_context,
            client_id="test_id",
            client_secret="test_secret"
        )

        # Assert
        assert result["access_token"] == "test_token"
        assert "expires_at" in result
        mock_post.assert_called_once()
```

**Example Integration Test**:

```python
import pytest
import os

@pytest.mark.integration
@pytest.mark.asyncio
async def test_racing_get_next_to_go_real_api(authenticated_context):
    """Test next-to-go races with real API."""

    # Skip if no credentials
    if not os.getenv("TAB_CLIENT_ID"):
        pytest.skip("API credentials not configured")

    result = await racing_get_next_to_go(
        authenticated_context,
        access_token=authenticated_context.access_token,
        count=3
    )

    assert "races" in result
    assert len(result["races"]) <= 3
    assert all("meeting_id" in r for r in result["races"])
```

### Test Requirements for PRs

✅ **Required**:
- All existing tests must pass
- New features must have unit tests
- Bug fixes must have regression tests
- Test coverage should not decrease

⚠️ **Nice to Have**:
- Integration tests for API changes
- Performance benchmarks for optimizations
- Edge case testing

---

## 📝 Pull Request Process

### Before Submitting

**Checklist**:

- [ ] Code follows style guidelines (Black + Ruff)
- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

**Run Pre-commit Checks**:

```bash
# Format code
black src/ tests/

# Lint code
ruff check --fix src/ tests/

# Run tests
pytest tests/unit -v

# Check coverage
pytest --cov=src/tab_mcp --cov-report=term
```

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] Added tests
- [ ] All tests pass

## Related Issues
Closes #123
Related to #456
```

### Review Process

1. **Automated Checks**: GitHub Actions runs tests and linting
2. **Code Review**: At least one maintainer reviews the code
3. **Feedback**: Address review comments and update PR
4. **Approval**: Once approved, PR will be merged
5. **Merge**: Squash and merge (maintaining clean history)

### Response Time

- **Initial Review**: Within 3 business days
- **Follow-up**: Within 1-2 business days
- **Urgent Fixes**: Same day for critical bugs

---

## 📚 Documentation

### Documentation Types

**Code Documentation**:
- Docstrings for all public functions and classes
- Inline comments for complex logic
- Type hints for all parameters

**User Documentation**:
- Update `API_REFERENCE.md` for new tools
- Update `GETTING_STARTED.md` for setup changes
- Create tutorials for major features

**Changelog**:
- Add entry to `CHANGELOG.md` under `[Unreleased]`
- Follow Keep a Changelog format

### Documentation Standards

**API Reference Entries**:

```markdown
### tool_name

Brief description of what the tool does.

**Use Case**: When and why to use this tool.

**Parameters**:
- `param1` (type): Description
- `param2` (Optional[type]): Description with default behavior

**Returns**:
```json
{
  "field": "value",
  "another_field": 123
}
```

**Example Usage**:
```python
result = await tool_name(ctx, param1="value")
```

**Errors**:
- `ErrorType`: When this error occurs
```

---

## 🐛 Issue Guidelines

### Reporting Bugs

**Before Submitting**:
- Search existing issues to avoid duplicates
- Verify the bug exists in the latest version
- Collect relevant information (logs, environment)

**Bug Report Template**:

```markdown
## Bug Description
Clear description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. See error

## Expected Behavior
What should happen.

## Actual Behavior  
What actually happens.

## Environment
- OS: [e.g., macOS 14.0]
- Python: [e.g., 3.11.5]
- Version: [e.g., 1.0.0]

## Logs/Screenshots
Paste relevant logs or attach screenshots.

## Additional Context
Any other information.
```

### Feature Requests

**Feature Request Template**:

```markdown
## Feature Description
Clear description of the proposed feature.

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How you think this should work.

## Alternatives Considered
Other approaches you considered.

## Additional Context
Mockups, examples, or references.
```

---

## 👥 Community

### Communication Channels

- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and reviews

### Getting Help

1. **Check Documentation**: [Getting Started](GETTING_STARTED.md), [API Reference](API_REFERENCE.md)
2. **Search Issues**: Look for similar problems
3. **Ask in Discussions**: Create a new discussion thread
4. **Open an Issue**: If you found a bug

### Recognition

Contributors are recognized in:
- `CHANGELOG.md` for each release
- GitHub contributors page
- Special mentions for significant contributions

---

## 🏆 Types of Contributions

We welcome all types of contributions:

### Code Contributions
- New features and tools
- Bug fixes
- Performance optimizations
- Refactoring and code improvements

### Documentation
- Improving existing docs
- Writing tutorials
- Adding examples
- Fixing typos

### Testing
- Writing new tests
- Improving test coverage
- Adding integration tests
- Performance benchmarks

### Design
- UI/UX improvements
- Visual assets
- Architecture proposals

### Community
- Answering questions
- Reviewing pull requests
- Triaging issues
- Helping newcomers

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Thank you for contributing to Tabcorp MCP Server! Your efforts help make this project better for everyone.

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Review existing contributions for examples
- Reach out to maintainers

**Happy coding!** 🚀
