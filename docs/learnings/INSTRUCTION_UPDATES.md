# Instruction Updates from Corrections

This file tracks corrections provided by the user to improve future performance.

## Correction Template
### [Date] - [Context]
- **Mistake**: What went wrong?
- **Correction**: What was the correct way?
- **New Rule**: How to prevent this in the future? (Update `AGENTS.md` if necessary)

---

### 2026-02-06 - Test file structure
- **Mistake**: Used `class TestListModels:` and `class TestRetrieveModel:` to group tests in pytest.
- **Correction**: Use top-level functions for tests, not test classes.
- **New Rule**: Always write pytest tests as top-level functions (e.g., `def test_something():`) instead of grouping them in classes.

### 2026-02-06 - Docker command style
- **Mistake**: Used shorthand Docker commands like `docker build` and `docker run`.
- **Correction**: Use explicit subcommands `docker image` and `docker container`.
- **New Rule**: Always use `docker image build` instead of `docker build`, and `docker container run` instead of `docker run`. This applies to all Docker commands - prefer the explicit `docker <object> <verb>` syntax (e.g., `docker container ls`, `docker image ls`, `docker container rm`, etc.).

### 2026-02-06 - Documentation updates for endpoint changes
- **Mistake**: Added `/v1/responses` endpoint without updating documentation (README.md, ARCHITECTURE.md).
- **Correction**: Documentation must be updated whenever endpoints are added, changed, or deleted.
- **New Rule**: When adding, modifying, or removing API endpoints, always check and update all relevant documentation files (README.md, docs/ARCHITECTURE.md, and any other docs that reference endpoints).
