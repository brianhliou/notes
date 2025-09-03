from fastapi import FastAPI
from app.routes import router
from app.settings import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

# Include application routes
app.include_router(router)
