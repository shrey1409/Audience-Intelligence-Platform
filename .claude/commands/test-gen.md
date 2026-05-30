---
description: Generate comprehensive pytest tests for a module — happy path, edge cases, error handling, Faker data, fixtures, mocked dependencies
argument-hint: <module_path>  e.g. "etl/ingestion/zephr.py" or "app/services/persona_service.py"
allowed-tools: Read, Write, Glob, Bash(python3:*), Bash(pytest:*)
---

Read `.claude/CLAUDE.md` to load full project context.

The user passed `$ARGUMENTS` as the module path to generate tests for.

## Step 1 — Read the source module
Read the target file in full. Map every:
- Public function (not starting with `_`)
- Public method on every class
- Exception types raised
- External dependencies called (DB session, Redis, HTTP client, MLflow, Airflow)
- Configuration values read

## Step 2 — Read existing test infrastructure
Read `tests/unit/conftest.py` and `tests/integration/conftest.py` if they exist.
Identify existing fixtures (DB session mocks, Redis mocks, settings override, Faker instance).
Do NOT recreate fixtures that already exist — reuse them.

Read `requirements/dev.txt` to confirm available test libraries (pytest, pytest-asyncio, Faker, httpx, etc.).

## Step 3 — Determine test file location
- If the module is under `app/` or `etl/` or `ml/` with no external service calls → `tests/unit/`
- If the module requires a real DB, Redis, or external API → `tests/integration/`
- File naming: `test_{module_filename}.py` in the appropriate directory
- For nested modules: mirror the source path, e.g. `etl/ingestion/zephr.py` → `tests/unit/ingestion/test_zephr.py`

Check if the test file already exists. If so, read it and augment rather than overwrite.

## Step 4 — Generate tests
Write the complete test file. Requirements:

**Structure:**
```python
"""Tests for {module_path}."""
import pytest
from faker import Faker
from unittest.mock import AsyncMock, MagicMock, patch
# project imports

fake = Faker()
Faker.seed(42)
```

**For every public function/method, write:**
1. `test_{function}_happy_path` — normal inputs, verify correct output
2. `test_{function}_edge_case_{description}` — boundary values (empty list, zero, None where nullable)
3. `test_{function}_raises_{error}` — for each exception the function can raise

**For ETL ingestion modules:**
- Mock the external API client (httpx, requests) — never make real HTTP calls in tests
- Test incremental mode: only rows after `last_run_timestamp` are returned
- Test full_refresh mode: all rows returned regardless of timestamp
- Test API rate limit handling (429 response → retry)
- Test malformed API response (missing expected fields)
- Use `Faker` to generate realistic data matching the source schema

**For ORM model files:**
- Use SQLAlchemy `create_engine("sqlite:///:memory:")` for unit tests
- Test `__repr__` returns a non-empty string
- Test all required fields raise `IntegrityError` if None

**For service layer files:**
- Mock the SQLAlchemy session using `AsyncMock`
- Test that the service calls the correct ORM query
- Test that the service does NOT expose raw ORM objects (returns Pydantic schemas)

**For ML modules:**
- Use `numpy` and `pandas` to create test DataFrames with the 46 feature columns
- Test that feature names match `configs/base.yaml` ml.features.matrix — load from config, not hardcoded
- Test clustering with a small synthetic dataset (100 rows, 46 columns)
- Test propensity score outputs are in [0, 1] range
- Test cold start rules produce one of the 9 valid persona labels

**For API endpoint files:**
- Use `httpx.AsyncClient` with FastAPI `app` as transport
- Test 200 OK for valid input
- Test 422 Unprocessable Entity for invalid input (Pydantic validation)
- Test 404 for unknown user_id
- Test 401/403 if auth is implemented

**Fixtures to define (if not in conftest already):**
```python
@pytest.fixture
def sample_user_id() -> str:
    return str(fake.uuid4())

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.commit = AsyncMock()
    return session

@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.setex = MagicMock()
    return redis
```

**Naming conventions:**
- Test classes: `class Test{ClassName}:` or `class Test{FunctionName}:`
- Test functions: `test_{scenario}_{expected_outcome}`
- Use `@pytest.mark.asyncio` for async tests
- Use `@pytest.mark.parametrize` for multiple input variants of the same logic

## Step 5 — Verify test file syntax
```
python3 -m py_compile {test_file_path} && echo "Syntax OK"
```
Fix any syntax error before reporting.

## Step 6 — Dry-run test collection
```
pytest {test_file_path} --collect-only -q 2>&1 | head -30
```
Verify pytest can collect all tests without import errors.

## Step 7 — Report
```
✓ Test file written: {test_file_path}
  Tests generated: {N}
    - Happy path:   {N}
    - Edge cases:   {N}
    - Error cases:  {N}
  Syntax check:    OK
  Collection:      {N} tests collected

Mocked dependencies:
  - {dependency}: using {mock strategy}

To run:
  pytest {test_file_path} -v
  pytest {test_file_path} -v --cov={module_path} --cov-report=term-missing

Estimated coverage of {module_path}: ~{N}%
```
