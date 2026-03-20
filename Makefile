.PHONY: up down migrate createsuperuser shell

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	docker compose run --rm web python manage.py migrate

createsuperuser:
	docker compose run --rm web python manage.py createsuperuser

shell:
	docker compose run --rm web python manage.py shell
