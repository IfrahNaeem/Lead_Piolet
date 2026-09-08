# ============================================================
# AlgoQuest — Makefile
# Run all dev commands from the project root
# ============================================================

.PHONY: help install dev-frontend dev-backend dev db-migrate db-seed lint test clean docker-up docker-down

# ── Colors ──────────────────────────────────────────────────
CYAN  = \033[0;36m
GREEN = \033[0;32m
RESET = \033[0m

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)AlgoQuest — Available Commands$(RESET)"
	@echo "────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ── Setup ───────────────────────────────────────────────────
install: ## Install all dependencies (frontend + backend)
	@echo "$(CYAN)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(CYAN)Installing backend dependencies...$(RESET)"
	cd backend && pip install -r requirements.txt
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

install-frontend: ## Install frontend dependencies only
	cd frontend && npm install

install-backend: ## Install backend dependencies only
	cd backend && pip install -r requirements.txt

# ── Development ─────────────────────────────────────────────
dev: ## Start both frontend and backend in parallel
	@echo "$(CYAN)Starting AlgoQuest in development mode...$(RESET)"
	make -j2 dev-frontend dev-backend

dev-frontend: ## Start Next.js dev server (port 3000)
	cd frontend && npm run dev

dev-backend: ## Start FastAPI dev server (port 8000)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ── Database ─────────────────────────────────────────────────
db-migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

db-rollback: ## Rollback last migration
	cd backend && alembic downgrade -1

db-seed: ## Seed the database with problems and lessons
	cd backend && python -m app.scripts.seed_problems
	cd backend && python -m app.scripts.seed_lessons

db-reset: ## Drop all tables and re-migrate + re-seed
	cd backend && alembic downgrade base
	make db-migrate
	make db-seed

# ── ML ───────────────────────────────────────────────────────
ml-train: ## Train all ML models (scorer, recommender, detector)
	cd backend && python -m app.ml.train_all

ml-evaluate: ## Evaluate ML model performance
	cd backend && python -m app.ml.evaluate

# ── Build ────────────────────────────────────────────────────
build-frontend: ## Build Next.js for production
	cd frontend && npm run build

build-backend: ## Build backend Docker image
	docker build -t algoquest-backend ./backend

# ── Testing ──────────────────────────────────────────────────
test: ## Run all tests
	make test-frontend
	make test-backend

test-frontend: ## Run frontend tests
	cd frontend && npm run test

test-backend: ## Run backend pytest suite
	cd backend && pytest -v

lint: ## Lint frontend and backend
	cd frontend && npm run lint
	cd backend && pylint app/

type-check: ## TypeScript type checking
	cd frontend && npm run type-check

# ── Docker ───────────────────────────────────────────────────
docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

# ── Deploy ───────────────────────────────────────────────────
deploy-frontend: ## Deploy frontend to Vercel
	cd frontend && npx vercel --prod

deploy-backend: ## Deploy backend to Railway
	@echo "Push to Railway via: railway up"
	railway up

# ── Utilities ────────────────────────────────────────────────
clean: ## Clean build artifacts and caches
	cd frontend && rm -rf .next node_modules/.cache
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} +
	cd backend && find . -name "*.pyc" -delete

env-check: ## Verify all required env vars are set
	@echo "$(CYAN)Checking environment variables...$(RESET)"
	cd backend && python -c "from app.config import settings; print('$(GREEN)✓ Backend env OK$(RESET)')"
	@echo "$(GREEN)✓ Environment check complete$(RESET)"

format: ## Auto-format Python code with black
	cd backend && black app/
	cd backend && isort app/
