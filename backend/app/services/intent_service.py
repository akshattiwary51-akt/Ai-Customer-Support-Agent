import re

from app.schemas import IntentResult

ORDER_RE = re.compile(r"\b(?:order|#)\s*([A-Z]{2,}-\d{4,}|\d{4,})\b", re.IGNORECASE)


def extract_order_number(text: str) -> str | None:
    match = ORDER_RE.search(text)
    if not match:
        return None
    value = match.group(1).upper()
    return value if value.startswith("ORD-") else f"ORD-{value}"


def classify_intent(message: str) -> IntentResult:
    text = message.lower()
    if any(term in text for term in ["human", "agent", "representative", "person"]):
        return IntentResult(
            intent="Human escalation",
            confidence=0.95,
            required_entities=[],
            authentication_required=True,
            suggested_action="createSupportTicket",
            escalation_required=True,
        )
    if any(term in text for term in ["refund", "money back", "chargeback"]):
        return IntentResult(
            intent="Refund request",
            confidence=0.9,
            required_entities=["order_id"],
            authentication_required=True,
            suggested_action="checkRefundEligibility",
            escalation_required=False,
        )
    if any(term in text for term in ["cancel", "cancellation"]):
        return IntentResult(
            intent="Order cancellation",
            confidence=0.88,
            required_entities=["order_id"],
            authentication_required=True,
            suggested_action="cancelOrder",
            escalation_required=False,
        )
    if any(term in text for term in ["where", "tracking", "shipped", "delivery", "status"]):
        return IntentResult(
            intent="Order status",
            confidence=0.86,
            required_entities=["order_id"],
            authentication_required=True,
            suggested_action="getOrderStatus",
            escalation_required=False,
        )
    if any(term in text for term in ["payment", "paid", "invoice", "card", "charged", "charge"]):
        return IntentResult(
            intent="Payment issue",
            confidence=0.82,
            required_entities=["order_id"],
            authentication_required=True,
            suggested_action="getPaymentStatus",
            escalation_required=False,
        )
    if any(term in text for term in ["policy", "return", "warranty", "how do", "can i"]):
        return IntentResult(
            intent="General FAQ",
            confidence=0.8,
            required_entities=[],
            authentication_required=False,
            suggested_action="searchKnowledgeBase",
            escalation_required=False,
        )
    return IntentResult(
        intent="Technical support",
        confidence=0.48,
        required_entities=[],
        authentication_required=True,
        suggested_action="askClarifyingQuestion",
        escalation_required=True,
    )
