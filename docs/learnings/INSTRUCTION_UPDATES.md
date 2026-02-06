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
