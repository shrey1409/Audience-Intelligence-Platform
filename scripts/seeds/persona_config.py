"""Persona archetype definitions with feature distributions for synthetic data.

All feature distributions are (mu, sigma) tuples. Generators call
rng.normal(mu, sigma) and clip to valid range. Page category and device
weights are normalized probability vectors for rng.choice().
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.config import settings

# Canonical persona order — used for deterministic array construction.
PERSONA_NAMES: list[str] = [
    "low_engager",
    "casual_reader",
    "sports_focused",
    "celebrity_entertainment",
    "social_engager",
    "occasional_buyer",
    "subscription_focused",
    "loyalist",
    "high_value_shopper",
]

# Valid page category values (must match PageCategory enum in enums.py).
PAGE_CATS: list[str] = [
    "sports",
    "entertainment",
    "celebrity",
    "business",
    "lifestyle",
    "world_news",
    "opinion",
    "shopping",
    "us_news",
    "page_six",
]

# Valid device category values (must match DeviceCategory enum).
DEVICE_CATS: list[str] = ["desktop", "mobile", "tablet"]


@dataclass(frozen=True)
class PersonaArchetype:
    """Feature distribution parameters for one persona.

    All (mu, sigma) pairs are drawn via rng.normal(mu, sigma) then clipped.
    Boolean fields store probability of True (0.0–1.0).
    Dict fields are normalized probability vectors for rng.choice().
    """

    name: str

    # --- Web behaviour ---
    total_sessions_mu: float
    total_sessions_sigma: float
    total_pageviews_mu: float
    total_pageviews_sigma: float
    active_days_mu: float
    active_days_sigma: float
    avg_session_duration_mu: float  # seconds
    avg_session_duration_sigma: float
    bounce_rate_mu: float
    bounce_rate_sigma: float
    days_since_last_visit_mu: float
    days_since_last_visit_sigma: float
    account_age_days_mu: float
    account_age_days_sigma: float
    mobile_ratio_mu: float
    mobile_ratio_sigma: float

    # --- Content affinity (ratio_* features) ---
    page_category_weights: dict[str, float]  # must sum to 1.0, 10 categories

    # --- Subscription ---
    has_subscription_prob: float  # P(True)
    subscription_amount_mu: float
    subscription_amount_sigma: float
    billing_cycle_count_mu: float
    billing_cycle_count_sigma: float

    # --- Email newsletter flags (P(True) per flag) ---
    nl_sports_alerts_prob: float
    nl_morning_report_prob: float
    nl_page_six_daily_prob: float
    nl_celebrity_news_prob: float
    nl_evening_update_prob: float
    nl_post_opinion_prob: float
    nl_breaking_news_prob: float
    nl_real_estate_prob: float
    nl_tech_news_prob: float
    nl_lifestyle_weekly_prob: float
    open_rate_mu: float
    open_rate_sigma: float
    click_through_rate_mu: float
    click_through_rate_sigma: float

    # --- Social engagement ---
    # OpenWeb users only; n_openweb_events drawn from Poisson(lambda_)
    openweb_events_lambda: float
    comments_fraction: float  # fraction of events that are 'comment'
    likes_fraction: float  # fraction that are 'like'
    # shares_fraction = 1 - comments - likes

    # --- Commerce ---
    # Trackonomics users only; n_clicks drawn from Poisson(lambda_)
    trackonomics_clicks_lambda: float
    conversion_prob: float  # P(converted=True) per click
    transaction_amount_mu: float
    transaction_amount_sigma: float

    # --- Demographics (ordinal scores, drawn from weighted choice) ---
    age_score_weights: list[float]  # [P(score=1), ..., P(score=6)]
    income_score_weights: list[float]

    # --- Device weights ---
    device_weights: dict[str, float]  # desktop/mobile/tablet, must sum to 1.0


def _uniform_page_weights() -> dict[str, float]:
    w = 1.0 / len(PAGE_CATS)
    return {c: w for c in PAGE_CATS}


def _page_weights(**overrides: float) -> dict[str, float]:
    """Build a normalized page category weight dict from keyword overrides."""
    base = {c: 0.01 for c in PAGE_CATS}
    base.update(overrides)
    total = sum(base.values())
    return {c: v / total for c, v in base.items()}


def _device(desktop: float, mobile: float, tablet: float = 0.05) -> dict[str, float]:
    total = desktop + mobile + tablet
    return {
        "desktop": desktop / total,
        "mobile": mobile / total,
        "tablet": tablet / total,
    }


PERSONA_ARCHETYPES: dict[str, PersonaArchetype] = {
    "low_engager": PersonaArchetype(
        name="low_engager",
        # Web behaviour — all low; bounce_rate is the primary separator
        total_sessions_mu=3.0,
        total_sessions_sigma=1.2,
        total_pageviews_mu=7.0,
        total_pageviews_sigma=3.0,
        active_days_mu=3.0,
        active_days_sigma=1.0,
        avg_session_duration_mu=30.0,
        avg_session_duration_sigma=15.0,
        bounce_rate_mu=0.82,
        bounce_rate_sigma=0.06,
        days_since_last_visit_mu=180.0,
        days_since_last_visit_sigma=60.0,
        account_age_days_mu=180.0,
        account_age_days_sigma=90.0,
        mobile_ratio_mu=0.45,
        mobile_ratio_sigma=0.12,
        page_category_weights=_uniform_page_weights(),
        # Subscription — very low
        has_subscription_prob=0.02,
        subscription_amount_mu=14.99,
        subscription_amount_sigma=3.0,
        billing_cycle_count_mu=1.5,
        billing_cycle_count_sigma=0.8,
        # Email — very low engagement
        nl_sports_alerts_prob=0.04,
        nl_morning_report_prob=0.04,
        nl_page_six_daily_prob=0.03,
        nl_celebrity_news_prob=0.03,
        nl_evening_update_prob=0.03,
        nl_post_opinion_prob=0.02,
        nl_breaking_news_prob=0.03,
        nl_real_estate_prob=0.02,
        nl_tech_news_prob=0.02,
        nl_lifestyle_weekly_prob=0.02,
        open_rate_mu=0.05,
        open_rate_sigma=0.03,
        click_through_rate_mu=0.01,
        click_through_rate_sigma=0.01,
        # Social — minimal
        openweb_events_lambda=2.0,
        comments_fraction=0.40,
        likes_fraction=0.40,
        # Commerce — minimal
        trackonomics_clicks_lambda=2.0,
        conversion_prob=0.05,
        transaction_amount_mu=25.0,
        transaction_amount_sigma=10.0,
        # Demographics — skew younger/lower income
        age_score_weights=[0.25, 0.25, 0.20, 0.15, 0.10, 0.05],
        income_score_weights=[0.30, 0.30, 0.20, 0.12, 0.05, 0.03],
        device_weights=_device(desktop=0.50, mobile=0.45),
    ),
    "casual_reader": PersonaArchetype(
        name="casual_reader",
        total_sessions_mu=12.0,
        total_sessions_sigma=4.0,
        total_pageviews_mu=45.0,
        total_pageviews_sigma=15.0,
        active_days_mu=12.0,
        active_days_sigma=4.0,
        avg_session_duration_mu=180.0,
        avg_session_duration_sigma=60.0,
        bounce_rate_mu=0.35,
        bounce_rate_sigma=0.10,
        days_since_last_visit_mu=28.0,
        days_since_last_visit_sigma=15.0,
        account_age_days_mu=300.0,
        account_age_days_sigma=150.0,
        mobile_ratio_mu=0.50,
        mobile_ratio_sigma=0.12,
        page_category_weights=_page_weights(
            lifestyle=0.18,
            entertainment=0.16,
            us_news=0.14,
            world_news=0.13,
            business=0.10,
            opinion=0.09,
            sports=0.08,
            celebrity=0.06,
            shopping=0.04,
            page_six=0.02,
        ),
        has_subscription_prob=0.05,
        subscription_amount_mu=14.99,
        subscription_amount_sigma=3.0,
        billing_cycle_count_mu=2.0,
        billing_cycle_count_sigma=1.0,
        nl_sports_alerts_prob=0.10,
        nl_morning_report_prob=0.30,
        nl_page_six_daily_prob=0.08,
        nl_celebrity_news_prob=0.10,
        nl_evening_update_prob=0.12,
        nl_post_opinion_prob=0.08,
        nl_breaking_news_prob=0.10,
        nl_real_estate_prob=0.06,
        nl_tech_news_prob=0.06,
        nl_lifestyle_weekly_prob=0.12,
        open_rate_mu=0.12,
        open_rate_sigma=0.05,
        click_through_rate_mu=0.03,
        click_through_rate_sigma=0.02,
        openweb_events_lambda=3.0,
        comments_fraction=0.30,
        likes_fraction=0.45,
        trackonomics_clicks_lambda=3.0,
        conversion_prob=0.08,
        transaction_amount_mu=30.0,
        transaction_amount_sigma=15.0,
        age_score_weights=[0.15, 0.20, 0.25, 0.20, 0.13, 0.07],
        income_score_weights=[0.15, 0.22, 0.25, 0.20, 0.12, 0.06],
        device_weights=_device(desktop=0.45, mobile=0.50),
    ),
    "sports_focused": PersonaArchetype(
        name="sports_focused",
        total_sessions_mu=20.0,
        total_sessions_sigma=5.0,
        total_pageviews_mu=90.0,
        total_pageviews_sigma=25.0,
        active_days_mu=18.0,
        active_days_sigma=5.0,
        avg_session_duration_mu=240.0,
        avg_session_duration_sigma=80.0,
        bounce_rate_mu=0.28,
        bounce_rate_sigma=0.08,
        days_since_last_visit_mu=5.0,
        days_since_last_visit_sigma=4.0,
        account_age_days_mu=500.0,
        account_age_days_sigma=200.0,
        mobile_ratio_mu=0.55,
        mobile_ratio_sigma=0.10,
        # ratio_sports = ~0.65 is the PRIMARY separator
        page_category_weights=_page_weights(
            sports=0.65,
            business=0.08,
            us_news=0.06,
            entertainment=0.05,
            lifestyle=0.04,
            world_news=0.04,
            opinion=0.03,
            shopping=0.02,
            celebrity=0.02,
            page_six=0.01,
        ),
        has_subscription_prob=0.55,
        subscription_amount_mu=19.99,
        subscription_amount_sigma=5.0,
        billing_cycle_count_mu=6.0,
        billing_cycle_count_sigma=2.0,
        nl_sports_alerts_prob=0.88,
        nl_morning_report_prob=0.40,
        nl_page_six_daily_prob=0.08,
        nl_celebrity_news_prob=0.06,
        nl_evening_update_prob=0.20,
        nl_post_opinion_prob=0.10,
        nl_breaking_news_prob=0.15,
        nl_real_estate_prob=0.05,
        nl_tech_news_prob=0.05,
        nl_lifestyle_weekly_prob=0.08,
        open_rate_mu=0.25,
        open_rate_sigma=0.07,
        click_through_rate_mu=0.08,
        click_through_rate_sigma=0.03,
        openweb_events_lambda=6.0,
        comments_fraction=0.40,
        likes_fraction=0.35,
        trackonomics_clicks_lambda=4.0,
        conversion_prob=0.12,
        transaction_amount_mu=45.0,
        transaction_amount_sigma=20.0,
        age_score_weights=[0.12, 0.28, 0.25, 0.18, 0.12, 0.05],
        income_score_weights=[0.10, 0.18, 0.28, 0.25, 0.13, 0.06],
        device_weights=_device(desktop=0.40, mobile=0.55),
    ),
    "celebrity_entertainment": PersonaArchetype(
        name="celebrity_entertainment",
        total_sessions_mu=18.0,
        total_sessions_sigma=5.0,
        total_pageviews_mu=75.0,
        total_pageviews_sigma=20.0,
        active_days_mu=16.0,
        active_days_sigma=5.0,
        avg_session_duration_mu=200.0,
        avg_session_duration_sigma=70.0,
        bounce_rate_mu=0.30,
        bounce_rate_sigma=0.08,
        days_since_last_visit_mu=8.0,
        days_since_last_visit_sigma=6.0,
        account_age_days_mu=400.0,
        account_age_days_sigma=180.0,
        mobile_ratio_mu=0.60,
        mobile_ratio_sigma=0.10,
        # ratio_celebrity~0.38 + ratio_entertainment~0.25 = ~0.63 PRIMARY separator
        page_category_weights=_page_weights(
            celebrity=0.38,
            entertainment=0.25,
            page_six=0.12,
            lifestyle=0.10,
            us_news=0.05,
            opinion=0.04,
            world_news=0.03,
            sports=0.01,
            business=0.01,
            shopping=0.01,
        ),
        has_subscription_prob=0.10,
        subscription_amount_mu=14.99,
        subscription_amount_sigma=3.0,
        billing_cycle_count_mu=3.0,
        billing_cycle_count_sigma=1.5,
        nl_sports_alerts_prob=0.05,
        nl_morning_report_prob=0.15,
        nl_page_six_daily_prob=0.60,
        nl_celebrity_news_prob=0.80,
        nl_evening_update_prob=0.40,
        nl_post_opinion_prob=0.12,
        nl_breaking_news_prob=0.20,
        nl_real_estate_prob=0.05,
        nl_tech_news_prob=0.04,
        nl_lifestyle_weekly_prob=0.35,
        open_rate_mu=0.18,
        open_rate_sigma=0.06,
        click_through_rate_mu=0.05,
        click_through_rate_sigma=0.02,
        openweb_events_lambda=5.0,
        comments_fraction=0.25,
        likes_fraction=0.45,
        trackonomics_clicks_lambda=3.5,
        conversion_prob=0.10,
        transaction_amount_mu=35.0,
        transaction_amount_sigma=15.0,
        age_score_weights=[0.18, 0.28, 0.22, 0.18, 0.10, 0.04],
        income_score_weights=[0.12, 0.20, 0.28, 0.22, 0.12, 0.06],
        device_weights=_device(desktop=0.35, mobile=0.60),
    ),
    "social_engager": PersonaArchetype(
        name="social_engager",
        total_sessions_mu=22.0,
        total_sessions_sigma=6.0,
        total_pageviews_mu=95.0,
        total_pageviews_sigma=25.0,
        active_days_mu=20.0,
        active_days_sigma=5.0,
        avg_session_duration_mu=280.0,
        avg_session_duration_sigma=90.0,
        bounce_rate_mu=0.20,
        bounce_rate_sigma=0.07,
        days_since_last_visit_mu=4.0,
        days_since_last_visit_sigma=3.0,
        account_age_days_mu=600.0,
        account_age_days_sigma=200.0,
        mobile_ratio_mu=0.55,
        mobile_ratio_sigma=0.10,
        page_category_weights=_page_weights(
            entertainment=0.22,
            opinion=0.20,
            celebrity=0.15,
            sports=0.15,
            world_news=0.10,
            us_news=0.08,
            lifestyle=0.05,
            business=0.03,
            shopping=0.01,
            page_six=0.01,
        ),
        has_subscription_prob=0.15,
        subscription_amount_mu=14.99,
        subscription_amount_sigma=3.0,
        billing_cycle_count_mu=4.0,
        billing_cycle_count_sigma=2.0,
        nl_sports_alerts_prob=0.15,
        nl_morning_report_prob=0.25,
        nl_page_six_daily_prob=0.20,
        nl_celebrity_news_prob=0.30,
        nl_evening_update_prob=0.45,
        nl_post_opinion_prob=0.55,
        nl_breaking_news_prob=0.25,
        nl_real_estate_prob=0.05,
        nl_tech_news_prob=0.10,
        nl_lifestyle_weekly_prob=0.15,
        open_rate_mu=0.20,
        open_rate_sigma=0.06,
        click_through_rate_mu=0.07,
        click_through_rate_sigma=0.03,
        # Social: Poisson(40) events — PRIMARY separator
        openweb_events_lambda=40.0,
        comments_fraction=0.45,
        likes_fraction=0.40,
        trackonomics_clicks_lambda=3.0,
        conversion_prob=0.10,
        transaction_amount_mu=30.0,
        transaction_amount_sigma=15.0,
        age_score_weights=[0.20, 0.28, 0.22, 0.15, 0.10, 0.05],
        income_score_weights=[0.12, 0.22, 0.28, 0.22, 0.12, 0.04],
        device_weights=_device(desktop=0.40, mobile=0.55),
    ),
    "occasional_buyer": PersonaArchetype(
        name="occasional_buyer",
        total_sessions_mu=10.0,
        total_sessions_sigma=4.0,
        total_pageviews_mu=38.0,
        total_pageviews_sigma=15.0,
        active_days_mu=10.0,
        active_days_sigma=4.0,
        avg_session_duration_mu=160.0,
        avg_session_duration_sigma=60.0,
        bounce_rate_mu=0.35,
        bounce_rate_sigma=0.09,
        days_since_last_visit_mu=22.0,
        days_since_last_visit_sigma=12.0,
        account_age_days_mu=350.0,
        account_age_days_sigma=150.0,
        mobile_ratio_mu=0.45,
        mobile_ratio_sigma=0.12,
        # ratio_shopping ~0.35 PRIMARY separator
        page_category_weights=_page_weights(
            shopping=0.35,
            lifestyle=0.20,
            business=0.12,
            entertainment=0.12,
            us_news=0.08,
            world_news=0.05,
            sports=0.03,
            celebrity=0.02,
            opinion=0.02,
            page_six=0.01,
        ),
        has_subscription_prob=0.08,
        subscription_amount_mu=14.99,
        subscription_amount_sigma=3.0,
        billing_cycle_count_mu=2.0,
        billing_cycle_count_sigma=1.0,
        nl_sports_alerts_prob=0.08,
        nl_morning_report_prob=0.15,
        nl_page_six_daily_prob=0.05,
        nl_celebrity_news_prob=0.08,
        nl_evening_update_prob=0.12,
        nl_post_opinion_prob=0.06,
        nl_breaking_news_prob=0.08,
        nl_real_estate_prob=0.12,
        nl_tech_news_prob=0.10,
        nl_lifestyle_weekly_prob=0.20,
        open_rate_mu=0.14,
        open_rate_sigma=0.05,
        click_through_rate_mu=0.04,
        click_through_rate_sigma=0.02,
        openweb_events_lambda=3.0,
        comments_fraction=0.25,
        likes_fraction=0.45,
        trackonomics_clicks_lambda=20.0,
        conversion_prob=0.12,
        transaction_amount_mu=38.0,
        transaction_amount_sigma=18.0,
        age_score_weights=[0.10, 0.22, 0.28, 0.22, 0.12, 0.06],
        income_score_weights=[0.08, 0.18, 0.28, 0.26, 0.14, 0.06],
        device_weights=_device(desktop=0.50, mobile=0.45),
    ),
    "subscription_focused": PersonaArchetype(
        name="subscription_focused",
        total_sessions_mu=16.0,
        total_sessions_sigma=4.0,
        total_pageviews_mu=65.0,
        total_pageviews_sigma=18.0,
        active_days_mu=15.0,
        active_days_sigma=4.0,
        avg_session_duration_mu=220.0,
        avg_session_duration_sigma=70.0,
        bounce_rate_mu=0.22,
        bounce_rate_sigma=0.07,
        days_since_last_visit_mu=6.0,
        days_since_last_visit_sigma=4.0,
        account_age_days_mu=550.0,
        account_age_days_sigma=200.0,
        mobile_ratio_mu=0.40,
        mobile_ratio_sigma=0.10,
        page_category_weights=_page_weights(
            opinion=0.22,
            world_news=0.18,
            business=0.15,
            us_news=0.14,
            entertainment=0.12,
            lifestyle=0.10,
            sports=0.04,
            celebrity=0.02,
            shopping=0.02,
            page_six=0.01,
        ),
        has_subscription_prob=0.72,
        subscription_amount_mu=19.99,
        subscription_amount_sigma=5.0,
        billing_cycle_count_mu=7.0,
        billing_cycle_count_sigma=2.0,
        # newsletter_count ~5 PRIMARY separator (all 6 flags high probability)
        nl_sports_alerts_prob=0.55,
        nl_morning_report_prob=0.80,
        nl_page_six_daily_prob=0.65,
        nl_celebrity_news_prob=0.60,
        nl_evening_update_prob=0.80,
        nl_post_opinion_prob=0.75,
        nl_breaking_news_prob=0.55,
        nl_real_estate_prob=0.35,
        nl_tech_news_prob=0.40,
        nl_lifestyle_weekly_prob=0.60,
        open_rate_mu=0.45,
        open_rate_sigma=0.08,
        click_through_rate_mu=0.22,
        click_through_rate_sigma=0.06,
        openweb_events_lambda=5.0,
        comments_fraction=0.35,
        likes_fraction=0.40,
        trackonomics_clicks_lambda=3.0,
        conversion_prob=0.10,
        transaction_amount_mu=35.0,
        transaction_amount_sigma=15.0,
        age_score_weights=[0.08, 0.18, 0.26, 0.26, 0.16, 0.06],
        income_score_weights=[0.06, 0.14, 0.26, 0.28, 0.18, 0.08],
        device_weights=_device(desktop=0.55, mobile=0.40),
    ),
    "loyalist": PersonaArchetype(
        name="loyalist",
        total_sessions_mu=25.0,
        total_sessions_sigma=6.0,
        total_pageviews_mu=110.0,
        total_pageviews_sigma=30.0,
        active_days_mu=22.0,
        active_days_sigma=5.0,
        avg_session_duration_mu=300.0,
        avg_session_duration_sigma=90.0,
        bounce_rate_mu=0.12,
        bounce_rate_sigma=0.05,
        days_since_last_visit_mu=3.0,
        days_since_last_visit_sigma=2.0,
        account_age_days_mu=900.0,
        account_age_days_sigma=150.0,
        mobile_ratio_mu=0.35,
        mobile_ratio_sigma=0.10,
        page_category_weights=_page_weights(
            world_news=0.20,
            business=0.18,
            opinion=0.15,
            sports=0.13,
            us_news=0.12,
            entertainment=0.08,
            lifestyle=0.07,
            celebrity=0.03,
            shopping=0.02,
            page_six=0.02,
        ),
        # has_subscription=1.0 and billing_cycles~18 are PRIMARY separators
        has_subscription_prob=0.97,
        subscription_amount_mu=24.99,
        subscription_amount_sigma=5.0,
        billing_cycle_count_mu=18.0,
        billing_cycle_count_sigma=4.0,
        nl_sports_alerts_prob=0.50,
        nl_morning_report_prob=0.75,
        nl_page_six_daily_prob=0.40,
        nl_celebrity_news_prob=0.35,
        nl_evening_update_prob=0.65,
        nl_post_opinion_prob=0.60,
        nl_breaking_news_prob=0.45,
        nl_real_estate_prob=0.30,
        nl_tech_news_prob=0.25,
        nl_lifestyle_weekly_prob=0.45,
        open_rate_mu=0.50,
        open_rate_sigma=0.07,
        click_through_rate_mu=0.28,
        click_through_rate_sigma=0.06,
        openweb_events_lambda=8.0,
        comments_fraction=0.38,
        likes_fraction=0.38,
        trackonomics_clicks_lambda=5.0,
        conversion_prob=0.18,
        transaction_amount_mu=55.0,
        transaction_amount_sigma=20.0,
        age_score_weights=[0.03, 0.10, 0.22, 0.30, 0.25, 0.10],
        income_score_weights=[0.04, 0.10, 0.22, 0.30, 0.22, 0.12],
        device_weights=_device(desktop=0.60, mobile=0.35),
    ),
    "high_value_shopper": PersonaArchetype(
        name="high_value_shopper",
        total_sessions_mu=20.0,
        total_sessions_sigma=5.0,
        total_pageviews_mu=80.0,
        total_pageviews_sigma=20.0,
        active_days_mu=18.0,
        active_days_sigma=5.0,
        avg_session_duration_mu=260.0,
        avg_session_duration_sigma=80.0,
        bounce_rate_mu=0.18,
        bounce_rate_sigma=0.06,
        days_since_last_visit_mu=4.0,
        days_since_last_visit_sigma=3.0,
        account_age_days_mu=650.0,
        account_age_days_sigma=200.0,
        mobile_ratio_mu=0.40,
        mobile_ratio_sigma=0.10,
        page_category_weights=_page_weights(
            shopping=0.40,
            business=0.18,
            lifestyle=0.14,
            entertainment=0.10,
            us_news=0.06,
            world_news=0.05,
            opinion=0.03,
            sports=0.02,
            celebrity=0.01,
            page_six=0.01,
        ),
        has_subscription_prob=0.70,
        subscription_amount_mu=19.99,
        subscription_amount_sigma=5.0,
        billing_cycle_count_mu=8.0,
        billing_cycle_count_sigma=3.0,
        nl_sports_alerts_prob=0.10,
        nl_morning_report_prob=0.30,
        nl_page_six_daily_prob=0.08,
        nl_celebrity_news_prob=0.12,
        nl_evening_update_prob=0.25,
        nl_post_opinion_prob=0.12,
        nl_breaking_news_prob=0.15,
        nl_real_estate_prob=0.25,
        nl_tech_news_prob=0.20,
        nl_lifestyle_weekly_prob=0.35,
        open_rate_mu=0.28,
        open_rate_sigma=0.07,
        click_through_rate_mu=0.12,
        click_through_rate_sigma=0.04,
        openweb_events_lambda=4.0,
        comments_fraction=0.20,
        likes_fraction=0.45,
        # Trackonomics: Poisson(50) clicks; conversion~0.40 — PRIMARY separators
        trackonomics_clicks_lambda=50.0,
        conversion_prob=0.40,
        transaction_amount_mu=85.0,
        transaction_amount_sigma=20.0,
        age_score_weights=[0.05, 0.20, 0.28, 0.25, 0.15, 0.07],
        income_score_weights=[0.03, 0.08, 0.18, 0.28, 0.28, 0.15],
        device_weights=_device(desktop=0.55, mobile=0.40),
    ),
}


def normalized_weights(settings_obj: object | None = None) -> dict[str, float]:
    """Return persona weights normalized to exactly 1.0.

    Raw values from configs/base.yaml sum to 1.009 — must normalize before use.

    Args:
        settings_obj: The SyntheticDataSettings instance. Uses module-level settings
            singleton when None.

    Returns:
        Dict mapping persona name → normalized weight.
    """
    src = settings_obj or settings.synthetic_data
    raw: dict[str, float] = src.persona_distribution.model_dump()
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def persona_counts(n_users: int, weights: dict[str, float]) -> dict[str, int]:
    """Compute exact integer user counts per persona summing to n_users.

    Uses round() for all personas, then adjusts the largest group (low_engager)
    to absorb any rounding residual.

    Args:
        n_users: Total number of users.
        weights: Normalized weights dict from normalized_weights().

    Returns:
        Dict mapping persona name → exact integer count.
    """
    counts = {k: round(n_users * v) for k, v in weights.items()}
    residual = n_users - sum(counts.values())
    counts["low_engager"] += residual
    return counts


def build_persona_array(
    rng: np.random.Generator, n_users: int, weights: dict[str, float]
) -> np.ndarray:
    """Build a shuffled array of persona labels with exact counts.

    Args:
        rng: Seeded numpy RNG instance.
        n_users: Total number of users.
        weights: Normalized weights from normalized_weights().

    Returns:
        numpy array of shape (n_users,) with persona label strings.
    """
    counts = persona_counts(n_users, weights)
    labels: list[str] = []
    for name in PERSONA_NAMES:
        labels.extend([name] * counts[name])
    arr = np.array(labels)
    rng.shuffle(arr)
    return arr


def get_archetype(name: str) -> PersonaArchetype:
    """Retrieve a PersonaArchetype by name.

    Args:
        name: Persona label string.

    Returns:
        Corresponding PersonaArchetype instance.

    Raises:
        KeyError: If name is not one of the 9 valid persona labels.
    """
    if name not in PERSONA_ARCHETYPES:
        valid = ", ".join(sorted(PERSONA_ARCHETYPES))
        raise KeyError(f"Unknown persona '{name}'. Valid personas: {valid}")
    return PERSONA_ARCHETYPES[name]
