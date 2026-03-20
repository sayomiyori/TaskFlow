.PHONY: up down migrate createsuperuser shell test test-integration

up:
	docker compose up --build -d

rebuild:
	docker compose up --build -d

down:
	docker compose down

migrate:
	docker compose run --rm django python manage.py migrate

createsuperuser:
	docker compose run --rm django python manage.py createsuperuser

shell:
	docker compose run --rm django python manage.py shell

test:
	docker compose run --rm django pytest -q

test-integration:
	docker compose run --rm django pytest tests/test_rabbitmq_integration.py -m integration -v --no-cov

logs:
	docker compose logs -f

ps:
	docker compose ps
