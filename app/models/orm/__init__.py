"""ORM model registry — import all models so they register with Base.metadata."""

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

__all__ = [
    "ZephrUsers",
    "Ga4Events",
    "Ga4IdentityBridge",
    "BraintreeSubscriptions",
    "SailthruNewsletter",
    "PushlySubscribers",
    "OpenwebEngagement",
    "TrackonomicsClicks",
    "TransunionDemographics",
    "FeatureStore",
]
