from __future__ import annotations

from typing import Any

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all AIP ORM models.

    Invokes Python-callable column defaults at __init__ time so that
    generated PKs (uuid.uuid4) are available immediately after instantiation,
    before the object is flushed to the database.
    """

    def __init__(self, **kwargs: Any) -> None:
        for col in self.__table__.columns:
            if (
                col.name not in kwargs
                and col.default is not None
                and col.default.is_callable
            ):
                kwargs[col.name] = col.default.arg({})  # type: ignore[arg-type]
        # Mirror sqlalchemy's _declarative_constructor: set attrs via descriptors.
        for key, val in kwargs.items():
            setattr(self, key, val)
