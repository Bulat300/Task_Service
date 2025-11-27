run:
	uvicorn main:app --workers 1 --timeout-keep-alive 0 --host 0.0.0.0 --port 8080
.PHONY: run

install:
	pip3 install -r requirements.txt
.PHONY: install

migrate:
	DB_HOST=${DB_HOST} \
	DB_PORT=${DB_PORT} \
	DB_USER=${DB_USER} \
	DB_PASSWORD=${DB_PASSWORD} \
	DB_NAME=${DB_NAME} \
	alembic upgrade head
.PHONY: migrate

start: migrate run
.PHONY: start

lint:
	python3 -m ruff check .
.PHONY: lint

test:
	python3 -W ignore -m pytest ./tests
.PHONY: test

docker-compose:
	docker-compose up
.PHONY: docker-compose

worker:
	python3 run.py worker
.PHONY: worker

worker_low:
	python3 run.py worker_low
.PHONY: worker_low

worker_high:
	python3 run.py worker_high
.PHONY: worker_high

worker_outbox:
	python3 run.py worker_outbox
.PHONY: worker_outbox
