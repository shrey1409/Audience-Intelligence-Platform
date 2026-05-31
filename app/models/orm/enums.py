"""Python Enum classes for all enumerated column types.

All enums use VARCHAR + CHECK constraint at the DB level (not PostgreSQL ENUM types).
These classes enforce type safety at the application layer only.
"""

from enum import Enum


class DeviceCategory(str, Enum):
    """Device type for GA4 session events. Used by: ga4_events.device_category."""

    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class PageCategory(str, Enum):
    """Content section category. Used by: ga4_events.page_category."""

    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    CELEBRITY = "celebrity"
    BUSINESS = "business"
    LIFESTYLE = "lifestyle"
    WORLD_NEWS = "world_news"
    OPINION = "opinion"
    SHOPPING = "shopping"
    US_NEWS = "us_news"
    PAGE_SIX = "page_six"


class SubscriptionPlan(str, Enum):
    """Braintree subscription plan. Used by: braintree_subscriptions.plan_id."""

    SPORTS_PLUS = "sports_plus"
    HOME_DELIVERY = "home_delivery"
    DIGITAL_ALL_ACCESS = "digital_all_access"


class SubscriptionStatus(str, Enum):
    """Braintree subscription status. Used by: braintree_subscriptions.status."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class PaymentMethod(str, Enum):
    """Payment method. Used by: braintree_subscriptions.payment_method."""

    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"


class EmailEngagementTier(str, Enum):
    """Email engagement tier. Used by: sailthru_newsletter.engagement_tier."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PushPlatform(str, Enum):
    """Push notification platform. Used by: pushly_subscribers.platform."""

    WEB_DESKTOP = "web_desktop"
    WEB_MOBILE = "web_mobile"
    IOS = "ios"
    ANDROID = "android"


class ProductCategory(str, Enum):
    """Affiliate product category. Used by: trackonomics_clicks.product_category."""

    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME = "home"
    BEAUTY = "beauty"
    SPORTS_GEAR = "sports_gear"
    BOOKS = "books"
    TRAVEL = "travel"


class AgeRange(str, Enum):
    """Transunion age range bucket. Used by: transunion_demographics.age_range.

    age_score ordinal encoding: AGE_18_24=1, AGE_25_34=2, ..., AGE_65_PLUS=6.
    """

    AGE_18_24 = "age_18_24"
    AGE_25_34 = "age_25_34"
    AGE_35_44 = "age_35_44"
    AGE_45_54 = "age_45_54"
    AGE_55_64 = "age_55_64"
    AGE_65_PLUS = "age_65_plus"


class Gender(str, Enum):
    """Transunion gender. PII field. Used by: transunion_demographics.gender."""

    M = "m"
    F = "f"
    NON_BINARY = "non_binary"
    UNKNOWN = "unknown"


class IncomeRange(str, Enum):
    """Transunion income range. Used by: transunion_demographics.income_range.

    income_score ordinal encoding: LT_30K=1, GT_150K=6.
    """

    LT_30K = "lt_30k"
    RANGE_30_50K = "range_30_50k"
    RANGE_50_75K = "range_50_75k"
    RANGE_75_100K = "range_75_100k"
    RANGE_100_150K = "range_100_150k"
    GT_150K = "gt_150k"


class HomeOwnership(str, Enum):
    """Transunion home ownership (PII). Used in transunion_demographics."""

    OWNER = "owner"
    RENTER = "renter"
    UNKNOWN = "unknown"


class Education(str, Enum):
    """Transunion education level (PII). Used by: transunion_demographics.education."""

    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"


class AlgorithmUsed(str, Enum):
    """Clustering algorithm used in the run. Used by: feature_store.algorithm_used."""

    KMEANS = "kmeans"
    BISECTING_KMEANS = "bisecting_kmeans"
    GMM = "gmm"
    HDBSCAN = "hdbscan"
    ENSEMBLE = "ensemble"
