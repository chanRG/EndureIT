.PHONY: help build up down logs clean init-db reset-db backup-db shell-backend shell-db health

# Variables
DOCKER_COMPOSE = docker-compose
PROJECT_NAME = endureit

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Build and Start
build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services (backend + frontend)
	@echo "🚀 Starting all services (backend + frontend)..."
	$(DOCKER_COMPOSE) up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Access points:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost/api/v1"
	@echo "   API Docs:  http://localhost/docs"

up-build: ## Build and start all services (backend + frontend)
	@echo "🔨 Building and starting all services..."
	$(DOCKER_COMPOSE) up -d --build
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Access points:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost/api/v1"
	@echo "   API Docs:  http://localhost/docs"

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ All services stopped"

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(DOCKER_COMPOSE) restart
	@echo "✅ Services restarted"

# Logs
logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Show backend logs
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Show frontend logs
	$(DOCKER_COMPOSE) logs -f frontend

logs-db: ## Show database logs
	$(DOCKER_COMPOSE) logs -f db

logs-nginx: ## Show nginx logs
	$(DOCKER_COMPOSE) logs -f nginx

# Database
init-db: ## Initialize database tables
	$(DOCKER_COMPOSE) exec backend python -m app.db.init_db

reset-db: ## Reset database (drop and recreate all tables)
	$(DOCKER_COMPOSE) exec backend python -m app.db.init_db reset

backup-db: ## Backup database to SQL file
	$(DOCKER_COMPOSE) exec db pg_dump -U endureit_user endureit_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Database backed up to backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore-db: ## Restore database from SQL file (usage: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Error: FILE not specified. Usage: make restore-db FILE=backup.sql"; exit 1; fi
	$(DOCKER_COMPOSE) exec -T db psql -U endureit_user endureit_db < $(FILE)

# Shell Access
shell-backend: ## Access backend container shell
	$(DOCKER_COMPOSE) exec backend /bin/bash

shell-frontend: ## Access frontend container shell
	$(DOCKER_COMPOSE) exec frontend /bin/sh

shell-db: ## Access PostgreSQL shell
	$(DOCKER_COMPOSE) exec db psql -U endureit_user -d endureit_db

shell-redis: ## Access Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# Status and Health
ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

health: ## Check health of all services
	@echo "Checking service health..."
	@$(DOCKER_COMPOSE) ps
	@echo "\nAPI Health Check:"
	@curl -sL http://localhost/api/v1/health | python3 -m json.tool || echo "❌ API health check failed"

# Testing
test-backend: ## Run backend tests
	$(DOCKER_COMPOSE) exec backend pytest

test-backend-cov: ## Run backend tests with coverage
	$(DOCKER_COMPOSE) exec backend pytest --cov=app --cov-report=html

test-frontend: ## Run frontend tests
	$(DOCKER_COMPOSE) exec frontend npm test

# Cleanup
clean: ## Stop and remove containers, networks, volumes
	$(DOCKER_COMPOSE) down -v --remove-orphans

clean-all: ## Remove everything including images
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	docker system prune -af

clean-build: ## Clean and rebuild everything
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d --build

# Production
build-prod: ## Build for production
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml build

up-prod: ## Start production services
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

down-prod: ## Stop production services
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down

# Development helpers
format-backend: ## Format backend code
	$(DOCKER_COMPOSE) exec backend black app/
	$(DOCKER_COMPOSE) exec backend isort app/

lint-backend: ## Lint backend code
	$(DOCKER_COMPOSE) exec backend flake8 app/
	$(DOCKER_COMPOSE) exec backend mypy app/

# Environment Setup
setup-env: ## Setup environment files (interactive)
	@./setup-env.sh

# Setup
setup: setup-env ## Complete initial setup - env + build + init
	@echo "🔨 Building services (backend + frontend)..."
	$(DOCKER_COMPOSE) build
	@echo "🚀 Starting services..."
	$(DOCKER_COMPOSE) up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "💾 Initializing database..."
	$(DOCKER_COMPOSE) exec backend python -m app.db.init_db
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "📍 Access points:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost/api/v1"
	@echo "   API Docs:  http://localhost/docs"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run: make setup-strava  (create user with Strava)"
	@echo "  2. Login at http://localhost:3000/login"
	@echo ""
	@echo "Documentation:"
	@echo "  - README.md - Project overview"
	@echo "  - STRAVA_SETUP.md - Strava integration guide"

# Strava Integration
migrate-strava: ## Add Strava columns to database
	@echo "🔧 Adding Strava columns to database..."
	@docker cp backend/add_strava_fields_migration.sql endureit_postgres:/tmp/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec db psql -U endureit_user -d endureit_db -f /tmp/add_strava_fields_migration.sql 2>&1 | grep -v "NOTICE" || true
	@echo "🔧 Adding Strava activities cache table..."
	@docker cp backend/migrations/add_strava_activities_cache.sql endureit_postgres:/tmp/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec db psql -U endureit_user -d endureit_db -f /tmp/add_strava_activities_cache.sql 2>&1 | grep -v "NOTICE" || true
	@echo "🔧 Adding heart rate stream columns..."
	@docker cp backend/migrations/add_hr_stream_columns.sql endureit_postgres:/tmp/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec db psql -U endureit_user -d endureit_db -f /tmp/add_hr_stream_columns.sql 2>&1 | grep -v "NOTICE" || true
	@echo "✓ Database migration complete"

setup-strava: migrate-strava ## Setup Strava user (automated)
	@echo ""
	@echo "========================================================================"
	@echo "🏃 Strava User Setup"
	@echo "========================================================================"
	@echo ""
	@echo "📦 Copying scripts to container..."
	@docker cp backend/create_user_with_token.py endureit_backend:/app/ 2>/dev/null || true
	@docker cp backend/refresh_strava_token.py endureit_backend:/app/ 2>/dev/null || true
	@docker cp backend/app/services/strava_service.py endureit_backend:/app/app/services/ 2>/dev/null || true
	@echo "✓ Scripts copied"
	@echo ""
	@echo "🔧 Updating dependencies..."
	@$(DOCKER_COMPOSE) exec backend pip install --quiet bcrypt==4.0.1 2>/dev/null || echo "Dependencies already up to date"
	@echo "✓ Dependencies updated"
	@echo ""
	@echo "🚀 Creating Strava user..."
	@echo ""
	@$(DOCKER_COMPOSE) exec backend python create_user_with_token.py
	@echo ""
	@echo "✅ Done! Check output above for login credentials"

refresh-strava-token: ## Refresh Strava access token
	@echo "🔄 Refreshing Strava token..."
	@docker cp backend/refresh_strava_token.py endureit_backend:/app/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec backend python refresh_strava_token.py

test-strava: ## Test Strava connection
	@echo "🧪 Testing Strava connection..."
	@docker cp backend/quick_strava_demo.py endureit_backend:/app/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec backend python quick_strava_demo.py

update-username: ## Update username for first user (usage: make update-username USERNAME=newname)
	@echo "🔧 Updating username..."
	@docker cp backend/update_username.py endureit_backend:/app/ 2>/dev/null || true
	@$(DOCKER_COMPOSE) exec backend python update_username.py 1 $(USERNAME)

# Quick commands
dev: up-build init-db ## Quick start for development (backend + frontend)
	@echo ""
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Login with:"
	@echo "   Username: roger"
	@echo "   Password: EndureIT2024!"

stop: down ## Alias for down

restart-all: restart ## Restart all services (alias)

rebuild: clean-build ## Alias for clean-build

start: up ## Start all services (alias)

