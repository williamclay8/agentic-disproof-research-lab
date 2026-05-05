.PHONY: test api web worker-example worker-snapshot dev docker-up docker-down product-check

test:
	python3 -m pytest -q

api:
	PYTHONPATH=src python3 apps/api/server.py

web:
	python3 apps/web/server.py

worker-example:
	PYTHONPATH=src python3 apps/worker/worker.py example-run

worker-snapshot:
	PYTHONPATH=src python3 apps/worker/worker.py fixture-snapshot

dev:
	@echo "Starting API on http://127.0.0.1:5299 and web on http://127.0.0.1:5199"
	@trap 'kill 0' INT TERM EXIT; \
	PYTHONPATH=src python3 apps/api/server.py & \
	python3 apps/web/server.py & \
	wait

docker-up:
	docker compose -f infra/docker-compose.yml up --build

docker-down:
	docker compose -f infra/docker-compose.yml down

product-check:
	python3 -m pytest -q tests/test_product_environment.py
