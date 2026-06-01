from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import inspect

from app.core.config import settings
from app.models.orm import (
    BraintreeSubscriptions,
    FeatureStore,
    Ga4Events,
    Ga4IdentityBridge,
    OpenwebEngagement,
    PushlySubscribers,
    SailthruNewsletter,
    TrackonomicsClicks,
    TransunionDemographics,
    ZephrUsers,
)

ALL_MODEL_CLASSES = [
    ZephrUsers,
    Ga4Events,
    Ga4IdentityBridge,
    BraintreeSubscriptions,
    SailthruNewsletter,
    PushlySubscribers,
    OpenwebEngagement,
    TrackonomicsClicks,
    TransunionDemographics,
    FeatureStore,
]


def test_all_orm_models_instantiate_without_db() -> None:
    for ModelClass in ALL_MODEL_CLASSES:
        inst = ModelClass()
        assert isinstance(inst, ModelClass)


def test_uuid4_default_generates_valid_uuid() -> None:
    user = ZephrUsers(
        email="test@example.com",
        registration_date=datetime.utcnow(),
    )
    assert isinstance(user.user_id, uuid.UUID)
    assert user.user_id.version == 4


def test_table_args_schema_matches_settings() -> None:
    for ModelClass in ALL_MODEL_CLASSES:
        assert ModelClass.__table_args__["schema"] == settings.database.schema


def test_feature_store_has_64_columns() -> None:
    mapper = inspect(FeatureStore)
    column_count = len(list(mapper.columns))
    assert column_count == 64, f"Expected 64 columns, got {column_count}"
