from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.db import db_ready
from app.routes import router
from app.settings import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# Include application routes
app.include_router(router)


def _status_code_to_machine_code(status_code: int) -> str:
    if status_code == 404:
        return "not_found"
    try:
        phrase = HTTPStatus(status_code).phrase
        return phrase.lower().replace(" ", "-")
    except Exception:
        return "error"


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "detail" in detail:
        msg = str(detail.get("detail"))
    else:
        msg = str(detail)
    code = _status_code_to_machine_code(exc.status_code)
    return JSONResponse(status_code=exc.status_code, content={"detail": msg, "code": code})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors() or []
    msg = errors[0].get("msg") if errors else "validation error"
    return JSONResponse(status_code=422, content={"detail": msg, "code": "validation_error"})


@app.get("/ready")
def ready() -> JSONResponse:
    if db_ready():
        return JSONResponse(status_code=200, content={"status": "ready"})
    return JSONResponse(status_code=503, content={"detail": "database unavailable", "code": "service-unavailable"})
