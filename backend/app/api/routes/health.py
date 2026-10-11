from fastapi import APIRouter

from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
def ready():
    return HealthResponse(status="ready")
