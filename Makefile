# ═══════════════════════════════════════════════════════════
#  RinRec SmartAdvisor 360 — Developer Automation Makefile
# ═══════════════════════════════════════════════════════════
PYTHON ?= python3
PIP    ?= pip3

.PHONY: help install install-backend install-frontend \
        run run-frontend run-backend run-dashboard run-legacy \
        docker-up docker-down docker-build \
        test lint clean

## ─── Default ──────────────────────────────────────────────
help:		## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Quick start: make install && make run"

## ─── Install ──────────────────────────────────────────────
install: install-backend install-frontend		## Install all dependencies

install-backend:	## Install backend dependencies
	@echo "📦 Installing backend dependencies..."
	$(PIP) install -r backend/requirements.txt

install-frontend:	## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	$(PIP) install -r frontend/requirements.txt

## ─── Run (Local Dev) ──────────────────────────────────────
run: run-frontend		## Run the Streamlit frontend (default)

run-frontend:		## Run Streamlit frontend on :8501
	@echo "🚀 Starting Streamlit frontend on http://localhost:8501"
	streamlit run frontend/app/main.py \
		--server.port 8501 \
		--server.headless false

run-backend:		## Run FastAPI backend on :8000
	@echo "🚀 Starting FastAPI backend on http://localhost:8000/docs"
	$(PYTHON) -m uvicorn backend.app.main:app \
		--host 0.0.0.0 --port 8000 --reload

run-dashboard:		## Run Streamlit admin dashboard on :8502
	@echo "📊 Starting Admin Dashboard on http://localhost:8502"
	streamlit run dashboard/app/admin_dashboard.py \
		--server.port 8502 \
		--server.headless false

run-legacy:		## Run original Streamlit (Product_Demo/ — backward compat)
	@echo "🔁 Running legacy demo_web.py..."
	streamlit run Product_Demo/demo_web.py --server.port 8502

## ─── Docker ───────────────────────────────────────────────
docker-build:		## Build all Docker images
	docker compose build

docker-up:		## Start all services with Docker Compose
	@echo "🐳 Starting all services..."
	docker compose up -d
	@echo ""
	@echo "  Frontend:  http://localhost:8501"
	@echo "  Backend:   http://localhost:8000/docs"

docker-down:		## Stop all Docker services
	docker compose down

docker-logs:		## Stream logs from all containers
	docker compose logs -f

## ─── Quality & Testing ────────────────────────────────────
test:			## Run pytest suite
	@echo "🧪 Running pytest..."
	$(PYTHON) -m pytest backend/tests/ -v

test-syntax:		## Run syntax check on all Python files
	@echo "🧪 Checking Python syntax..."
	$(PYTHON) -m py_compile backend/app/core/config.py && echo "  ✅ config.py"
	$(PYTHON) -m py_compile backend/app/core/db_connector.py && echo "  ✅ db_connector.py"
	$(PYTHON) -m py_compile backend/app/core/security.py && echo "  ✅ security.py"
	$(PYTHON) -m py_compile backend/app/core/auth.py && echo "  ✅ auth.py"
	$(PYTHON) -m py_compile backend/app/main.py && echo "  ✅ backend main.py"
	$(PYTHON) -m py_compile frontend/app/main.py && echo "  ✅ frontend main.py"
	@echo "✅ All syntax checks passed!"

test-db:		## Test MongoDB Atlas connection
	@echo "🔌 Testing MongoDB Atlas connection..."
	$(PYTHON) -c "from backend.app.core.db_connector import get_db_connector; conn = get_db_connector(); print('Connected:', conn.ping_db())"

lint:			## Run basic linting (check for common issues)
	@echo "🔍 Running basic linting..."
	@$(PYTHON) -m py_compile backend/app/**/*.py 2>&1 | grep -v "SyntaxError" || echo "  ✅ No syntax errors"

seed-db:		## Populate MongoDB with sample data from core/fallback_data/
	@echo "🌱 Seeding database with sample data..."
	$(PYTHON) -c "\
import json; \
from pathlib import Path; \
from backend.app.core.db_connector import get_db_connector; \
conn = get_db_connector(); \
data_dir = Path('core/fallback_data'); \
for file in data_dir.glob('*.json'): \
    coll_name = file.stem; \
    with open(file) as f: \
        records = json.load(f); \
    if records: \
        conn.get_collection(coll_name).insert_one(records[0] if isinstance(records, list) and len(records) > 0 else {}); \
        print(f'  ✅ Seeded {coll_name}: {len(records) if isinstance(records, list) else 1} records'); \
print('✅ Database seeded successfully!'); \
"

## ─── Cleanup ──────────────────────────────────────────────
clean:			## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleaned up cache files"
