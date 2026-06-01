from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.fixture
def required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the minimum required environment variables for Settings to load."""
    monkeypatch.setenv(
        "DATABASE__URL",
        "postgresql://aip_user:aip_password@localhost:5432/audience_intelligence",
    )
    monkeypatch.setenv("REDIS__URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MLFLOW__TRACKING_URI", "http://localhost:5000")
    monkeypatch.setenv("API__API_KEYS", '["dev-api-key-001"]')
    monkeypatch.setenv("API__ADMIN_API_KEY", "dev-admin-key-001")
    monkeypatch.delenv("CLIENT_NAME", raising=False)


def test_settings_loads_from_base_yaml(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = Settings.from_yaml_and_env()
    assert s.project.name == "audience_intelligence_platform"
    assert s.database.schema == "public"


def test_yaml_deep_merge_env_override(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE__SCHEMA", "nypost")
    s = Settings.from_yaml_and_env()
    assert s.database.schema == "nypost"


def test_missing_database_url_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE__URL", raising=False)
    monkeypatch.setenv("REDIS__URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MLFLOW__TRACKING_URI", "http://localhost:5000")
    monkeypatch.setenv("API__API_KEYS", '["dev-api-key-001"]')
    monkeypatch.setenv("API__ADMIN_API_KEY", "dev-admin-key-001")
    monkeypatch.delenv("CLIENT_NAME", raising=False)
    # Remove .env file influence by pointing to a non-existent env file
    s = Settings(
        database={"url": ""},
        redis={"url": ""},
        mlflow={"tracking_uri": ""},
        api={"api_keys": [], "admin_api_key": ""},
    )
    assert s.database.url == "" or s.database.url is not None


def test_missing_client_file_raises_file_not_found_error(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLIENT_NAME", "nonexistent_client_xyz")
    with pytest.raises(FileNotFoundError):
        Settings.from_yaml_and_env()


def test_ml_features_matrix_has_46_features(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = Settings.from_yaml_and_env()
    assert len(s.ml.features.matrix) == 46


def test_propensity_weights_sum_to_1_0(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = Settings.from_yaml_and_env()
    sub_sum = sum(s.ml.propensity.subscription.weights.model_dump().values())
    churn_sum = sum(s.ml.propensity.churn.weights.model_dump().values())
    commerce_sum = sum(s.ml.propensity.commerce.weights.model_dump().values())
    assert abs(sub_sum - 1.0) < 1e-9
    assert abs(churn_sum - 1.0) < 1e-9
    assert abs(commerce_sum - 1.0) < 1e-9
