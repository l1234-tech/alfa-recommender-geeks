from fastapi import FastAPI

app = FastAPI(
    title="Alfa Course Recommender API",
    version="0.1.0",
    description="API персональной рекомендательной системы Альфа-Курса",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "alfa-course-recommender", "docs": "/docs"}
