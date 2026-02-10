# pytest Skill Reference

## Project Convention: Top-Level Test Functions

**RULE**: Always write pytest tests as top-level functions, NOT grouped in test classes.

### Correct Pattern
```python
def test_something() -> None:
    assert True

def test_another_thing(monkeypatch: pytest.MonkeyPatch) -> None:
    assert True
```

### Wrong Pattern (Do NOT use)
```python
class TestSomething:
    def test_something(self) -> None:
        assert True
```

---

## Type Hints in Tests

Always add type hints to test function parameters:

```python
def test_with_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test using fixtures with proper type hints."""
    pass
```

### Common Fixture Type Hints
- `tmp_path: Path` - Temporary directory for file operations
- `monkeypatch: pytest.MonkeyPatch` - Environment variable and attribute mocking
- `fixture_name: FixtureType` - Custom fixtures from conftest.py

---

## Fixtures

### Using tmp_path for Temporary Files

**PREFERRED**: Use pytest's built-in `tmp_path` fixture for automatic cleanup.

```python
def test_with_temp_files(tmp_path: Path) -> None:
    """Create temporary files that are automatically cleaned up."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")

    # Read and test
    assert config_file.read_text() == "key: value"
    # Automatic cleanup after test
```

**NOT PREFERRED**: Manual tempfile operations (requires cleanup).

```python
# Avoid this pattern
import tempfile
import os

with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
    temp_path = f.name

try:
    # test code
    pass
finally:
    os.unlink(temp_path)  # Manual cleanup needed
```

### Custom Fixtures with tmp_path

```python
@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a config file for testing."""
    config_data = {"key": "value"}

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_file  # No manual cleanup needed
```

---

## Environment Variables with monkeypatch

Use `monkeypatch` for setting/clearing environment variables with automatic rollback:

```python
def test_env_var_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test with environment variable override."""
    monkeypatch.setenv("MY_VAR", "test-value")

    # MY_VAR is set in this test
    assert os.getenv("MY_VAR") == "test-value"

    # Automatically reset after test


def test_env_var_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ensures environment variable is NOT set."""
    monkeypatch.delenv("MY_VAR", raising=False)

    # MY_VAR is not set
    assert os.getenv("MY_VAR") is None
```

---

## Test Organization

Organize tests with comment sections:

```python
# Basic functionality tests


def test_basic_operation() -> None:
    pass


def test_another_basic() -> None:
    pass


# Edge case tests


def test_edge_case_empty() -> None:
    pass


def test_edge_case_special_chars() -> None:
    pass


# Integration tests


def test_full_workflow() -> None:
    pass
```

---

## Test Style Guidelines

### Function Naming
- Start with `test_` prefix
- Use descriptive names: `test_override_list_with_multi_value` ✓
- Avoid generic names: `test_something` ✗

### Assertions
- Use simple `assert` statements
- Add comments explaining complex assertions

```python
def test_config_override() -> None:
    config = load_config(config_file)

    # Value should be overridden by environment variable
    assert config["key"] == "env-value"
```

### Docstrings
- Always add docstrings explaining what the test validates

```python
def test_override_nested_key(temp_config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that nested config keys can be overridden via environment variables."""
    pass
```

---

## Best Practices

1. **One concept per test**: Each test should verify one specific behavior
2. **Clear test names**: Names should explain what is being tested
3. **Use fixtures**: Reduce code duplication with fixtures
4. **Type hints everywhere**: All parameters and return types
5. **Automatic cleanup**: Use `tmp_path` and `monkeypatch` instead of manual cleanup
6. **Top-level functions only**: Never use test classes
7. **Group related tests**: Use comment sections to organize logically related tests

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py -v

# Run specific test
uv run pytest tests/test_config.py::test_override_scalar_value -v

# Run with coverage
uv run pytest --cov=src

# Stop on first failure
uv run pytest -x
```

---

## Common Patterns in This Project

### Configuration Testing with YAML + Environment Variables

```python
@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a test config file."""
    config_data = {"api-key": "default", "cors": {"allow-origins": ["http://localhost"]}}
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return config_file


def test_override_scalar_value(
    config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding scalar config values via env vars."""
    monkeypatch.setenv("LLMOCK_API_KEY", "env-override")
    config = load_config(config_file)
    assert config["api-key"] == "env-override"


def test_override_list_value(
    config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test overriding list values with semicolon-separated env vars."""
    monkeypatch.setenv("LLMOCK_CORS_ALLOW_ORIGINS", "http://prod.com;http://api.com")
    config = load_config(config_file)
    assert config["cors"]["allow-origins"] == ["http://prod.com", "http://api.com"]
```

