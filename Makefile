.PHONY: help install install-dev lint format test test-cov clean docker-up docker-down migrate seed pipeline api

help:
	@echo "Audience Intelligence Platform — Developer Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install base dependencies"
	@echo "  make install-dev    Install dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run flake8 + mypy"
	@echo "  make format         Run black + isort"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-cov       Run tests with coverage report"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        Run SQL DDL scripts"
	@echo "  make seed           Seed database with synthetic data"
	@echo ""
	@echo "Services:"
	@echo "  make docker-up      Start all services (PostgreSQL, Redis, MLflow, Airflow)"
	@echo "  make docker-down    Stop all services"
	@echo "  make api            Start FastAPI development server"
	@echo "  make pipeline       Run ML pipeline manually"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove cache and temp files"

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/dev.txt

lint:
	flake8 app/ etl/ ml/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy app/ etl/ ml/ --ignore-missing-imports

format:
	black app/ etl/ ml/ tests/ scripts/
	isort app/ etl/ ml/ tests/ scripts/

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=app --cov=etl --cov=ml --cov-report=term-missing --cov-report=html

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage coverage.xml

docker-up:
	docker compose up -d

docker-down:
	docker compose down

migrate:
	python scripts/run_migrations.py

seed:
	python scripts/seed_database.py

pipeline:
	python scripts/run_pipeline.py

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
