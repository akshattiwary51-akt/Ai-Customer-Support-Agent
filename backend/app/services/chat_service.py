import json
import time

from sqlalchemy.orm import Session

from app.models import Conversation, Message, User
from app.schemas import ChatResponse, MessageRead, ToolResult
from app.services.business_service import (
    cancel_order,
    create_refund_request,
    create_ticket,
    get_owned_order,
    log_tool,
    refund_eligibility,
)
from app.services.intent_service import classify_intent, extract_order_number
from app.services.knowledge_service import search_knowledge


def _message_read(message: Message) -> MessageRead:
    return MessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=json.loads(message.citations_json or "[]"),
        created_at=message.created_at,
    )


def get_or_create_conversation(db: Session, user: User, conversation_id: int | None, title: str) -> Conversation:
    if conversation_id:
        conversation = db.get(Conversation, conversation_id)
        if conversation and conversation.customer_id == user.id:
            return conversation
    conversation = Conversation(customer_id=user.id, title=title[:255] or "Support conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def respond_to_chat(
    db: Session,
    user: User,
    message_text: str,
    conversation_id: int | None = None,
    confirm_action: bool = False,
    idempotency_key: str | None = None,
) -> ChatResponse:
    intent = classify_intent(message_text)
    conversation = get_or_create_conversation(db, user, conversation_id, message_text[:70])
    user_message = Message(conversation_id=conversation.id, role="user", content=message_text)
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    tool_results: list[ToolResult] = []
    citations = []
    response = ""
    order_number = extract_order_number(message_text)

    if intent.suggested_action == "getOrderStatus":
        if not order_number:
            response = "Which order number should I check? You can send it as ORD-1001."
        else:
            started = time.perf_counter()
            try:
                order = get_owned_order(db, user, order_number)
                result = {
                    "order_number": order.order_number,
                    "status": order.status,
                    "tracking_number": order.tracking_number,
                }
                tool_results.append(ToolResult(tool_name="getOrderStatus", success=True, result=result))
                log_tool(db, user, "getOrderStatus", started, True, conversation.id, metadata=result)
                response = (
                    f"Order {order.order_number} is currently {order.status.lower()}. "
                    f"Tracking: {order.tracking_number or 'not available yet'}."
                )
            except Exception as exc:
                log_tool(db, user, "getOrderStatus", started, False, conversation.id, "ORDER_LOOKUP_FAILED")
                raise exc
    elif intent.suggested_action == "getPaymentStatus":
        if not order_number:
            response = "Please provide the order number so I can check payment status."
        else:
            started = time.perf_counter()
            order = get_owned_order(db, user, order_number)
            result = {
                "order_number": order.order_number,
                "payment_status": order.payment.status if order.payment else "UNKNOWN",
            }
            tool_results.append(ToolResult(tool_name="getPaymentStatus", success=True, result=result))
            log_tool(db, user, "getPaymentStatus", started, True, conversation.id, metadata=result)
            response = f"Payment for {order.order_number} is {result['payment_status'].lower()}."
    elif intent.suggested_action == "checkRefundEligibility":
        if not order_number:
            response = "Please send the order number so I can check refund eligibility."
        else:
            started = time.perf_counter()
            order = get_owned_order(db, user, order_number)
            eligible, amount_cents, reason = refund_eligibility(order)
            result = {"eligible": eligible, "amount_cents": amount_cents, "reason": reason}
            tool_results.append(ToolResult(tool_name="checkRefundEligibility", success=True, result=result))
            log_tool(db, user, "checkRefundEligibility", started, True, conversation.id, metadata=result)
            if eligible and confirm_action:
                refund = create_refund_request(
                    db,
                    user,
                    order,
                    reason=message_text,
                    confirm=True,
                    idempotency_key=idempotency_key or f"chat-{conversation.id}-{user_message.id}",
                )
                response = (
                    f"Refund request {refund.id} is now {refund.status.lower()}. "
                    f"The eligible amount is {amount_cents / 100:.2f} {order.currency}."
                )
            elif eligible:
                response = (
                    f"{reason} The eligible amount is {amount_cents / 100:.2f} {order.currency}. "
                    "Please confirm before I submit the refund request."
                )
            else:
                response = reason
    elif intent.suggested_action == "cancelOrder":
        if not order_number:
            response = "Please provide the order number before I check cancellation options."
        else:
            started = time.perf_counter()
            order = get_owned_order(db, user, order_number)
            success, detail = cancel_order(db, order, confirm_action)
            result = {"cancelled": success, "detail": detail}
            tool_results.append(ToolResult(tool_name="cancelOrder", success=success, result=result))
            log_tool(db, user, "cancelOrder", started, success, conversation.id, metadata=result)
            response = detail
    elif intent.suggested_action == "createSupportTicket":
        ticket = create_ticket(
            db,
            user,
            subject="Human support requested",
            description=message_text,
            priority="HIGH",
            category="Escalation",
            conversation_id=conversation.id,
            escalation_reason="Customer requested a human agent",
        )
        tool_results.append(
            ToolResult(tool_name="createSupportTicket", success=True, result={"ticket_id": ticket.id})
        )
        response = f"I created ticket #{ticket.id} and routed it to the support inbox for a human agent."
    else:
        citations = search_knowledge(db, message_text)
        if citations:
            response = (
                "Based on the available knowledge base: "
                f"{citations[0].excerpt} Source: {citations[0].document_name}."
            )
            tool_results.append(
                ToolResult(
                    tool_name="searchKnowledgeBase",
                    success=True,
                    result={"citations": [citation.model_dump() for citation in citations]},
                )
            )
        else:
            response = (
                "I do not have enough verified information to answer that confidently. "
                "I can create a support ticket if you want a human to review it."
            )
            intent.escalation_required = True

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=response,
        citations_json=json.dumps([citation.model_dump() for citation in citations]),
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    db.refresh(user_message)

    return ChatResponse(
        conversation_id=conversation.id,
        user_message=_message_read(user_message),
        assistant_message=_message_read(assistant_message),
        intent=intent,
        tool_results=tool_results,
        escalation_required=intent.escalation_required,
    )
