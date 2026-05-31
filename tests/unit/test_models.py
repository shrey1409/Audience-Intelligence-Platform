"""Unit tests for ORM models — no database connection required."""

from __future__ import annotations

import uuid
import warnings

import pytest


# Suppress Pydantic UserWarning about 'schema' field shadowing throughout this module
@pytest.fixture(autouse=True)
def suppress_pydantic_warnings() -> None:
    """Suppress the Pydantic field-shadow UserWarning globally for this test session."""
    warnings.filterwarnings("ignore", category=UserWarning)


def test_all_orm_models_instantiate_without_db() -> None:
    """Every ORM model can be instantiated without a database connection."""
    from datetime import datetime, timezone

    from app.models.orm.braintree_subscriptions import BraintreeSubscriptions
    from app.models.orm.feature_store import FeatureStore
    from app.models.orm.ga4_events import Ga4Events
    from app.models.orm.ga4_identity_bridge import Ga4IdentityBridge
    from app.models.orm.openweb_engagement import OpenwebEngagement
    from app.models.orm.pushly_subscribers import PushlySubscribers
    from app.models.orm.sailthru_newsletter import SailthruNewsletter
    from app.models.orm.trackonomics_clicks import TrackonomicsClicks
    from app.models.orm.transunion_demographics import TransunionDemographics
    from app.models.orm.zephr_users import ZephrUsers

    now = datetime.now(timezone.utc)
    uid = uuid.uuid4()

    assert isinstance(
        ZephrUsers(email="test@example.com", registration_date=now), ZephrUsers
    )
    assert isinstance(
        Ga4Events(
            user_pseudo_id="abc123",
            event_name="page_view",
            event_date=now.date(),
            event_timestamp=now,
        ),
        Ga4Events,
    )
    assert isinstance(
        Ga4IdentityBridge(
            user_pseudo_id="abc123", user_id=uid, first_seen_at=now, last_seen_at=now
        ),
        Ga4IdentityBridge,
    )
    assert isinstance(
        BraintreeSubscriptions(
            user_id=uid,
            braintree_customer_id="bt_123",
            plan_id="sports_plus",
            status="active",
            amount="9.99",  # type: ignore[arg-type]
            started_at=now,
        ),
        BraintreeSubscriptions,
    )
    assert isinstance(SailthruNewsletter(email="test@example.com"), SailthruNewsletter)
    assert isinstance(
        PushlySubscribers(
            user_id=uid, external_id=str(uid), platform="ios", opted_in_at=now
        ),
        PushlySubscribers,
    )
    assert isinstance(
        OpenwebEngagement(user_id=uid, event_type="comment", engaged_at=now),
        OpenwebEngagement,
    )
    assert isinstance(
        TrackonomicsClicks(user_id=uid, advertiser_id="adv_123", click_timestamp=now),
        TrackonomicsClicks,
    )
    assert isinstance(
        TransunionDemographics(
            hashed_email="abc" * 20,
            match_confidence="0.85",  # type: ignore[arg-type]
            match_date=now.date(),
        ),
        TransunionDemographics,
    )
    assert isinstance(FeatureStore(), FeatureStore)


def test_uuid4_default_callable_is_set() -> None:
    """The user_id column default is the uuid.uuid4 callable."""
    from sqlalchemy import inspect as sa_inspect

    from app.models.orm.zephr_users import ZephrUsers

    mapper = sa_inspect(ZephrUsers)
    col = mapper.columns["user_id"]
    assert col.default is not None, "user_id has no column default"
    # SQLAlchemy stores the callable — verify it's uuid4 by name
    fn = col.default.arg
    assert callable(fn), f"Expected callable default, got {type(fn)}"
    assert fn.__name__ == "uuid4", f"Expected uuid4, got {fn.__name__}"


def test_table_args_schema_matches_settings() -> None:
    """Every ORM model's __table_args__ schema matches settings.database.schema."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from app.core.config import settings  # noqa: PLC0415

    from app.models.orm.braintree_subscriptions import BraintreeSubscriptions
    from app.models.orm.feature_store import FeatureStore
    from app.models.orm.ga4_events import Ga4Events
    from app.models.orm.ga4_identity_bridge import Ga4IdentityBridge
    from app.models.orm.openweb_engagement import OpenwebEngagement
    from app.models.orm.pushly_subscribers import PushlySubscribers
    from app.models.orm.sailthru_newsletter import SailthruNewsletter
    from app.models.orm.trackonomics_clicks import TrackonomicsClicks
    from app.models.orm.transunion_demographics import TransunionDemographics
    from app.models.orm.zephr_users import ZephrUsers

    all_models = [
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
    expected = settings.database.schema
    for model in all_models:
        args = model.__table_args__
        actual = args["schema"] if isinstance(args, dict) else args[-1]["schema"]
        assert actual == expected, (
            f"{model.__name__}.__table_args__['schema'] == {actual!r}, "
            f"expected {expected!r}"
        )


def test_feature_store_has_64_columns() -> None:
    """FeatureStore ORM model has exactly 64 mapped columns."""
    from sqlalchemy import inspect as sa_inspect

    from app.models.orm.feature_store import FeatureStore

    col_count = len(sa_inspect(FeatureStore).columns)
    assert col_count == 64, f"Expected 64 columns, got {col_count}"
