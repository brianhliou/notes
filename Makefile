.PHONY: test run

test:
	pytest -q

run:
	uvicorn app.main:app --reload

