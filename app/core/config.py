"""Application configuration — loads base.yaml, env overrides, and client overrides."""

from __future__ import annotations

import os
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Nested settings models ────────────────────────────────────────────────────


class ProjectSettings(BaseModel):
    name: str = "audience_intelligence_platform"
    version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"


class DatabaseSettings(BaseModel):
    url: str
    schema: str = "public"  # type: ignore[assignment]  # noqa: E501
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False


class RedisSettings(BaseModel):
    url: str
    ttl_seconds: int = 604800
    max_connections: int = 50


class MLflowSettings(BaseModel):
    tracking_uri: str
    artifact_root: str = "/mlflow/artifacts"
    experiment_name: str = "audience_intelligence"


class APISettings(BaseModel):
    api_keys: list[str]
    admin_api_key: str
    batch_max_size: int = 1000
    rate_limit_per_minute: int = 1000


class SelectionWeightsSettings(BaseModel):
    silhouette: float = 0.40
    interpretability: float = 0.40
    stability: float = 0.20


class ClusteringSettings(BaseModel):
    random_state: int = 42
    k_min: int = 5
    k_max: int = 15
    n_init: int = 3
    silhouette_sample_size: int = 50000
    silhouette_threshold: float = 0.30
    silhouette_alert_delta: float = 0.05
    stability_threshold: float = 0.80
    min_cluster_size_pct: float = 0.005
    selection_weights: SelectionWeightsSettings = SelectionWeightsSettings()


class SubscriptionPropensityWeights(BaseModel):
    newsletter_count_scaled: float = 0.30
    open_rate_scaled: float = 0.25
    days_since_last_visit_scaled_inverted: float = 0.25
    dist_to_subscription_focused_inverted: float = 0.20


class ChurnPropensityWeights(BaseModel):
    days_since_last_visit_scaled: float = 0.40
    bounce_rate_scaled: float = 0.30
    total_billing_cycles_scaled_inverted: float = 0.30


class CommercePropensityWeights(BaseModel):
    ratio_shopping_scaled: float = 0.35
    total_affiliate_clicks_scaled: float = 0.30
    dist_to_high_value_shopper_inverted: float = 0.35


class SubscriptionPropensitySettings(BaseModel):
    weights: SubscriptionPropensityWeights = SubscriptionPropensityWeights()


class ChurnPropensitySettings(BaseModel):
    weights: ChurnPropensityWeights = ChurnPropensityWeights()


class CommercePropensitySettings(BaseModel):
    weights: CommercePropensityWeights = CommercePropensityWeights()


class PropensitySettings(BaseModel):
    subscription: SubscriptionPropensitySettings = SubscriptionPropensitySettings()
    churn: ChurnPropensitySettings = ChurnPropensitySettings()
    commerce: CommercePropensitySettings = CommercePropensitySettings()


class MLFeaturesSettings(BaseModel):
    matrix: list[str]
    log1p_features: list[str]


class MLSettings(BaseModel):
    features: MLFeaturesSettings
    clustering: ClusteringSettings = ClusteringSettings()
    propensity: PropensitySettings = PropensitySettings()


class ColdStartRule(BaseModel):
    condition: str
    persona: str
    priority: int


class ColdStartSettings(BaseModel):
    min_sessions_for_ml: int = 5
    rules: list[ColdStartRule] = []


class NamingRule(BaseModel):
    top_feature: str
    supporting: list[str]
    label: str


class PersonasSettings(BaseModel):
    labels: list[str]
    naming_rules: list[NamingRule]


class EmailEngagementSettings(BaseModel):
    low_threshold: float = 0.15
    high_threshold: float = 0.35


class MonitoringSettings(BaseModel):
    persona_distribution_drift_threshold: float = 0.30
    feature_drift_threshold: float = 0.20
    max_drifting_features: int = 3
    ga4_coverage_alert_threshold: float = 0.90
    transunion_coverage_alert_threshold: float = 0.60
    pipeline_runtime_multiplier: float = 2.0


class ETLSourceSettings(BaseModel):
    mode: str


class ETLSourcesSettings(BaseModel):
    zephr: ETLSourceSettings
    ga4: ETLSourceSettings
    braintree: ETLSourceSettings
    sailthru: ETLSourceSettings
    pushly: ETLSourceSettings
    openweb: ETLSourceSettings
    trackonomics: ETLSourceSettings
    transunion: ETLSourceSettings


class ETLSettings(BaseModel):
    row_count_deviation_threshold: float = 0.20
    transunion_min_confidence: float = 0.70
    new_user_session_threshold: int = 4
    sources: ETLSourcesSettings


class FeatureEngineeringSettings(BaseModel):
    backend: str = "pandas"
    spark_master: str = "local[*]"


# ── Root Settings class ───────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Root settings — loaded from YAML + environment variables.

    Load order (lowest → highest priority):
        1. configs/base.yaml
        2. configs/{APP_ENV}.yaml
        3. configs/clients/{CLIENT_NAME}.yaml
        4. .env file
        5. Process environment variables
    """

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project: ProjectSettings
    database: DatabaseSettings
    redis: RedisSettings
    mlflow: MLflowSettings
    api: APISettings
    ml: MLSettings
    cold_start: ColdStartSettings
    personas: PersonasSettings
    email_engagement: EmailEngagementSettings
    monitoring: MonitoringSettings
    etl: ETLSettings
    feature_engineering: FeatureEngineeringSettings

    @classmethod
    def from_yaml_and_env(cls) -> "Settings":
        """Merge YAML configs, apply explicit env var overrides, then create Settings.

        Environment variables take priority over YAML values.
        Process env vars → .env file → client YAML → env YAML → base YAML (lowest).
        """
        merged = _load_and_merge_yaml()
        _apply_env_overrides(merged)
        return cls(**merged)


# ── YAML loading helpers ──────────────────────────────────────────────────────


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge override into base. Lists are replaced, not appended."""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _apply_env_overrides(merged: dict[str, Any]) -> None:
    """Apply process environment variable overrides into the merged YAML dict.

    Handles DATABASE__SCHEMA and DATABASE__URL so they can be overridden at
    runtime without relying on Pydantic-settings constructor kwargs priority.
    Env var format: SECTION__FIELD maps to merged[section][field].
    """
    delimiter = "__"
    for key, value in os.environ.items():
        if delimiter in key:
            parts = key.lower().split(delimiter, 1)
            if len(parts) == 2 and parts[0] in merged:
                section, field = parts
                if isinstance(merged.get(section), dict):
                    # JSON-parse list/dict values so Pydantic receives the right type
                    import json  # noqa: PLC0415

                    try:
                        parsed = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        parsed = value
                    merged[section][field] = parsed


def _load_and_merge_yaml() -> dict[str, Any]:
    """Load base.yaml, env override, and optional client override.

    Returns:
        Merged config dict, ready to pass as kwargs to Settings().

    Raises:
        FileNotFoundError: If CLIENT_NAME is set but the client config file is missing.
    """
    app_env = os.environ.get("APP_ENV", "development")
    client_name = os.environ.get("CLIENT_NAME")

    with open("configs/base.yaml") as f:
        merged: dict[str, Any] = yaml.safe_load(f)

    env_path = f"configs/{app_env}.yaml"
    if os.path.exists(env_path):
        with open(env_path) as f:
            _deep_merge(merged, yaml.safe_load(f) or {})

    if client_name:
        client_path = f"configs/clients/{client_name}.yaml"
        if not os.path.exists(client_path):
            raise FileNotFoundError(
                f"CLIENT_NAME={client_name!r} set but {client_path} does not exist"
            )
        with open(client_path) as f:
            _deep_merge(merged, yaml.safe_load(f) or {})

    return merged


# ── Module-level singleton ────────────────────────────────────────────────────

settings: Settings = Settings.from_yaml_and_env()
