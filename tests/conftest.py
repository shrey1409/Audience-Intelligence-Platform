from __future__ import annotations

import os
import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """PostgreSQL URL for integration tests — requires docker compose up -d postgres."""
    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://aip_user:aip_password@localhost:5432/audience_intelligence",
    )


@pytest.fixture(scope="function")
def test_schema(test_db_url: str) -> Generator[str, None, None]:
    """Creates a fresh test schema, yields schema name, drops it after test."""
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
    os.environ.pop("DATABASE__SCHEMA", None)
