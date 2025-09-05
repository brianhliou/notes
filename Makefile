.PHONY: test run migrate-init migrate-rev migrate-up

test:
	pytest -vv --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --reload

migrate-init:
	alembic init alembic

migrate-rev:
	PYTHONPATH=. alembic revision --autogenerate -m "init"

migrate-up:
	PYTHONPATH=. alembic upgrade head
