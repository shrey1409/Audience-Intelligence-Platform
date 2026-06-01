# System Design Specification Summary

**Full Document:** `.claude/specs/system_design-spec.md` (1,880 lines)
**Version:** 1.0
**Status:** APPROVED FOR IMPLEMENTATION
**Date:** 2026-05-30

---

## Purpose

Answers the question: "HOW do the components connect, initialise, and interact at the code level?" The master spec says WHAT; this spec says HOW.

## Key Design Decisions

### Configuration Loading (Section 2 + 12)
```
Priority (lowest → highest):
1. configs/base.yaml
2. configs/{APP_ENV}.yaml
3. configs/clients/{CLIENT_NAME}.yaml
4. _apply_env_overrides() → injects process env vars into merged dict
5. .env file (secrets only)
6. Process environment variables
```

Module-level singleton: `settings: Settings = Settings.from_yaml_and_env()`

### Database Engines (Section 3)
- FastAPI path: `create_async_engine` + asyncpg driver (`postgresql+asyncpg://`)
- ETL/ML/Alembic path: `create_engine` + psycopg2 driver (`postgresql://`)
- Both connect to same PostgreSQL server; different drivers, different session types

### Redis (Section 4)
- FastAPI path: `redis.asyncio.Redis` (async)
- ETL Step 9 path: `redis.Redis` (sync)
- Cache key schema: `persona:{schema}:{user_id}`
- TTL set on WRITE only (never on read); value: `settings.redis.ttl_seconds` = 604800

### FastAPI Application Factory (Section 5)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(...)     # structlog setup
    pool = await init_redis_pool(...)
    app.state.redis_pool = pool
    yield
    await close_redis_pool(...)
    await async_engine.dispose()
```

Middleware execution order (last added = first to execute):
```
Incoming: LoggingMiddleware → APIKeyMiddleware → endpoint
Outgoing: endpoint → APIKeyMiddleware → LoggingMiddleware
```

### ORM Schema Injection (Section 9)
```python
__table_args__ = {"schema": settings.database.schema}
```
Evaluated at class definition time. Set `DATABASE__SCHEMA` before any import.

### Alembic env.py (Section 8)
- No `sqlalchemy.url` in `alembic.ini`
- URL injected at runtime from `settings.database.url`
- `version_table_schema = _schema` — Alembic history in client schema
- `include_schemas=True` — autogenerate sees non-public schemas
- `include_object()` — filters to configured schema only

### Identified Risks and Decisions (Section 13)
1. **Async vs sync engine**: async for FastAPI (chosen), sync for ETL (chosen) — both correct
2. **Redis async vs sync**: async for FastAPI (chosen), sync for ETL Step 9 (chosen)
3. **Pydantic YAML loading**: `_apply_env_overrides()` fix required — env vars must override YAML kwargs
4. **Alembic schema-per-tenant**: `version_table_schema`, `include_schemas`, `include_object` — complex but necessary
5. **MLflow PostgreSQL backend**: single postgres instance, two databases (audience_intelligence + mlflow)
6. **structlog vs standard logging**: structlog (chosen) — JSON output, Airflow worker stdout forwarding

## Phase 2 Definition of Done (Section 14) — All Resolved

- [x] config.py field list complete and typed
- [x] Docker Compose service topology complete with health checks
- [x] Database session lifecycle specified (async + sync)
- [x] Redis connection lifecycle specified
- [x] Alembic schema-aware migration env.py specified
- [x] ORM base class schema injection pattern specified
- [x] ETL BaseIngestionModule interface specified
- [x] ML BaseClusteringAlgorithm interface specified
- [x] structlog initialization pattern specified
- [x] Configuration loading sequence specified and unambiguous
