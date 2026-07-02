.PHONY: help install dev test lint docker-up docker-down migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r backend/requirements.txt -r backend/requirements-dev.txt
	cd frontend && npm install

dev-backend: ## Run backend in development mode
	uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

test: ## Run all tests
	pytest backend/tests/ -v --cov=backend

lint: ## Run linter
	ruff check backend/ agent/
	ruff format --check backend/ agent/

format: ## Format code
	ruff format backend/ agent/

docker-up: ## Start all services with Docker Compose
	docker compose up -d --build

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/htmlcov
