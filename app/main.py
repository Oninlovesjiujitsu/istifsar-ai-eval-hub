from fastapi import FastAPI
from app.api import endpoints
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Decoupled MLOps Evaluation Microservice"
)

# Include the evaluation router under /api
app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "online", "service": settings.PROJECT_NAME}
