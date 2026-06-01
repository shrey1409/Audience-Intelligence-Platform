-- Creates additional databases for MLflow and Airflow on first postgres container start.
-- audience_intelligence is created by POSTGRES_DB environment variable — do not create here.
-- This script runs only on the FIRST start (when postgres_data volume is empty).

CREATE DATABASE mlflow OWNER aip_user;
CREATE DATABASE airflow OWNER aip_user;
