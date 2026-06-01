# Current Status — Audience Intelligence Platform

**Last updated:** 2026-06-01
**Current phase:** 3 — Synthetic Data Generation
**Current branch:** feature/phase03-synthetic-data
**Status:** Spec ready, implementation pending

## Progress
- ✅ Phase 1: Environment Setup (merged)
- ✅ Phase 2: Database Schema (merged, PR #5) — 10 tables, 64-col feature_store, 46 ML features
- 🔄 Phase 3: Synthetic Data (in progress) — generators + seeds needed
- ⏳ Phases 4-10: Pending

## Last Completed
Phase 2 database schema with Alembic migrations, ORM models, and integration tests (all passing).

## Next Immediate Action
Implement synthetic data generators for Phase 3: GA4 events, identity bridge, transunion demographics, first-party attributes, behavioral segments, lookalike scores, survey responses, device graphs.

## Phase 3 Watch-Outs
1. **GA4 identity resolution:** pseudo_id → user_id mapping via login events (ga4_identity_bridge)
2. **Coverage percentages:** Vary by source (GA4: 64%, Transunion: 70%, First-party: 95%)
3. **Feature completeness:** All 46 features must be present in seeded feature_store
4. **Deterministic seeding:** Use Faker with fixed seed for reproducibility
5. **Insertion order:** user_profiles first, feature_store last (to avoid FK constraint failures)

## Known Issues from Phase 2
- importlib.reload() doesn't work for schema override in tests → use subprocess isolation
- Pydantic-settings constructor kwargs override env vars → use env fixtures instead
- Docker volume persistence → use `docker compose down -v` for clean slate
- ON CONFLICT upserts require UNIQUE constraints (Alembic auto-detect may miss composite keys)

## Context Optimization Status
- ✅ Created .claude/project_context/ (6 files: 00_global → 06_session_recovery)
- ✅ Rewritten CURRENT_STATUS.md (40 lines, down from 203)
- ⏳ Command files need updating (reference new project_context structure)

**Full history:** See .claude/project_journal/
**Decisions log:** See .claude/project_context/05_decisions.md
**Recovery prompts:** See .claude/project_context/06_session_recovery.md
