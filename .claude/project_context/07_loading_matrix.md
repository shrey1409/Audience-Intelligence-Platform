# Context Loading Matrix

**Use this table to minimize token usage by loading only necessary files per task type.**

## Loading Guidelines by Task

| Task Type | Always Load | Load If Needed | Never Load | Est. Tokens |
|-----------|-------------|---|---|---|
| **Start new phase** (/phase-start) | 00_global, CURRENT_STATUS | phase spec (if exists) | ml/api/infra context | ~12K |
| **Create phase spec** (/create-spec) | 00_global, CURRENT_STATUS | configs/base.yaml, related files | large archives | ~15K |
| **Build DB/ETL file** (/build-file) | 00_global, CURRENT_STATUS, 01_data | target file, sql/ddl/, orm/ | ml/api context | ~25K |
| **Build ML file** (/build-file) | 00_global, CURRENT_STATUS, 02_ml | target file, ml/ modules | data/api context | ~25K |
| **Build API file** (/build-file) | 00_global, CURRENT_STATUS, 03_api | target file, app/ modules | ml/data context | ~25K |
| **Build infra/CI** (/build-file) | 00_global, CURRENT_STATUS, 04_infra | target file, docker/, .github/ | domain context | ~20K |
| **Generate tests** (/test-gen) | 00_global | target module, test fixtures | unrelated domains | ~15K |
| **Validate schema** (/db-check) | 00_global, 01_data | sql/ddl/, app/models/orm/ | ml/api/infra context | ~30K |
| **Validate ML config** (/ml-check) | 00_global, 02_ml | configs/base.yaml | data/api context | ~15K |
| **Debug issue** (/debug) | 00_global, CURRENT_STATUS | domain-specific context (see below) | unrelated domains | ~18K |
| **Validate phase** (/validate-phase) | 00_global | phase spec, spec deliverables | large archives | ~15K |
| **Commit phase** (/phase-commit) | 00_global, CURRENT_STATUS | phase spec (optional) | everything else | ~8K |
| **Ship phase** (/phase-ship) | 00_global, CURRENT_STATUS | phase spec, DoD checklist | everything else | ~15K |

## Debug Task — Domain-Specific Loading

When running `/debug`, load the context matching the error category:

| Error Type | Load This | Rationale |
|-----------|---|---|
| Import/module errors | 00_global | File structure, conventions |
| Config/settings errors | 00_global, configs/base.yaml | Config structure and keys |
| Database/ORM errors | 00_global, 01_data | Table schema, constraints |
| ML/training errors | 00_global, 02_ml | Feature matrix, algorithms |
| API/endpoint errors | 00_global, 03_api | Endpoint signatures, schemas |
| Docker/infra errors | 00_global, 04_infra | Services, ports, env vars |
| Migration/Alembic errors | 00_global, 01_data | Schema pattern, DDL rules |

## Recovery Prompt Selection

Use recovery prompts from `06_session_recovery.md`:
- **RECOVERY_GLOBAL:** Any session, any task
- **RECOVERY_DATA:** ETL, synthetic data, feature engineering
- **RECOVERY_ML:** Training, evaluation, inference, MLflow
- **RECOVERY_API:** FastAPI, Redis, serving
- **RECOVERY_INFRA:** Docker, CI/CD, Airflow
- **RECOVERY_DB:** Schema, ORM, migrations

## Examples

### Example 1: Building app/services/persona_service.py
```
Load: 00_global + CURRENT_STATUS + 02_ml_context + target file + ml/ directory
Skip: 01_data, 03_api, 04_infra (not relevant)
Tokens: ~25K
```

### Example 2: Debugging "column not found in feature_store"
```
Load: 00_global + 01_data_context + configs/base.yaml
Skip: ml/api/infra context
Tokens: ~18K
```

### Example 3: Starting Phase 4 (ETL)
```
Load: 00_global + CURRENT_STATUS + phase04-etl-ingestion.md
Skip: project_context domain files (will read from spec)
Tokens: ~12K
```

### Example 4: Building tests for etl/ingestion/ga4.py
```
Load: 00_global + target module + test fixtures
Skip: domain context (not needed for test generation)
Tokens: ~15K
```

## Token Budget Summary

| Activity | Token Range | Principle |
|----------|---|---|
| Session baseline | 10–15K | Always: 00_global + CURRENT_STATUS (~12K) |
| Per-task context | +10–20K | Domain-specific project_context files |
| Estimated max per task | ~30K | Worst case: 00_global + all domain files + source code |
| **Full context** (old) | ~200K | CLAUDE.md + CURRENT_STATUS + all specs + all source |

**Target:** Future sessions stay under 200K total by loading only needed files per task.
