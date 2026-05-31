-- Creates additional databases for MLflow and Airflow on first postgres container start.
-- audience_intelligence is created by the POSTGRES_DB environment variable — do not create here.
-- This script runs ONLY on the first start when the postgres_data volume is empty.
-- To reset and re-run: docker compose down -v && docker compose up -d postgres

CREATE DATABASE mlflow OWNER aip_user;
CREATE DATABASE airflow OWNER aip_user;
