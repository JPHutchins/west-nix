# west-nix Test Suite

This is a language-agnostic test suite for all west-nix implementations.

## Structure

```
tests/
├── fixtures/          # West manifest fixtures
│   └── *.yaml        # Various west.yaml test cases
├── test_*.py         # Test cases that run against all implementations
└── pyproject.toml    # Test suite dependencies
```

## Running Tests

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov
```

## Adding Tests

1. Add west.yaml fixtures to `fixtures/`
2. Create test cases in `test_*.py` files
3. Tests should invoke the CLI of each implementation and verify output
