.PHONY: up down logs test

up:
@echo "🚀 docker compose up --build"
@docker compose up -d --build


down:
@echo "🧹 docker compose down"
@docker compose down -v


logs:
@docker compose logs -f web


test:
@pytest -q
