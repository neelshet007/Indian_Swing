.PHONY: install dev test lint fmt clean db-init db-upgrade scan api dashboard

install:
	pip install -e ".[dev]"

dev:
	cp -n .env.example .env || true
	mkdir -p data/cache config
	python -m indian_swing.scripts.cli db init

api:
	uvicorn indian_swing.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir indian_swing

dashboard:
	cd dashboard && npm run dev

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=indian_swing --cov-report=html

lint:
	ruff check indian_swing/ tests/
	mypy indian_swing/

fmt:
	ruff format indian_swing/ tests/
	ruff check --fix indian_swing/ tests/

db-init:
	python -m indian_swing.scripts.cli db init

db-upgrade:
	alembic upgrade head

db-reset:
	rm -f data/swing.db
	python -m indian_swing.scripts.cli db init

download:
	python -m indian_swing.scripts.cli data download --universe nifty2000

scan:
	python -m indian_swing.scripts.cli scan run

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

full-setup: install db-init download
	@echo "Platform ready. Run 'make api' and 'make dashboard' to start."
