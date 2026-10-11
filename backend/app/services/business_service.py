import json
import time
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    Order,
    OrderStatus,
    PaymentStatus,
    RefundRequest,
    RefundStatus,
    SupportTicket,
    TicketEvent,
    ToolExecutionLog,
    User,
    UserRole,
)


def can_access_customer_resource(user: User, customer_id: int) -> bool:
    return user.role in {UserRole.ADMIN.value, UserRole.SUPPORT_AGENT.value} or user.id == customer_id


def get_owned_order(db: Session, user: User, order_number: str) -> Order:
    order = db.execute(select(Order).where(Order.order_number == order_number)).scalar_one_or_none()
    if order is None or not can_access_customer_resource(user, order.customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def log_tool(
    db: Session,
    user: User,
    tool_name: str,
    started_at: float,
    success: bool,
    conversation_id: int | None = None,
    error_code: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        ToolExecutionLog(
            user_id=user.id,
            conversation_id=conversation_id,
            tool_name=tool_name,
            success=success,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            error_code=error_code,
            safe_metadata=json.dumps(metadata or {}),
        )
    )
    db.commit()


def refund_eligibility(order: Order) -> tuple[bool, int, str]:
    settings = get_settings()
    if order.status == OrderStatus.CANCELLED.value:
        return False, 0, "Cancelled orders are not eligible for an additional refund request."
    if not order.payment or order.payment.status != PaymentStatus.PAID.value:
        return False, 0, "Only paid orders are eligible for refund review."
    age_days = (datetime.now(UTC).replace(tzinfo=None) - order.placed_at.replace(tzinfo=None)).days
    if age_days > settings.refund_window_days:
        return False, 0, f"Order is outside the {settings.refund_window_days}-day refund window."
    return True, order.total_cents, "Order is paid and inside the configured refund window."


def create_refund_request(
    db: Session,
    user: User,
    order: Order,
    reason: str,
    confirm: bool,
    idempotency_key: str,
) -> RefundRequest:
    existing = db.execute(
        select(RefundRequest).where(
            RefundRequest.order_id == order.id, RefundRequest.idempotency_key == idempotency_key
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    eligible, amount_cents, decision = refund_eligibility(order)
    status_value = (
        RefundStatus.PROCESSING.value
        if eligible and confirm
        else RefundStatus.AWAITING_CONFIRMATION.value
        if eligible
        else RefundStatus.REJECTED.value
    )
    refund = RefundRequest(
        order_id=order.id,
        customer_id=user.id,
        status=status_value,
        reason=reason,
        eligible=eligible,
        decision_reason=decision,
        amount_cents=amount_cents,
        idempotency_key=idempotency_key,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def cancel_order(db: Session, order: Order, confirm: bool) -> tuple[bool, str]:
    if order.status in {OrderStatus.SHIPPED.value, OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value}:
        return False, f"Order cannot be cancelled because its status is {order.status}."
    if not confirm:
        return False, "Cancellation is allowed, but explicit confirmation is required."
    order.status = OrderStatus.CANCELLED.value
    db.commit()
    return True, "Order was cancelled in the local demo database."


def create_ticket(
    db: Session,
    user: User,
    subject: str,
    description: str,
    priority: str = "NORMAL",
    category: str = "General",
    conversation_id: int | None = None,
    escalation_reason: str | None = None,
) -> SupportTicket:
    ticket = SupportTicket(
        customer_id=user.id,
        conversation_id=conversation_id,
        subject=subject,
        description=description,
        priority=priority,
        category=category,
        escalation_reason=escalation_reason,
        status="ESCALATED" if escalation_reason else "OPEN",
    )
    db.add(ticket)
    db.flush()
    db.add(
        TicketEvent(
            ticket_id=ticket.id,
            actor_id=user.id,
            event_type="CREATED",
            note=escalation_reason or "Ticket created",
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket
