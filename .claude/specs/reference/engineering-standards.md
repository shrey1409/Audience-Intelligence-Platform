# Engineering Standards Reference

## Python Standards

### Type Hints & Code Style
- **Type hints on every function:** No exceptions. Includes return types.
- **No `Any` types** — use proper generics or Union
- **No `# type: ignore` without explanation** — comment must explain the specific type system reason
- **Black (line-length=88) + isort (profile=black) + flake8 + mypy (strict)**
- **No bare `except:`** — always catch specific exceptions

### Structural Logging
- **structlog 24.1** for all logging — no bare `print()` in production code
- **Every function entry and exit logged** to a configured logger
- **No log level CRITICAL** — use ERROR or lower
- Example:
  ```python
  logger = structlog.get_logger(__name__)
  logger.info("event", user_count=1000, algorithm="kmeans")
  ```

### Configuration
- **Zero hardcoded parameters** — all config values read from `configs/base.yaml` via `settings` object
- All numbers/strings/thresholds/weights/thresholds from config, never hardcoded
- CI check: grep fails build if hardcoded values found matching known configurable patterns

### Testing
- **Unit tests must not require live services** — mock all DB, Redis, external APIs
- **Integration tests run against Docker Compose** — real Postgres, Redis, etc.
- **Coverage target: ≥ 80%** on ETL, feature engineering, and API code
- **Faker for synthetic test data** — no hardcoded test values
- **Fixture-based test setup** — reusable, DRY, minimal per-test setup

### SQLAlchemy 2.0 Style (Async)
- **Use `select()` constructor** — no legacy `Query.filter()`
- **Use `Session.scalars()`** — not `Session.query()`
- **All ORM models have `__table_args__`** with schema parameter: `__table_args__ = {"schema": settings.database.schema}`
- **Foreign keys as class attributes** — SQLAlchemy relationships managed declaratively
- **No direct SQL outside service layer** — all DB operations through ORM or raw select() with proper escaping

---

## SQL Standards

### DDL (Data Definition Language)

**Every SQL file must use `{schema}` placeholder** — never hardcode schema name.

```sql
-- CORRECT
CREATE TABLE {schema}.user_profiles (
  user_id UUID PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- WRONG
CREATE TABLE public.user_profiles (...)  -- hardcoded schema
```

### Query Style
- **Never use `SELECT *`** — always name columns explicitly
- **Always escape identifiers** — use Postgres double-quotes for reserved words
- **Use parameterized queries** — never string interpolation for user input
- **Transactions for multi-step operations** — ensure atomicity
- **EXPLAIN ANALYZE for queries touching > 100K rows** — verify index usage

### Indexes
- **Primary keys on all tables** (usually `user_id` or `(user_id, updated_at)`)
- **Indexes on foreign keys** — enables fast joins
- **Indexes on frequently-filtered columns** (e.g., `is_new_user`, `algorithm_used`)
- **No indexes on low-cardinality columns** — waste of space

### Constraints
- **UNIQUE constraints on natural keys** — enables `ON CONFLICT` upserts
- **NOT NULL on required columns** — explicit about data expectations
- **FOREIGN KEY constraints** with `ON DELETE CASCADE` for dependent tables
- **CHECK constraints for enum-like columns** — enforce valid values at DB layer

---

## API Standards (FastAPI)

### Endpoint Structure
- **Never return raw ORM objects** — always use Pydantic schemas
- **Every endpoint has error handling** — 404, 422, 500 with descriptive messages
- **Input validation via Pydantic v2** — automatic on request body
- **HTTP status codes follow REST conventions** — 200, 201, 400, 401, 404, 500
- **API versioning in URL path** — `/api/v1/` prefix (mandatory)

### Performance
- **Redis cache checked before database on every read** (except inserts/updates)
- **Batch endpoints use Redis pipeline** — single round-trip for multiple keys
- **Response time targets:** p99 < 10 ms (single), p99 < 100 ms (batch 1,000)
- **Load testing in CI** — locust 10,000 req/sec for 60s

### Authentication & Security
- **All endpoints require `X-API-Key` header** — validated via middleware
- **Admin endpoints require admin-tier API keys** — separate from client keys
- **API keys rotated quarterly** — tracked in environment/secrets management
- **No PII in API responses** — automated scanning in CI
- **No `hashed_email` exposed in any response** — it's a private identifier

### Response Schema (Persona Endpoint)

```python
class PersonaResponse(BaseModel):
    persona_label: str  # One of 9 labels or cold-start label
    cluster_id: int  # Integer cluster assignment
    propensity_scores: dict  # {subscription, churn, commerce: float}
    soft_scores: Optional[list[float]]  # 9 elements or null
    algorithm_used: str  # {kmeans, bisecting_kmeans, gmm, hdbscan, ensemble}
    last_updated: datetime  # ISO 8601
    is_cold_start: bool
```

---

## ML Pipeline Standards

### Algorithm Implementation
- **`random_state=42` on every stochastic algorithm** — configurable in base.yaml
- **Each algorithm module in `ml/training/algorithms/`** — one file per algorithm
- **Common interface:** `fit(X: np.ndarray, k: int) → ClusterResult`
- **ClusterResult contains:** labels, centroids (or means), score, metadata

### Scaler Management
- **Fit once on training data, never refit on inference data** — critical invariant
- **Scaler persisted as MLflow artifact** (`scaler.pkl`) with every run
- **Inference loads scaler from MLflow** — using the same run_id or model registry
- **Any re-fit of scaler on new data is a bug** — triggers alert

### MLflow Integration
- **Every run logs:** algorithm, K, silhouette score, per-cluster scores, persona distribution, feature importance
- **Artifacts:** scaler.pkl, feature_importance.json, inertia_curve.json, persona_distribution.json
- **Run tags:** trigger_source, rationale, stage (discovery/evaluation/production)
- **Model registry:** retain last 4 runs for rollback

### Feature Engineering
- **log1p() on right-skewed features** before StandardScaler (F-07)
- **Features requiring log1p:** total_sessions, total_pageviews, total_affiliate_clicks, total_comments
- **All numeric features scaled to zero mean, unit variance** via StandardScaler
- **Null values imputed with 0** for optional sources (F-08)
- **46-feature matrix finalized** before scaler fit

### Reproducibility Requirement
- **Same input data + same config + same random_state → identical output**
- **HDBSCAN is exception** — inherently non-deterministic; validate by checking cluster count agreement within ±1 across 3 seeds
- **No hardcoded seeds anywhere** — all from config

---

## Git Standards

### Branch Naming
- **Feature branches:** `feature/phaseN-short-description` (e.g., `feature/phase03-etl-ingestion`)
- **Bug fixes:** `fix/short-description`
- **Chore/non-feature:** `chore/short-description`
- **Always branch from `main`**
- **Always PR back to `main`**

### Commit Messages
- **Conventional commit format:** `<type>: <description>`
- **Types:** `feat`, `fix`, `chore`, `refactor`, `test`, `docs`
- **Description:** imperative mood, lowercase, ≤ 50 characters
- **Example:** `feat: add subscription propensity score calculation`
- **No merge commits on main** — use squash for feature PRs

### Code Review
- **Every PR requires ≥ 1 approval** before merge
- **All CI checks must pass** — tests, linting, type checking, coverage
- **No TODO comments in merged code** — resolve before committing
- **No placeholder code or pseudo-code in merged code**

---

## CI/CD Standards

### Pre-Commit Checks
- **Black formatting** — auto-fix
- **isort import sorting** — auto-fix
- **flake8 linting** — fails build on violations
- **mypy type checking (strict mode)** — fails build on type errors
- **No hardcoded values check** — grep patterns for configurable numbers
- **No secrets scan** — detects API keys, passwords, PII patterns

### Test Requirements
- **All new Python files pass `python3 -m py_compile`**
- **All tests pass:** `pytest tests/ -v`
- **Coverage ≥ 80%** on ETL, feature engineering, API — fails build if below
- **Integration tests pass** on Docker Compose services
- **Load test passes** in CI — 10,000 req/sec for 60s on API endpoints

### Deployment Gating
- **No hardcoded values in any module** (except config loading)
- **configs/base.yaml validates as valid YAML** — `python3 -c "import yaml; yaml.safe_load(...)"`
- **No PII in any committed file** — CI scanner blocks commits
- **All phase deliverables present** — no missing files referenced in CLAUDE.md phase tracker

---

## Database Connection Standards

### Connection Pooling
- **SQLAlchemy AsyncEngine with connection pool** — default pool size 20, max overflow 10
- **Configurable via `configs/base.yaml`** as `database.pool_size` and `database.max_overflow`
- **Connection timeout 30s** — configurable as `database.timeout_seconds`

### Schema Isolation (Multi-Tenancy)
- **Every ORM model has `__table_args__ = {"schema": settings.database.schema}`**
- **CI integration test verifies:** client_a session cannot read/write client_b schema
- **Schema name from `configs/clients/{client}.yaml`** under `database.schema` key
- **Development default schema:** `"public"` (in `configs/base.yaml`)

---

## Documentation Standards

### Docstrings
- **Google-style docstrings on all public functions**
- **One-line summary, blank line, longer description if needed**
- **Args, Returns, Raises sections for public functions**
- **Example:**
  ```python
  def compute_silhouette(X: np.ndarray, labels: np.ndarray) -> float:
      """Compute silhouette score for clustered data.

      Args:
          X: Feature matrix (n_samples, n_features)
          labels: Cluster assignments (n_samples,)

      Returns:
          Silhouette score between -1.0 and 1.0
      """
  ```

### Inline Comments
- **Only for non-obvious WHY, not WHAT**
- **If the code is clear, no comment needed**
- **Comments should explain hidden constraints or workarounds**
- **Example:**
  ```python
  # Scaler must never be refit on inference data — caches must use
  # the same scaler fitted on training data to preserve centroid positions
  scaler = mlflow.sklearn.load_model(...)
  ```

### Code Comments to AVOID
- `# removed by F-XX` — doesn't belong in code; belongs in PR description
- `# used by X flow` — rots as code evolves
- Restating what the code does — let the identifier names do that
- `# TODO`, `# FIXME` — must be resolved before commit (no TODOs in merged code)
