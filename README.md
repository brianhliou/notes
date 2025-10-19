# Notes API — FastAPI + SQLModel (Codex-Built Toy)

Simple notes API to demo ChatGPT Codex coding. Local only. SQLite DB.

## Stack
- FastAPI, SQLModel, Alembic, SQLite
- HTTPX tests, Ruff, MyPy
- JSONL export/import

## Features
- CRUD: POST/GET/LIST/PATCH/DELETE `/notes`
- Wrapper list: `{"items":[...]}` newest-first
- Unified error shape: `{"detail","code"}`
- OpenAPI at `/docs` and `/openapi.json`
- Seed: fake notes generator
- Export/Import: JSONL round-trip

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# run API
uvicorn app.main:app --reload

# health
curl -s localhost:8000/health
# docs
open http://localhost:8000/docs
```

## Config
Reads env vars with safe defaults.
- `DATABASE_URL` (default `sqlite:///./data/app.db`)
- `LOG_LEVEL` (`INFO` default)
- `APP_NAME` (`Notes API` default)
- `ENV` (`dev` default)
- `ENABLE_FTS` (placeholder, unused)

Example:
```bash
DATABASE_URL=sqlite:////tmp/notes.db LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Troubleshooting
- `ImportError: cannot import name 'UTC' from 'datetime'`: your interpreter is older than Python 3.11; upgrade Python or use the bundled `.venv`. This error is unrelated to database initialization.

## Makefile
```bash
make test        # run unit + http tests
make run         # uvicorn app.main:app --reload
make lint        # ruff
make fmt         # ruff --fix
make type        # mypy
make seed        # seed fake notes (COUNT=50 RESET=1 overrides)
```

## Database & Seeding
```bash
# reset and insert 25 notes
make seed RESET=1 COUNT=25

# list
curl -s localhost:8000/notes | jq '.items | length'
```

## Export / Import (JSONL)
```bash
# export
curl -s -H 'Accept: application/x-ndjson' \
  localhost:8000/notes/export > /tmp/notes.jsonl
wc -l /tmp/notes.jsonl

# wipe and import
sqlite3 data/app.db 'DELETE FROM notes;'
curl -s -X POST --data-binary @/tmp/notes.jsonl \
  -H 'Content-Type: application/x-ndjson' \
  localhost:8000/notes/import
```

## API Cheatsheet
```bash
# create
curl -s -X POST localhost:8000/notes \
  -H 'Content-Type: application/json' \
  -d '{"title":"Hello","content":"World","tags":["demo"]}'

# list (wrapper)
curl -s localhost:8000/notes | jq '.items[0]'

# get
curl -s localhost:8000/notes/1

# patch
curl -s -X PATCH localhost:8000/notes/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Updated"}'

# delete
curl -s -X DELETE -i localhost:8000/notes/1
```

## Project Layout
```
app/
  main.py         # FastAPI app
  routes.py       # endpoints
  db.py           # engine + session
  models.py       # SQLModel Note
  settings.py     # env-driven config
scripts/
  seed_notes.py   # seed CLI
alembic/          # migrations
tests/            # unit + http tests
data/             # sqlite db file
```

## Roadmap (optional)
- Auth (API key)
- Pagination params
- Basic rate limit
- Docker (local)
- FTS or LIKE search

## License
MIT
