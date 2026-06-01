"""Database writer for synthetic seed data.

Provides ORM bulk-save and SQLAlchemy Core bulk-insert paths.
All writes are batched to avoid memory pressure.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.models.orm.base import Base

logger = structlog.get_logger(__name__)


class DbWriter:
    """Handles batched bulk inserts for all synthetic seed tables.

    Two write paths:
    - write_batch: ORM path via session.bulk_save_objects() — used for tables
      with manageable row counts (≤ 100K rows).
    - write_batch_core: SQLAlchemy Core path via session.execute(insert(...)) —
      used for high-volume tables (ga4_events ~15M, trackonomics ~500K) where
      ORM object instantiation overhead is prohibitive.
    """

    def __init__(self, session_factory: sessionmaker[Session], batch_size: int) -> None:
        """Initialise the writer.

        Args:
            session_factory: SQLAlchemy sync sessionmaker bound to the sync engine.
            batch_size: Maximum rows per database commit.
        """
        self._session_factory = session_factory
        self._batch_size = batch_size

    def write_batch(self, objects: list[Base], table_name: str) -> int:
        """Write ORM objects in batches using bulk_save_objects.

        Opens a fresh session per batch to avoid long-lived transactions.

        Args:
            objects: List of ORM model instances to insert.
            table_name: Used for structured logging only.

        Returns:
            Total number of rows inserted.

        Raises:
            SQLAlchemyError: On any database error.
        """
        logger.info("db_writer.write_batch.start", table=table_name, total=len(objects))
        total_written = 0
        t0 = time.monotonic()

        for i in range(0, len(objects), self._batch_size):
            chunk = objects[i : i + self._batch_size]
            try:
                with self._session_factory() as session:
                    session.bulk_save_objects(chunk)
                    session.commit()
            except SQLAlchemyError as exc:
                logger.error(
                    "db_writer.write_batch.error",
                    table=table_name,
                    batch_start=i,
                    error=str(exc),
                )
                raise
            total_written += len(chunk)
            logger.debug(
                "db_writer.write_batch.chunk",
                table=table_name,
                written=total_written,
                total=len(objects),
            )

        elapsed = time.monotonic() - t0
        logger.info(
            "db_writer.write_batch.done",
            table=table_name,
            rows=total_written,
            elapsed_s=round(elapsed, 2),
        )
        return total_written

    def write_batch_core(
        self,
        table_class: type[Base],
        rows: list[dict[str, Any]],
        table_name: str,
    ) -> int:
        """Write rows using Core INSERT — bypasses ORM overhead for high-volume tables.

        Callers must include all required column values (including primary keys)
        in each dict, since Base.__init__ is not called.

        Args:
            table_class: ORM model class (used to resolve the mapped Table object).
            rows: List of column-value dicts. Must include primary key.
            table_name: Used for structured logging only.

        Returns:
            Total rows inserted.

        Raises:
            SQLAlchemyError: On any database error.
        """
        logger.info("db_writer.write_core.start", table=table_name, total=len(rows))
        total_written = 0
        t0 = time.monotonic()

        for i in range(0, len(rows), self._batch_size):
            chunk = rows[i : i + self._batch_size]
            try:
                with self._session_factory() as session:
                    session.execute(insert(table_class), chunk)
                    session.commit()
            except SQLAlchemyError as exc:
                logger.error(
                    "db_writer.write_core.error",
                    table=table_name,
                    batch_start=i,
                    error=str(exc),
                )
                raise
            total_written += len(chunk)
            logger.debug(
                "db_writer.write_core.chunk",
                table=table_name,
                written=total_written,
                total=len(rows),
            )

        elapsed = time.monotonic() - t0
        logger.info(
            "db_writer.write_core.done",
            table=table_name,
            rows=total_written,
            elapsed_s=round(elapsed, 2),
        )
        return total_written

    def truncate_table(self, table_name: str, schema: str) -> None:
        """Truncate a single table with CASCADE.

        Args:
            table_name: Unqualified table name.
            schema: Database schema name.

        Raises:
            SQLAlchemyError: On any database error.
        """
        from sqlalchemy import text

        sql = f"TRUNCATE TABLE {schema}.{table_name} RESTART IDENTITY CASCADE"
        try:
            with self._session_factory() as session:
                session.execute(text(sql))
                session.commit()
        except SQLAlchemyError as exc:
            logger.error("db_writer.truncate.error", table=table_name, error=str(exc))
            raise
        logger.info("db_writer.truncate.done", table=table_name)

    def truncate_all_tables(self, schema: str) -> None:
        """Truncate all 10 seed tables in reverse FK-safe order.

        Reverse of insertion order: feature_store → ... → zephr_users.

        Args:
            schema: Database schema name.
        """
        # Reverse insertion order to satisfy FK constraints.
        tables = [
            "feature_store",
            "transunion_demographics",
            "trackonomics_clicks",
            "openweb_engagement",
            "pushly_subscribers",
            "sailthru_newsletter",
            "braintree_subscriptions",
            "ga4_identity_bridge",
            "ga4_events",
            "zephr_users",
        ]
        logger.info("db_writer.truncate_all.start", schema=schema)
        for table in tables:
            self.truncate_table(table, schema)
        logger.info("db_writer.truncate_all.done", schema=schema)
