from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import Order, User
from app.schemas import (
    CancellationResponse,
    OrderRead,
    RefundEligibilityRead,
    RefundRequestCreate,
    RefundRequestRead,
)
from app.services.business_service import (
    cancel_order,
    create_refund_request,
    get_owned_order,
    refund_eligibility,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    statement = select(Order)
    if current_user.role == "CUSTOMER":
        statement = statement.where(Order.customer_id == current_user.id)
    return db.execute(statement.order_by(Order.placed_at.desc())).scalars().all()


@router.get("/{order_number}", response_model=OrderRead)
def get_order(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_owned_order(db, current_user, order_number.upper())


@router.get("/{order_number}/payment")
def get_payment(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_owned_order(db, current_user, order_number.upper())
    return order.payment or {"status": "UNKNOWN"}


@router.post("/{order_number}/refund-eligibility", response_model=RefundEligibilityRead)
def check_refund_eligibility(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_owned_order(db, current_user, order_number.upper())
    eligible, amount_cents, reason = refund_eligibility(order)
    return RefundEligibilityRead(
        order_number=order.order_number,
        eligible=eligible,
        amount_cents=amount_cents,
        reason=reason,
        requires_confirmation=eligible,
    )


@router.post("/{order_number}/refund-requests", response_model=RefundRequestRead)
def request_refund(
    order_number: str,
    payload: RefundRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_owned_order(db, current_user, order_number.upper())
    return create_refund_request(
        db,
        current_user,
        order,
        reason=payload.reason,
        confirm=payload.confirm,
        idempotency_key=payload.idempotency_key,
    )


@router.post("/{order_number}/cancel", response_model=CancellationResponse)
def cancel(
    order_number: str,
    confirm: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_owned_order(db, current_user, order_number.upper())
    cancelled, detail = cancel_order(db, order, confirm=confirm)
    return CancellationResponse(
        order_number=order.order_number,
        cancelled=cancelled,
        detail=detail,
        requires_confirmation=not confirm and "confirmation is required" in detail,
    )
