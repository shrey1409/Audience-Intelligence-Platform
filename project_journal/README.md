# Audience Intelligence Platform — Project Journal

**Last Updated:** 2026-05-31
**Current Phase:** Phase 2 — Database Schema (verification complete, PR open)
**Repository:** https://github.com/shrey1409/Audience-Intelligence-Platform

---

## What This Folder Is

This folder is the single source of truth for the entire Audience Intelligence Platform project. It functions simultaneously as:

- **Project Knowledge Base** — everything we know about this system
- **Engineering Wiki** — how it works and why it was built this way
- **Architecture Repository** — current and planned architectural decisions
- **Decision Log** — every major choice with rationale and alternatives
- **Learning Repository** — lessons learned, bugs hit, patterns discovered
- **Replication Guide** — step-by-step instructions to recreate from scratch
- **Developer Onboarding Guide** — everything a new engineer needs to know
- **Project History Tracker** — chronological record of what happened and when

## How to Use This Journal

| Situation | Start Here |
|---|---|
| Lost access to Claude Code mid-project | [REPLICATION_GUIDE.md](REPLICATION_GUIDE.md) + [CURRENT_STATUS.md](CURRENT_STATUS.md) |
| New machine / fresh environment | [REPLICATION_GUIDE.md](REPLICATION_GUIDE.md) |
| Starting a new Claude session | [CURRENT_STATUS.md](CURRENT_STATUS.md) + [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) |
| New engineer joining | [PROJECT_VISION.md](PROJECT_VISION.md) → [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) → [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) |
| Returning after 6+ months | [PROJECT_HISTORY.md](PROJECT_HISTORY.md) → [CURRENT_STATUS.md](CURRENT_STATUS.md) |
| Need to understand a decision | [DECISION_LOG.md](DECISION_LOG.md) or `decisions/` folder |
| Understanding a specification | `specifications/` folder |
| Reviewing phase history | `milestones/` folder |

## Quick Reference

### The One-Line Summary
> An ML-powered audience segmentation platform that ingests data from 8 source systems, builds a 46-feature user matrix, assigns one of 9 persona labels per user using unsupervised clustering, and exposes results via a FastAPI microservice — built for digital publishers to monetise their audience data.

### Current Phase Summary
- Phase 1 (Environment Setup): ✅ COMPLETE
- Phase 2 (Database Schema): 🔄 IN PROGRESS — verification done, PR open for merge
- Phases 3–15: ⏳ PENDING

### Key Numbers
- **46** ML features per user
- **9** persona labels
- **10** database tables (9 source + ga4_identity_bridge)
- **64** columns in feature_store
- **15** engineering phases total
- **8** source system connectors
- **3** propensity scores (subscription, churn, commerce)

### Repository Layout
```
.
├── app/                    FastAPI application (config, ORM, API, services)
├── etl/                    ETL ingestion modules (8 source connectors)
├── ml/                     ML pipeline (features, training, inference)
├── sql/ddl/                10 SQL DDL reference files
├── alembic/                Database migrations
├── dags/                   Airflow DAG definitions
├── configs/                YAML configuration (base, dev, prod, clients/)
├── tests/                  Unit + integration tests
├── scripts/                run_migrations.py, seed_database.py (future)
├── docker/                 Docker Compose infrastructure
├── requirements/           Python dependency files
├── .claude/                Claude Code slash commands and specs
└── project_journal/        THIS FOLDER — project knowledge base
```

## Maintenance Protocol

**After every major event**, update the appropriate files:

| Event | Files to Update |
|---|---|
| New specification created | `specifications/`, `PROJECT_HISTORY.md`, `CURRENT_STATUS.md` |
| Architectural decision made | `decisions/adr_NNN.md`, `DECISION_LOG.md`, `ARCHITECTURE_OVERVIEW.md` |
| Phase completed | `milestones/milestone_NN.md`, `CURRENT_STATUS.md`, `PROJECT_HISTORY.md` |
| Bug / unexpected behavior found | `LEARNINGS.md`, relevant `session_logs/` |
| New Claude session started | Read `CURRENT_STATUS.md` first; update at end of session |
| Requirements change | `PROJECT_VISION.md`, `DECISION_LOG.md`, relevant `specifications/` |
