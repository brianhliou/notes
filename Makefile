.PHONY: test run migrate-init migrate-rev migrate-up lint fmt type seed

test:
	PYTHONWARNINGS="ignore::ResourceWarning" .venv/bin/pytest -vv && (.venv/bin/mypy app || true)

run:
	uvicorn app.main:app --reload

migrate-init:
	alembic init alembic

migrate-rev:
	PYTHONPATH=. alembic revision --autogenerate -m "init"

migrate-up:
	PYTHONPATH=. alembic upgrade head

lint:
	ruff check .

fmt:
	ruff check . --fix

type:
	mypy app

seed:
	python -m scripts.seed_notes $(if $(COUNT),--count $(COUNT),) $(if $(RESET),--reset,)
