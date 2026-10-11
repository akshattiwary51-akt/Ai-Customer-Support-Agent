from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas import OrchestrationRequest, OrchestrationResponse
from app.services.orchestration_service import run_ordered_orchestration

router = APIRouter(prefix="/orchestration", tags=["Orchestration"])


@router.post("/run", response_model=OrchestrationResponse)
def run_orchestration(
    payload: OrchestrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return run_ordered_orchestration(
        db,
        current_user,
        payload.message,
        confirm_action=payload.confirm_action,
        idempotency_key=payload.idempotency_key,
    )
