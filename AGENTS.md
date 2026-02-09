# PROJECT KNOWLEDGE BASE (LLM-Optimized)

## AI WAY OF WORKING (MANDATORY)

This project is designed for AI-first development. All agents MUST follow these protocols:

### 0. Context Loading (ALWAYS FIRST)
- **RULE**: ALWAYS read project context before starting ANY task.
- **PROCESS**:
    1. Read `docs/ARCHITECTURE.md` to understand system design.
    2. Read `docs/learnings/*.md` to learn from past corrections.
    3. Check `.agents/skills/` for relevant technology skills.
- **WHY**: These files contain critical knowledge from past work. Skipping them leads to repeated mistakes and inconsistent code.

### 1. Technology Skill Acquisition
- **RULE**: NEVER work on a technology without verified skills.
- **PROCESS**:
    1. If a task involves a new technology/library: **STOP**.
    2. Perform a web search or use the dedicated task agent to investigate best practices, common pitfalls, and API usage.
    3. Document findings in `.agents/skills/<tech-name>/SKILL.md`.
    4. Only proceed with implementation once the skill file exists and is reviewed.

### 2. Architecture First
- **RULE**: Architecture MUST be adapted/reviewed before coding starts.
- **PROCESS**:
    1. For any new feature/package, update `docs/DECISIONS.md`.
    2. Ensure the architecture aligns with the overall project goals.

### 3. Learning from Corrections
- **RULE**: If the user corrects a mistake, update the instructions immediately.
- **PROCESS**:
    1. Identify the root cause of the mistake.
    2. Update `docs/learnings/INSTRUCTION_UPDATES.md` with a new rule to prevent recurrence.
    3. Append relevant rules to `AGENTS.md` if they are project-wide.

### 4. Test-Driven Completion
- **RULE**: A task is NOT done until tests pass.
- **PROCESS**:
    1. Every work package MUST include tests.
    2. Tests MUST pass before the task is marked `completed` in the todo list.

### 5. Code Quality Gate (MANDATORY)
- **RULE**: ALWAYS run linting and formatting before completing any code task.
- **PROCESS**:
    1. Run `uv run ruff format src tests` to format code.
    2. Run `uv run ruff check src tests` to lint code.
    3. Fix any issues before marking task as complete.

### 6. Documentation Updates for API Changes (MANDATORY)
- **RULE**: When adding, modifying, or deleting API endpoints, ALWAYS update documentation.
- **PROCESS**:
    1. Check `README.md` for endpoint references and usage examples.
    2. Check `docs/ARCHITECTURE.md` for endpoint documentation.
    3. Check any other docs that reference API endpoints.
    4. Update all affected documentation before marking task as complete.

## PROJECT OVERVIEW
- **Core Stack**: Python + FastAPI + uv (build system)

## WHERE TO LOOK
- `docs/ARCHITECTURE.md`: System design documentation.
- `docs/DECISIONS.md`: Architecture decisions.
- `docs/learnings/`: Persistent memory of user corrections.
- `.agents/skills/`: Tech-specific knowledge base.
- `src/llmock/`: Main application source code.
- `tests/`: Test files.

## COMMANDS

### uv (Package Manager / Build System)
ALWAYS use `uv` to run Python commands. Never use `pip` or raw `python` directly.

```bash
uv sync                    # Install dependencies from pyproject.toml
uv sync --all-extras       # Install with all optional dependencies (dev, etc.)
uv add <package>           # Add a dependency
uv add --dev <package>     # Add a dev dependency
uv run <command>           # Run a command in the virtual environment
uv run python -m llmock   # Run the application
uv run pytest              # Run tests
```

### ruff (Linter & Formatter)
```bash
uv run ruff format src tests         # Format code (rewrites files)
uv run ruff format --check src tests # Check formatting without changes
uv run ruff check src tests          # Lint code
uv run ruff check --fix src tests    # Lint and auto-fix issues
```

### pytest (Testing)
```bash
uv run pytest              # Run all tests
uv run pytest -v           # Run tests with verbose output
uv run pytest -x           # Stop on first failure
uv run pytest --tb=short   # Shorter traceback
```

**Test Style**: Always write tests as top-level functions, NOT grouped in classes.
```python
# CORRECT
def test_something() -> None:
    assert True

# WRONG - do not use test classes
class TestSomething:
    def test_something(self) -> None:
        assert True
```

### Docker
ALWAYS use explicit `docker <object> <verb>` syntax. Never use shorthand commands.

```bash
# CORRECT - use explicit subcommands
docker image build -t llmock .       # Build image
docker container run -p 8000:8000 llmock  # Run container
docker container ls                  # List containers
docker image ls                      # List images
docker container rm <id>             # Remove container
docker container logs <id>           # View logs

# WRONG - do not use shorthand
docker build ...
docker run ...
docker ps
docker images
```

### Application
```bash
uv run python -m llmock   # Start the FastAPI server
```
