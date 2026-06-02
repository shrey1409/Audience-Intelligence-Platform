# Current Status — Audience Intelligence Platform

**Last updated:** 2026-06-02
**Current phase:** 3 — Synthetic Data (COMPLETE, PR pending merge)
**Current branch:** feature/phase03-synthetic-data
**Next phase:** 4 — ETL Ingestion

## Progress
- ✅ Phase 1: Environment Setup (merged)
- ✅ Phase 2: Database Schema (merged, PR #5)
- 🔄 Phase 3: Synthetic Data — code complete, PR open, pending merge
- ⏳ Phases 4-10: Pending

## Phase 3 Final State
- **Commit:** 89d8eea — all fixes applied, all tests passing
- **Tests:** 79/79 passed (unit + integration)
- **Reproducibility:** MD5 = `1129b811d9945a7bd7cb407b4734baeb` (verified across 5 seed runs)
- **Feature validator:** 46/46 features at 100% non-null rate

## Before Moving to Phase 4
1. ✅ Merge Phase 3 PR on GitHub
2. ✅ `git checkout main && git pull`
3. ✅ Run `/phase-start 4 etl-ingestion` to create branch + spec

## Phase 4 Watch-Outs (carry-forward from Phase 3)
1. `persona_label` in feature_store is NULL — ETL must not touch it (Phase 6 writes it)
2. `bounce_rate` = 0.000 across all users in synthetic data — verify ETL real data handles single-event sessions correctly
3. `openweb_engagement` has 296K rows — **this is correct**: event-level table (~13 events/user), not one row per user. feature_store_builder aggregates with GROUP BY user_id. Spec row estimate was wrong. in ETL
4. `importlib.reload()` doesn't work for schema override in tests → use subprocess isolation
5. `os.environ["DATABASE__SCHEMA"]` leaks if set directly (not via monkeypatch) — fixed in conftest but watch for new tests

## Useful Commands
```bash
# Verify seed is healthy
PYTHONPATH=. python3 scripts/validate_features.py

# Full test suite
pytest tests/ -v

# Row counts
docker exec aip_postgres psql -U aip_user -d audience_intelligence \
  -c "SELECT relname, n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' ORDER BY n_live_tup DESC;"
```

**Full journal:** See .claude/project_journal/phase03-synthetic-data.md
**Decisions log:** See .claude/project_context/05_decisions.md
