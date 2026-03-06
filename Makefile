.PHONY: up down logs test clean

## Start everything (DB + API + frontend). Migrations and seed run automatically.
up:
	docker compose up -d --build
	@echo ""
	@echo "System starting..."
	@echo "  Frontend : http://localhost:8080"
	@echo "  API      : http://localhost:8000"
	@echo "  Swagger  : http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make logs' to follow startup output."

## Stop all containers (data preserved).
down:
	docker compose down

## Follow logs from all containers.
logs:
	docker compose logs -f

## Follow logs from a single service: make logs-api  make logs-frontend  make logs-db
logs-api:
	docker compose logs -f api

logs-frontend:
	docker compose logs -f frontend

logs-db:
	docker compose logs -f db

## Run the test suite (requires DB to be running).
test:
	docker compose up -d db
	python -m pytest tests/ -v

## Stop and delete all data (full reset).
clean:
	docker compose down -v
	@echo "All containers and volumes removed."
