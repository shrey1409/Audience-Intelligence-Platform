from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Pydantic v2 warns when a field name shadows a BaseModel class attribute.
# "schema" is valid in v2 — model_json_schema() replaced schema().
warnings.filterwarnings(
    "ignore",
    message=r'Field name "schema" in "DatabaseSettings" shadows an attribute',
    category=UserWarning,
)

# ---------------------------------------------------------------------------
# Nested config models — populated from configs/base.yaml
# ---------------------------------------------------------------------------


class ProjectSettings(BaseModel):
    name: str = "audience_intelligence_platform"
    version: str = "0.1.0"
    environment: str = "development"


class DatabaseSettings(BaseModel):
    url: str = ""
    schema: str = "public"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False

    model_config = ConfigDict(protected_namespaces=())


class RedisSettings(BaseModel):
    url: str = ""
    ttl_seconds: int = 604800
    max_connections: int = 50


class MLFlowSettings(BaseModel):
    tracking_uri: str = ""


class APISettings(BaseModel):
    api_keys: list[str] = Field(default_factory=list)
    admin_api_key: str = ""
    batch_max_size: int = 1000
    rate_limit_per_minute: int = 1000


class MLFeaturesSettings(BaseModel):
    matrix: list[str] = Field(default_factory=list)
    log1p_features: list[str] = Field(default_factory=list)


class ClusteringSelectionWeights(BaseModel):
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
    selection_weights: ClusteringSelectionWeights = Field(
        default_factory=ClusteringSelectionWeights
    )


class SubscriptionPropensityWeights(BaseModel):
    newsletter_count_scaled: float = 0.30
    open_rate_scaled: float = 0.25
    days_since_last_visit_scaled_inverted: float = 0.25
    dist_to_subscription_focused_inverted: float = 0.20


class SubscriptionPropensitySettings(BaseModel):
    weights: SubscriptionPropensityWeights = Field(
        default_factory=SubscriptionPropensityWeights
    )


class ChurnPropensityWeights(BaseModel):
    days_since_last_visit_scaled: float = 0.40
    bounce_rate_scaled: float = 0.30
    total_billing_cycles_scaled_inverted: float = 0.30


class ChurnPropensitySettings(BaseModel):
    weights: ChurnPropensityWeights = Field(default_factory=ChurnPropensityWeights)


class CommercePropensityWeights(BaseModel):
    ratio_shopping_scaled: float = 0.35
    total_affiliate_clicks_scaled: float = 0.30
    dist_to_high_value_shopper_inverted: float = 0.35


class CommercePropensitySettings(BaseModel):
    weights: CommercePropensityWeights = Field(
        default_factory=CommercePropensityWeights
    )


class PropensitySettings(BaseModel):
    subscription: SubscriptionPropensitySettings = Field(
        default_factory=SubscriptionPropensitySettings
    )
    churn: ChurnPropensitySettings = Field(default_factory=ChurnPropensitySettings)
    commerce: CommercePropensitySettings = Field(
        default_factory=CommercePropensitySettings
    )


class MLSettings(BaseModel):
    features: MLFeaturesSettings = Field(default_factory=MLFeaturesSettings)
    clustering: ClusteringSettings = Field(default_factory=ClusteringSettings)
    propensity: PropensitySettings = Field(default_factory=PropensitySettings)


class ColdStartRule(BaseModel):
    condition: str
    persona: str
    priority: int


class ColdStartSettings(BaseModel):
    min_sessions_for_ml: int = 5
    rules: list[ColdStartRule] = Field(default_factory=list)


class PersonaNamingRule(BaseModel):
    top_feature: str
    supporting: list[str] = Field(default_factory=list)
    label: str


class PersonasSettings(BaseModel):
    labels: list[str] = Field(default_factory=list)
    naming_rules: list[PersonaNamingRule] = Field(default_factory=list)


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
    mode: str = "incremental"


class ETLSourcesSettings(BaseModel):
    zephr: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    ga4: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    braintree: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    sailthru: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    pushly: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    openweb: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    trackonomics: ETLSourceSettings = Field(default_factory=ETLSourceSettings)
    transunion: ETLSourceSettings = Field(default_factory=ETLSourceSettings)


class ETLSettings(BaseModel):
    row_count_deviation_threshold: float = 0.20
    transunion_min_confidence: float = 0.70
    new_user_session_threshold: int = 4
    sources: ETLSourcesSettings = Field(default_factory=ETLSourcesSettings)


class FeatureEngineeringSettings(BaseModel):
    backend: str = "pandas"
    spark_master: str = "local[*]"


class PersonaDistributionSettings(BaseModel):
    low_engager: float = 0.506
    casual_reader: float = 0.154
    sports_focused: float = 0.101
    celebrity_entertainment: float = 0.097
    social_engager: float = 0.077
    occasional_buyer: float = 0.029
    subscription_focused: float = 0.028
    loyalist: float = 0.011
    high_value_shopper: float = 0.006


class SourceCoverageSettings(BaseModel):
    ga4: float = 0.95
    braintree: float = 0.10
    sailthru: float = 1.00
    pushly: float = 0.35
    openweb: float = 0.23
    trackonomics: float = 0.16
    transunion: float = 0.70


class SyntheticDataSettings(BaseModel):
    n_users: int = 100000
    random_seed: int = 42
    batch_size: int = 5000
    ga4_events_per_user_mean: int = 150
    ga4_events_per_user_std: int = 50
    transunion_high_confidence_ratio: float = 0.85
    persona_distribution: PersonaDistributionSettings = Field(
        default_factory=PersonaDistributionSettings
    )
    source_coverage: SourceCoverageSettings = Field(
        default_factory=SourceCoverageSettings
    )


# ---------------------------------------------------------------------------
# Custom YAML settings source for pydantic-settings v2
# ---------------------------------------------------------------------------


class _YamlSettingsSource(PydanticBaseSettingsSource):
    """Loads settings from a YAML file, optionally deep-merged with a client YAML."""

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        yaml_path: str,
        client_yaml_path: str | None = None,
    ) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] = {}

        base_path = Path(yaml_path)
        if base_path.exists():
            with open(base_path) as f:
                self._data = yaml.safe_load(f) or {}

        if client_yaml_path is not None:
            client_path = Path(client_yaml_path)
            if not client_path.exists():
                raise FileNotFoundError(f"Client config not found: {client_yaml_path}")
            with open(client_path) as f:
                client_data = yaml.safe_load(f) or {}
            self._data = _deep_merge(self._data, client_data)

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        if field_name in self._data:
            return self._data[field_name], field_name, False
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        return self._data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, override wins on conflicts."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ---------------------------------------------------------------------------
# Top-level Settings class
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project: ProjectSettings = Field(default_factory=ProjectSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    mlflow: MLFlowSettings = Field(default_factory=MLFlowSettings)
    api: APISettings = Field(default_factory=APISettings)
    ml: MLSettings = Field(default_factory=MLSettings)
    cold_start: ColdStartSettings = Field(default_factory=ColdStartSettings)
    personas: PersonasSettings = Field(default_factory=PersonasSettings)
    email_engagement: EmailEngagementSettings = Field(
        default_factory=EmailEngagementSettings
    )
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    etl: ETLSettings = Field(default_factory=ETLSettings)
    feature_engineering: FeatureEngineeringSettings = Field(
        default_factory=FeatureEngineeringSettings
    )
    synthetic_data: SyntheticDataSettings = Field(default_factory=SyntheticDataSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Priority: env vars > dotenv > init kwargs > yaml defaults
        return (env_settings, dotenv_settings, init_settings, file_secret_settings)

    @classmethod
    def from_yaml_and_env(
        cls,
        yaml_path: str = "configs/base.yaml",
    ) -> "Settings":
        """Load settings from YAML file merged with environment variables.

        Args:
            yaml_path: Path to the base YAML config file.

        Returns:
            Fully configured Settings instance.

        Raises:
            FileNotFoundError: If CLIENT_NAME env var is set but client config missing.
            ValidationError: If required env vars (DATABASE__URL, etc.) are absent.
        """
        client_name = os.environ.get("CLIENT_NAME", "").strip()
        client_yaml_path: str | None = None
        if client_name:
            client_yaml_path = f"configs/clients/{client_name}.yaml"

        yaml_source = _YamlSettingsSource(cls, yaml_path, client_yaml_path)
        yaml_data = yaml_source()

        return cls(**yaml_data)


# ---------------------------------------------------------------------------
# Module-level singleton — imported by ORM models at class definition time
# ---------------------------------------------------------------------------

settings: Settings = Settings.from_yaml_and_env()
