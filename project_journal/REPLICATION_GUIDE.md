# Replication Guide — Rebuild the Project From Scratch

**Document Type:** Step-by-Step Reconstruction Guide
**Created:** 2026-05-31
**Last Updated:** 2026-05-31

This guide enables anyone to reconstruct the Audience Intelligence Platform from scratch, even without access to the existing repository or Claude Code. Every step is explicit with the exact commands to run.

---

## Prerequisites

### Hardware
- macOS 13+ or Ubuntu 22.04+
- 8GB RAM minimum (16GB recommended for all Docker services)
- 20GB free disk space

### Software Requirements
```bash
# Required:
python3 --version   # Must be 3.11+
git --version       # Any recent version
docker --version    # Docker Desktop or Docker Engine 24+
docker compose version  # Compose v2 (bundled with Docker Desktop)

# Recommended:
code --version      # VS Code with Claude Code extension
# OR
claude --version    # Claude Code CLI
```

---

## Phase 0 — Repository and Environment Setup

### 0.1 Create Repository
```bash
# Create on GitHub: https://github.com/new
# Repository name: Audience-Intelligence-Platform
# Private, no README (we add our own)

git clone https://github.com/YOUR_USERNAME/Audience-Intelligence-Platform.git
cd "Audience-Intelligence-Platform"
```

### 0.2 Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# OR: venv\Scripts\activate  # Windows

pip install --upgrade pip
```

### 0.3 Create the Folder Structure
```bash
mkdir -p app/{core,models/orm,schemas,api/v1/endpoints,services,utils}
mkdir -p etl/{ingestion,transforms,identity}
mkdir -p ml/{feature_store,training/{algorithms,evaluation},inference,pipelines,experiments}
mkdir -p sql/{ddl,analytics}
mkdir -p dags configs/clients tests/{unit,integration}
mkdir -p scripts docker/postgres/init requirements .claude/{commands,specs}
mkdir -p project_journal/{specifications,milestones,decisions,session_logs}

# Create __init__.py files
find app etl ml tests -type d | xargs -I{} touch {}/__init__.py
touch scripts/.gitkeep sql/ddl/.gitkeep sql/analytics/.gitkeep docker/.gitkeep dags/.gitkeep
```

### 0.4 Create .gitignore
```bash
cat > .gitignore << 'EOF'
# Python
venv/
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Environment and secrets
.env
configs/clients/*.yaml
!configs/clients/example.yaml

# Data
data/
*.csv
*.parquet

# ML artifacts
mlruns/
artifacts/

# IDE
.vscode/
.idea/
*.swp

# Jupyter
.ipynb_checkpoints/
EOF
```

### 0.5 Create pyproject.toml
```toml
[project]
name = "audience-intelligence-platform"
version = "0.1.0"
description = "ML-powered audience segmentation platform for digital publishers"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=app --cov=etl --cov=ml --cov-report=term-missing"
asyncio_mode = "auto"
```

### 0.6 Create requirements/base.txt
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
redis==5.0.4
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.4.2
xgboost==2.0.3
lightgbm==4.3.0
hdbscan==0.8.33
optuna==3.6.1
mlflow==2.13.0
pydantic==2.7.1
pydantic-settings==2.2.1
pyyaml==6.0.1
structlog==24.1.0
httpx==0.27.0
python-dotenv==1.0.1
tenacity==8.3.0
```

### 0.7 Create configs/base.yaml
This is the most important file — the canonical configuration. Copy from `.claude/specs/master-specification.md` Section 2 or from the actual `configs/base.yaml` in the repository. Key sections:
- `database:` — schema, pool settings
- `redis:` — ttl_seconds: 604800, max_connections: 50
- `ml.features.matrix:` — 46 feature names (this list is immutable per spec)
- `ml.clustering:` — random_state: 42, k_min: 5, k_max: 15
- `ml.propensity:` — subscription/churn/commerce weights (each sum to 1.0)
- `cold_start.rules:` — 5 rules in priority order
- `personas.labels:` — 9 persona label strings
- `etl.sources:` — 8 source systems with modes

### 0.8 Install Dependencies and Pre-commit
```bash
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
pre-commit install
```

---

## Phase 1 — Core Application Layer

### 1.1 app/core/config.py

Critical pattern: Settings class uses Pydantic-settings with YAML deep-merge loader.

```python
# The loading sequence (lowest → highest priority):
# 1. configs/base.yaml
# 2. configs/{APP_ENV}.yaml
# 3. configs/clients/{CLIENT_NAME}.yaml
# 4. _apply_env_overrides() injects process env vars into merged dict
# 5. Pydantic-settings reads .env file for any remaining required fields

# Required env vars (ValidationError at startup if missing):
# DATABASE__URL, REDIS__URL, MLFLOW__TRACKING_URI, API__API_KEYS, API__ADMIN_API_KEY
```

See `.claude/specs/system_design-spec.md` Section 2 for the complete class hierarchy.

**Critical bug to avoid**: Do NOT set `DATABASE__SCHEMA` in `.env`. Set it only in `configs/base.yaml` (default: `"public"`) or as a process env var. If `.env` sets it, it wins over subprocess env var overrides.

### 1.2 app/core/database.py

```python
# Two engines, same PostgreSQL server:
async_engine = create_async_engine(postgresql+asyncpg://...)  # FastAPI only
sync_engine = create_engine(postgresql://...)                  # ETL + ML + Alembic

# DSN conversion helper needed:
def _async_dsn(sync_dsn: str) -> str:
    return sync_dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
```

### 1.3 app/models/orm/base.py
```python
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

### 1.4 ORM Models — All 10 Tables

**Invariants for every model:**
- `__table_args__ = {"schema": settings.database.schema}` — dynamic, not hardcoded
- UUID PKs: `default=uuid.uuid4` (Python-side, not `server_default=text("gen_random_uuid()")`)
- Timestamp columns: `DateTime` (not `Timestamp` — that's not a valid SQLAlchemy type)
- DECIMAL columns: `Numeric(precision, scale)` with `default=Decimal("0")` — never `Float`
- FK columns: `ForeignKey(f"{settings.database.schema}.zephr_users.user_id", ondelete="CASCADE")`
- `from decimal import Decimal` required in any model with Numeric columns
- `from datetime import date, datetime` — use `date` not `datetime.date`

See `.claude/specs/database-schema-spec.md` Section 4 for every column of every model.

---

## Phase 2 — Alembic Migrations

### 2.1 alembic.ini
```ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
# NO sqlalchemy.url here — injected at runtime by env.py
```

### 2.2 alembic/env.py
The env.py must be **schema-aware**:
```python
_schema = settings.database.schema  # read at migration load time

def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return object.schema == _schema
    return True

# In run_migrations_online():
context.configure(
    version_table="alembic_version",
    version_table_schema=_schema,  # critical — Alembic history in correct schema
    include_schemas=True,
    include_object=include_object,
)
```

### 2.3 scripts/run_migrations.py
```python
# Creates schema if absent, then runs alembic upgrade head
engine = create_engine(settings.database.url)
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.database.schema}"))
    conn.commit()
engine.dispose()
Config("alembic.ini") → command.upgrade(cfg, "head")
```

### 2.4 Generate and Fix Initial Migration

```bash
PYTHONPATH=. python3 -W ignore::UserWarning -m alembic revision --autogenerate -m "initial_schema"
```

**Critical post-generation fix**: The autogenerated migration will have `schema="public"` hardcoded. Replace with `schema=_schema` where `_schema` is loaded from `settings.database.schema` at migration load time. See `alembic/versions/20260531_d65666c751dc_initial_schema.py` for the pattern.

---

## Phase 3 — Docker Infrastructure

### docker-compose.yml (Phase 2 — postgres + redis only)
```yaml
services:
  postgres:
    image: postgres:15
    container_name: aip_postgres
    environment:
      POSTGRES_USER: aip_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: audience_intelligence
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aip_user -d audience_intelligence"]
      interval: 10s
      timeout: 5s
      retries: 5
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

### docker/postgres/init/01_create_databases.sql
```sql
CREATE DATABASE mlflow OWNER aip_user;
CREATE DATABASE airflow OWNER aip_user;
```

### .env (create from .env.example, never commit)
```bash
DATABASE__URL=postgresql://aip_user:changeme@localhost:5432/audience_intelligence
REDIS__URL=redis://localhost:6379/0
MLFLOW__TRACKING_URI=http://localhost:5000
API__API_KEYS=["dev-api-key-001"]
API__ADMIN_API_KEY=dev-admin-key-001
POSTGRES_PASSWORD=changeme
APP_ENV=development
```

---

## Verification Checklist After Setup

```bash
# 1. asyncpg importable
python3 -c "import asyncpg; print(asyncpg.__version__)"
# Expected: 0.29.0

# 2. Settings load
PYTHONPATH=. python3 -c "from app.core.config import settings; print(settings.database.schema)"
# Expected: public

# 3. 46 features
PYTHONPATH=. python3 -c "from app.core.config import settings; print(len(settings.ml.features.matrix))"
# Expected: 46

# 4. All ORM models import
PYTHONPATH=. python3 -c "from app.models.orm import *; print('OK')"
# Expected: OK

# 5. Engines initialise
PYTHONPATH=. python3 -c "from app.core.database import async_engine, sync_engine; print('OK')"
# Expected: OK

# 6. Docker services healthy
docker compose up -d postgres redis && sleep 15 && docker compose ps
# Expected: both services show "healthy"

# 7. Run migrations
PYTHONPATH=. python3 scripts/run_migrations.py
# Expected: exits cleanly

# 8. 10 tables exist
docker exec aip_postgres psql -U aip_user -d audience_intelligence -c "\dt public.*"
# Expected: 10 tables + alembic_version

# 9. feature_store has 64 columns
docker exec aip_postgres psql -U aip_user -d audience_intelligence \
  -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='feature_store';"
# Expected: 64

# 10. Tests pass
PYTHONPATH=. python3 -m pytest tests/ -v
# Expected: 16 passed

# 11. Pre-commit clean
pre-commit run --all-files
# Expected: all Passed
```

---

## Common Issues and Fixes

### Issue: `ModuleNotFoundError: No module named 'pydantic'`
```bash
# Activate venv first:
source venv/bin/activate
# Then pip install:
pip install -r requirements/base.txt
```

### Issue: `ValidationError: 5 validation errors for Settings`
The `.env` file is missing required variables. Check:
```bash
grep -E "DATABASE__URL|REDIS__URL|MLFLOW__TRACKING_URI|API__API_KEYS|API__ADMIN_API_KEY" .env
```

### Issue: Integration tests fail with `DuplicateTable`
The migration has `schema="public"` hardcoded. Fix:
```python
# In alembic/versions/*_initial_schema.py, add at top:
_schema = settings.database.schema
# Replace all: schema="public" → schema=_schema
```

### Issue: `DATABASE__SCHEMA` env var not respected in subprocess
Do NOT set `DATABASE__SCHEMA` in `.env` file. Remove it. The YAML default (`public`) will be used unless overridden via process env var.

### Issue: Pre-commit blocks commit with `E501 line too long`
Black formats at 88 chars; flake8 checks at 88 chars. Long docstrings must be wrapped or shortened. Module-level docstrings on line 1 are the most common source.
