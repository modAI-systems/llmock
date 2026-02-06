# PROJECT KNOWLEDGE BASE (LLM-Optimized)

## AI WAY OF WORKING (MANDATORY)

This project is designed for AI-first development. All agents MUST follow these protocols:

### 1. Technology Skill Acquisition
- **RULE**: NEVER work on a technology without verified skills.
- **PROCESS**: 
    1. If a task involves a new technology/library: **STOP**.
    2. Perform a `web_search` or `librarian` task to investigate best practices, common pitfalls, and API usage.
    3. Document findings in `docs/skills/<tech-name>.md`.
    4. Only proceed with implementation once the skill file exists and is reviewed.

### 2. Architecture First
- **RULE**: Architecture MUST be adapted/reviewed before coding starts.
- **PROCESS**:
    1. For any new feature/package, update `docs/architecture/DECISIONS.md`.
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

## PROJECT OVERVIEW
- **Goal**: LLM-optimized AI project.
- **Core Stack**: Python + FastAPI + uv (build system)

## WHERE TO LOOK
- `docs/architecture/`: System design and decisions.
- `docs/skills/`: Tech-specific knowledge base.
- `docs/learnings/`: Persistent memory of user corrections.
- `docs/tests/`: Global test configurations and results.
- `src/llmock3/`: Main application source code.
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
uv run python -m llmock3   # Run the application
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

### Application
```bash
uv run python -m llmock3   # Start the FastAPI server
```
