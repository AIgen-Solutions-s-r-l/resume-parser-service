# Contributing to Resume Parser Service

Thank you for your interest in contributing to the Resume Parser Service! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

### Prerequisites

- Python 3.12+
- MongoDB 7.0+
- Docker and Docker Compose (recommended)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/resume-parser-service.git
   cd resume-parser-service
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Copy environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Start MongoDB (using Docker)**
   ```bash
   docker-compose up -d mongodb
   ```

7. **Run the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. Write your code following our coding standards
2. Add or update tests as needed
3. Update documentation if applicable
4. Run the test suite locally

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(parser): add support for multi-page PDFs
fix(auth): resolve token expiration issue
docs(readme): update installation instructions
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) guidelines
- Maximum line length: 100 characters
- Use type hints for all function signatures
- Write docstrings for all public functions and classes

### Code Formatting

We use automated formatters. Run before committing:

```bash
# Format code
black app/
isort app/

# Or use pre-commit
pre-commit run --all-files
```

### Type Hints

All functions should include type hints:

```python
async def get_resume(user_id: int) -> dict[str, Any]:
    """
    Retrieve a resume by user ID.

    Args:
        user_id: The user's unique identifier

    Returns:
        The resume data as a dictionary

    Raises:
        ResumeNotFoundError: If no resume exists for the user
    """
    ...
```

### Documentation

- Write clear docstrings using Google style
- Update README.md for user-facing changes
- Add inline comments for complex logic

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test
pytest app/tests/test_resume_parser.py -v

# Run only unit tests
pytest app/tests/ -m "not integration"
```

### Writing Tests

- Place tests in `app/tests/`
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures from `conftest.py`
- Aim for meaningful test coverage

**Example Test:**
```python
@pytest.mark.asyncio
async def test_get_resume_success(mongo_mock, valid_resume_data):
    """Test successful resume retrieval."""
    mongo_mock.find_one.return_value = valid_resume_data

    result = await get_resume_by_user_id(user_id=1)

    assert result["user_id"] == 1
    mongo_mock.find_one.assert_called_once()
```

## Pull Request Process

### Before Submitting

1. **Run the full test suite**
   ```bash
   pytest
   ```

2. **Run linters**
   ```bash
   flake8 app/
   mypy app/
   ```

3. **Run security scan**
   ```bash
   bandit -r app/ -x app/tests/
   ```

4. **Update documentation** if needed

### Submitting a PR

1. Push your branch to your fork
2. Create a Pull Request against `main`
3. Fill out the PR template completely
4. Link any related issues

### PR Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
```

### Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. No merge conflicts
4. Documentation updated if applicable

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Potential implementation approach (optional)

## Security

If you discover a security vulnerability, please do NOT open a public issue. Instead, email the maintainers directly.

## Questions?

- Open a GitHub Discussion for general questions
- Check existing issues for similar problems
- Review the documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
