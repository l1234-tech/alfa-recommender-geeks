import logging
logging.basicConfig(level=logging.INFO)
from fastapi import FastAPI

from .api.routes.recommendations import router as recommendations_router

app = FastAPI(
    title="Alfa Course Recommender API",
    version="0.1.0",
    description="API персональной рекомендательной системы Альфа-Курса",
)

app.include_router(recommendations_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "alfa-course-recommender", "docs": "/docs"}
