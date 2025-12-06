# Contributing to Drafter

Thank you for your interest in contributing to Drafter! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate in your interactions with other contributors. We aim to foster an inclusive and welcoming community.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/drafter.git
   cd drafter
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the coding standards below

3. Run tests to ensure everything works:
   ```bash
   pytest
   ```

4. Run linters and formatters:
   ```bash
   black drafter/
   ruff check drafter/
   mypy drafter/
   ```

5. Commit your changes with a descriptive commit message:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request on GitHub

### Coding Standards

- **Formatting**: We use [Black](https://black.readthedocs.io/) with a line length of 100
- **Linting**: We use [Ruff](https://github.com/astral-sh/ruff) for fast Python linting
- **Type Hints**: We use [mypy](http://mypy-lang.org/) for static type checking
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Pre-commit hooks**: All commits should pass pre-commit checks

### Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a PR
- Aim for high test coverage of new code
- Place tests in the `tests/` directory
- Name test files with the prefix `test_`

To run tests:
```bash
pytest                  # Run all tests
pytest tests/test_file.py  # Run specific test file
pytest -v              # Verbose output
pytest --cov=drafter   # Run with coverage
```

### Documentation

- Update documentation for any changed functionality
- Add docstrings to new functions and classes
- Update the README.md if you add new features
- Update change_log.md with your changes

## Pull Request Process

1. Ensure your code passes all tests and linters
2. Update documentation as needed
3. Add an entry to `change_log.md` describing your changes
4. The PR will be reviewed by maintainers
5. Address any feedback from reviewers
6. Once approved, your PR will be merged

## Types of Contributions

### Bug Reports

When filing a bug report, please include:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, Drafter version)
- Any relevant error messages or logs

### Feature Requests

When suggesting a feature:
- Explain the problem you're trying to solve
- Describe your proposed solution
- Consider how it fits with the project's goals
- Be open to discussion and alternative approaches

### Code Contributions

We welcome:
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test improvements
- Code refactoring

## Questions?

If you have questions about contributing, feel free to:
- Open an issue on GitHub
- Ask in a PR or issue discussion

Thank you for contributing to Drafter! 🎉
