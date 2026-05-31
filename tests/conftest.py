"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

import uuid
import warnings
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session", autouse=True)
def suppress_pydantic_schema_warning() -> None:
    """Suppress Pydantic UserWarning about 'schema' field."""
    warnings.filterwarnings("ignore", category=UserWarning)


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """PostgreSQL URL for integration tests.

    Override via TEST_DATABASE_URL environment variable.
    Requires: docker compose up -d postgres
    """
    import os

    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://aip_user:aip_password@localhost:5432/audience_intelligence",
    )


@pytest.fixture(scope="function")
def test_schema(test_db_url: str) -> Generator[str, None, None]:
    """Create an isolated test schema, yield its name, then drop it.

    Each test function gets its own schema (test_<8hex chars>) so tests
    are fully isolated and can run in parallel.

    Args:
        test_db_url: PostgreSQL connection URL from test_db_url fixture.

    Yields:
        The name of the freshly created test schema.
    """
    from sqlalchemy import create_engine, text

    schema = f"test_{uuid.uuid4().hex[:8]}"
    engine = create_engine(test_db_url)

    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()

    yield schema

    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        conn.commit()

    engine.dispose()
