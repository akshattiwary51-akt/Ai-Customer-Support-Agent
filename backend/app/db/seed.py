from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import (
    Conversation,
    Document,
    DocumentChunk,
    Message,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    SupportTicket,
    TicketEvent,
    User,
    UserRole,
)
from app.services.knowledge_service import tokenize

DEMO_PASSWORD = "Password123!"


def reset_and_seed() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_if_empty()


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.execute(select(User.id)).first():
            return
        customer = User(
            email="customer@example.com",
            full_name="Nora Patel",
            role=UserRole.CUSTOMER.value,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        second_customer = User(
            email="ava@example.com",
            full_name="Ava Chen",
            role=UserRole.CUSTOMER.value,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        agent = User(
            email="agent@example.com",
            full_name="Priya Shah",
            role=UserRole.SUPPORT_AGENT.value,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN.value,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add_all([customer, second_customer, agent, admin])
        db.flush()

        order = Order(
            order_number="ORD-1001",
            customer_id=customer.id,
            status=OrderStatus.SHIPPED.value,
            total_cents=12900,
            currency="USD",
            placed_at=datetime.utcnow() - timedelta(days=8),
            shipped_at=datetime.utcnow() - timedelta(days=2),
            tracking_number="TRK-DEMO-1001",
        )
        other_order = Order(
            order_number="ORD-2001",
            customer_id=second_customer.id,
            status=OrderStatus.DELIVERED.value,
            total_cents=8499,
            currency="USD",
            placed_at=datetime.utcnow() - timedelta(days=12),
            delivered_at=datetime.utcnow() - timedelta(days=5),
            tracking_number="TRK-DEMO-2001",
        )
        cancellable_order = Order(
            order_number="ORD-1002",
            customer_id=customer.id,
            status=OrderStatus.PROCESSING.value,
            total_cents=4599,
            currency="USD",
            placed_at=datetime.utcnow() - timedelta(days=1),
            tracking_number=None,
        )
        db.add_all([order, other_order, cancellable_order])
        db.flush()
        db.add_all(
            [
                OrderItem(order_id=order.id, sku="BAG-001", name="Everyday Carry Pack", quantity=1, unit_price_cents=12900),
                OrderItem(order_id=other_order.id, sku="LMP-010", name="Desk Lamp Pro", quantity=1, unit_price_cents=8499),
                OrderItem(order_id=cancellable_order.id, sku="CAB-003", name="Cable Organizer", quantity=3, unit_price_cents=1533),
                Payment(
                    order_id=order.id,
                    status=PaymentStatus.PAID.value,
                    provider="simulated",
                    provider_reference="SIM-PAY-1001",
                    amount_cents=12900,
                ),
                Payment(
                    order_id=other_order.id,
                    status=PaymentStatus.PAID.value,
                    provider="simulated",
                    provider_reference="SIM-PAY-2001",
                    amount_cents=8499,
                ),
                Payment(
                    order_id=cancellable_order.id,
                    status=PaymentStatus.PAID.value,
                    provider="simulated",
                    provider_reference="SIM-PAY-1002",
                    amount_cents=4599,
                ),
            ]
        )

        policy_text = (
            "Return policy: customers may request a return or refund within 30 days of purchase "
            "when the order has been paid and the product is not marked final sale. Shipping "
            "questions should be answered from verified order tracking data. If evidence is "
            "insufficient, create a support ticket instead of inventing a policy."
        )
        doc = Document(name="return-policy.md", source="seed", content_type="text/markdown", status="INDEXED")
        db.add(doc)
        db.flush()
        db.add(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=0,
                page_number=None,
                text=policy_text,
                token_set=" ".join(sorted(tokenize(policy_text))),
            )
        )

        conversation = Conversation(customer_id=customer.id, title="Where is my order?")
        db.add(conversation)
        db.flush()
        db.add_all(
            [
                Message(conversation_id=conversation.id, role="user", content="Where is ORD-1001?"),
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Order ORD-1001 is shipped. Tracking: TRK-DEMO-1001.",
                ),
            ]
        )
        ticket = SupportTicket(
            customer_id=customer.id,
            conversation_id=conversation.id,
            subject="Customer requested delivery follow-up",
            description="Customer wants support agent follow-up if tracking does not update.",
            priority="NORMAL",
            category="Shipping",
            status="OPEN",
        )
        db.add(ticket)
        db.flush()
        db.add(TicketEvent(ticket_id=ticket.id, actor_id=agent.id, event_type="CREATED", note="Seed ticket"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed()
