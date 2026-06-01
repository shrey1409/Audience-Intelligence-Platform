# Infrastructure Context — Audience Intelligence Platform

## Docker Services (docker-compose.yml)

| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | Primary database (PostgreSQL 14) |
| redis | 6379 | Feature cache + persona cache |
| adminer | 8080 | DB admin UI (dev only) |
| api | 8000 | FastAPI application server |
| worker | — | Celery/Airflow task worker (no exposed port) |
| jupyter | 8888 | Notebooks for EDA/exploration (dev only) |
| minio | 9000 | S3-compatible object storage (model artifacts) |

## Database Setup

**Databases:**
- `audience_intelligence_dev` — Development (default)
- `audience_intelligence_staging` — Staging
- `audience_intelligence_prod` — Production

**Schema Pattern:** Dynamic from `settings.database.schema`
- Config: `configs/base.yaml` → `database.schema: "public"` (dev)
- Clients: `configs/clients/{client}.yaml` → `database.schema: "{client}_schema"`
- Migration: Alembic auto-applies schema via settings override

**Connection Pool:** SQLAlchemy AsyncEngine
- pool_size: 20
- max_overflow: 10
- Timeout: 30s connection acquire

## Alembic Migrations

**Pattern:** Never hardcode schema in migration files
```python
from app.core.config import settings
context.configure(..., target_metadata=Base.metadata)
```

**On Conflict Handling:** Hand-edit if auto-detect misses UNIQUE constraints on composite keys

## Environment Variables (Required)

- **DATABASE_URL:** postgresql+asyncpg://user:pass@postgres:5432/audience_intelligence_dev
- **REDIS_URL:** redis://redis:6379/0
- **MINIO_ENDPOINT:** minio:9000
- **MINIO_ACCESS_KEY:** minioadmin
- **MINIO_SECRET_KEY:** minioadmin
- **API_KEY_SECRET:** (generate with `openssl rand -hex 32`)
- **LOG_LEVEL:** DEBUG|INFO|WARNING (default: INFO)
- **SCHEMA:** "public" (default, override per client)

## CI/CD Pipeline (GitHub Actions, Phase 10)

**Pre-commit Checks:**
1. Black formatting (auto-fix)
2. isort imports (auto-fix)
3. flake8 linting
4. mypy type checking (strict)

**Build & Test:**
1. Spin up postgres + redis in Docker
2. Run migrations: `alembic upgrade head`
3. pytest all tests (unit + integration)
4. Generate coverage report

**Pre-Merge Gate:**
- All tests pass ✅
- Coverage >85% for new code
- No new linting errors
- Commit message follows conventional format

## Useful Debugging Commands

```bash
# Check container health
docker compose ps

# View logs for API
docker compose logs api -f

# Fresh start (WARNING: deletes all data)
docker compose down -v && docker compose up -d

# Reset one migration
alembic downgrade -1 && alembic upgrade head

# Test with subprocess isolation (avoids schema reload issue)
pytest tests/integration/test_schema_isolation.py -v
```
