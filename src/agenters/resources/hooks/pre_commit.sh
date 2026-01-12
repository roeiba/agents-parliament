#!/bin/bash
# Pre-commit hook for code quality checks
# This hook runs before Claude commits code changes

set -e

echo "Running pre-commit checks..."

# Python linting (if available)
if command -v ruff &> /dev/null; then
    echo "Running ruff linter..."
    ruff check . --fix --quiet
fi

# Format code (if available)
if command -v black &> /dev/null; then
    echo "Running black formatter..."
    black . --quiet
fi

# Type checking (if available)
if command -v mypy &> /dev/null; then
    echo "Running mypy type checker..."
    mypy . --ignore-missing-imports --quiet || true
fi

# Run tests
if [ -d "tests" ]; then
    echo "Running tests..."
    python -m pytest tests/ -q --tb=line
fi

echo "Pre-commit checks complete!"
