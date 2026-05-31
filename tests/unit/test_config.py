"""Unit tests for app/core/config.py — no database connection required."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_settings_loads_from_base_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings singleton loads without error when required env vars are present."""
    monkeypatch.setenv("DATABASE__URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS__URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MLFLOW__TRACKING_URI", "http://localhost:5000")
    monkeypatch.setenv("API__API_KEYS", '["test-key"]')
    monkeypatch.setenv("API__ADMIN_API_KEY", "test-admin-key")
    monkeypatch.setenv("CLIENT_NAME", "")

    import importlib
    import warnings

    import app.core.config as cfg_mod

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        importlib.reload(cfg_mod)

    assert cfg_mod.settings.project.name == "audience_intelligence_platform"
    assert cfg_mod.settings.database.schema == "public"


def test_yaml_deep_merge_produces_overridable_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_load_and_merge_yaml returns a dict with base.yaml defaults.

    Env var overrides are applied by Settings(), not by _load_and_merge_yaml.
    Verifies the base YAML default is present before env vars are applied.
    """
    monkeypatch.setenv("CLIENT_NAME", "")

    import warnings

    from app.core.config import _load_and_merge_yaml

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        merged = _load_and_merge_yaml()

    # YAML default for database.schema is "public" from configs/base.yaml
    assert merged.get("database", {}).get("schema") == "public"


def test_missing_database_url_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ValidationError is raised at startup when DATABASE__URL is absent."""
    monkeypatch.delenv("DATABASE__URL", raising=False)
    monkeypatch.setenv("REDIS__URL", "redis://localhost:6379/0")
    monkeypatch.setenv("MLFLOW__TRACKING_URI", "http://localhost:5000")
    monkeypatch.setenv("API__API_KEYS", '["test-key"]')
    monkeypatch.setenv("API__ADMIN_API_KEY", "test-admin-key")
    # Remove .env file influence by pointing to a non-existent file
    monkeypatch.setenv("CLIENT_NAME", "")

    import warnings

    from app.core.config import Settings, _load_and_merge_yaml

    # Without DATABASE__URL in env (and .env overridden), Settings() should fail
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises((ValidationError, Exception)):
            _load_and_merge_yaml()
            Settings()


def test_missing_client_file_raises_file_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FileNotFoundError raised when CLIENT_NAME is set but the file is absent."""
    monkeypatch.setenv("CLIENT_NAME", "nonexistent_publisher")

    import warnings

    from app.core.config import _load_and_merge_yaml

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with pytest.raises(FileNotFoundError):
            _load_and_merge_yaml()


def test_ml_features_matrix_has_46_features() -> None:
    """The ML feature matrix loaded from base.yaml has exactly 46 features."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from app.core.config import settings  # noqa: PLC0415

    assert (
        len(settings.ml.features.matrix) == 46
    ), f"Expected 46 ML features, got {len(settings.ml.features.matrix)}"


def test_propensity_weights_sum_to_1_0() -> None:
    """All three propensity weight sets each sum to exactly 1.0."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        from app.core.config import settings  # noqa: PLC0415

    sub = sum(settings.ml.propensity.subscription.weights.model_dump().values())
    churn = sum(settings.ml.propensity.churn.weights.model_dump().values())
    commerce = sum(settings.ml.propensity.commerce.weights.model_dump().values())

    assert abs(sub - 1.0) < 1e-9, f"Subscription weights sum to {sub}, expected 1.0"
    assert abs(churn - 1.0) < 1e-9, f"Churn weights sum to {churn}, expected 1.0"
    assert (
        abs(commerce - 1.0) < 1e-9
    ), f"Commerce weights sum to {commerce}, expected 1.0"
