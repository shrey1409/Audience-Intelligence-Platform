# Phase 3 — Synthetic Data Journal
**Completed:** 2026-06-02 | **Branch:** feature/phase03-synthetic-data | **PR:** #8 (pending merge)

## What Was Built
Full synthetic data pipeline: 100K users across 10 PostgreSQL tables, deterministic and reproducible.

## Key Decisions Made
- **GA4 sub-batching (20K rows):** Generator originally accumulated one full chunk-of-users before yielding → OOM on bulk insert. Fixed to yield every 20K events regardless of user chunk boundaries.
- **user_id seeding:** `uuid.uuid4()` in zephr_users is OS-random → replaced with `faker.uuid4()` (Faker seeded at 42) so user_ids are deterministic across runs.
- **Timestamps in feature_store:** ORM `server_default=func.now()` was writing wall-clock time → overrode with explicit `created_at=REFERENCE_DT, updated_at=REFERENCE_DT (2026-06-01 00:00:00)`.
- **Test isolation fix:** `test_migrations.py` sets `os.environ["DATABASE__SCHEMA"]` directly, leaking into unit tests. Fixed by popping it in `test_schema` fixture teardown in `tests/conftest.py`.
- **PostgreSQL WAL tuning:** Added `max_wal_size=256MB, wal_buffers=16MB, shared_buffers=256MB` to docker-compose.yml to reduce checkpoint pressure during 14M-row GA4 insert.

## Reproducibility Proof
MD5(feature_store ORDER BY user_id, all columns) = `1129b811d9945a7bd7cb407b4734baeb` — identical across all runs.

## Watch-Outs for Phase 4+
- `persona_label` in feature_store is NULL — ML clustering (Phase 6) writes it; ETL must not touch it
- `bounce_rate` computes as 0.000 for all users currently — derived from single-event sessions, verify ETL logic preserves this
- `avg_revenue` = $12.00 overall (heavy zero-weighting from 90% non-subscribers)
- `openweb_engagement` has 296K rows (vs spec's ~26K) — coverage may be higher than 23% target; verify in Phase 4 ETL
