# Full TDD Workflow Recipe

This recipe executes a complete Test-Driven Development workflow.

## Steps

1. **Understand Requirements**
   - Analyze the feature requirements
   - Identify edge cases and acceptance criteria

2. **Write Failing Tests**
   - Create test file if needed
   - Write comprehensive unit tests
   - Run tests to verify they fail

3. **Implement Feature**
   - Write minimal code to pass tests
   - Focus on making tests green

4. **Refactor**
   - Clean up implementation
   - Improve code quality
   - Ensure tests still pass

5. **Documentation**
   - Add docstrings and comments
   - Update README if needed

## Execution

```bash
# Run tests before implementing
pytest tests/ -v --tb=short

# After implementation
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Success Criteria

- All tests pass
- Code coverage > 80%
- No linting errors
- Documentation updated
