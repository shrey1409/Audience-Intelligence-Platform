from __future__ import annotations

from enum import Enum


class DeviceCategory(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class PageCategory(str, Enum):
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
    SPORTS_PLUS = "sports_plus"
    HOME_DELIVERY = "home_delivery"
    DIGITAL_ALL_ACCESS = "digital_all_access"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"


class EmailEngagementTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PushPlatform(str, Enum):
    WEB_DESKTOP = "web_desktop"
    WEB_MOBILE = "web_mobile"
    IOS = "ios"
    ANDROID = "android"


class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME = "home"
    BEAUTY = "beauty"
    SPORTS_GEAR = "sports_gear"
    BOOKS = "books"
    TRAVEL = "travel"


class AgeRange(str, Enum):
    AGE_18_24 = "age_18_24"
    AGE_25_34 = "age_25_34"
    AGE_35_44 = "age_35_44"
    AGE_45_54 = "age_45_54"
    AGE_55_64 = "age_55_64"
    AGE_65_PLUS = "age_65_plus"


class Gender(str, Enum):
    M = "m"
    F = "f"
    NON_BINARY = "non_binary"
    UNKNOWN = "unknown"


class IncomeRange(str, Enum):
    LT_30K = "lt_30k"
    RANGE_30_50K = "range_30_50k"
    RANGE_50_75K = "range_50_75k"
    RANGE_75_100K = "range_75_100k"
    RANGE_100_150K = "range_100_150k"
    GT_150K = "gt_150k"


class HomeOwnership(str, Enum):
    OWNER = "owner"
    RENTER = "renter"
    UNKNOWN = "unknown"


class Education(str, Enum):
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    GRADUATE = "graduate"


class AlgorithmUsed(str, Enum):
    KMEANS = "kmeans"
    BISECTING_KMEANS = "bisecting_kmeans"
    GMM = "gmm"
    HDBSCAN = "hdbscan"
    ENSEMBLE = "ensemble"
