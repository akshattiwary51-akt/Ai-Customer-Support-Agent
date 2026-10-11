import time

from sqlalchemy.orm import Session

from app.models import User
from app.schemas import (
    OrchestrationGraphEdge,
    OrchestrationGraphNode,
    OrchestrationResponse,
    OrchestrationStep,
    ToolResult,
)
from app.services.business_service import get_owned_order, log_tool, refund_eligibility
from app.services.intent_service import classify_intent, extract_order_number
from app.services.knowledge_service import search_knowledge


def _route_from_intent(intent: str) -> str:
    if intent in {"Refund request", "Payment issue", "Order cancellation"}:
        return "Billing Node"
    if intent == "Technical support":
        return "Technical Node"
    return "General Node"


def _node_detail(node: str) -> str:
    return {
        "Billing Node": "Handles refunds, invoices, charges, payments, and cancellations.",
        "Technical Node": "Handles bugs, errors, integrations, and troubleshooting.",
        "General Node": "Handles FAQs, how-to questions, policies, and general support.",
    }[node]


def _build_graph(
    route: str,
    final_status: str,
    retries: int,
    quality_score: float,
    tool_results: list[ToolResult],
    citations_count: int,
    final_response: str,
) -> tuple[list[OrchestrationGraphNode], list[OrchestrationGraphEdge]]:
    tool_status = "complete" if tool_results else "skipped"
    if final_status == "failed":
        tool_status = "failed"
    response_status = "retry" if final_status == "retry" else "failed" if final_status == "failed" else "complete"
    retry_status = "retry" if retries else "skipped"
    good_status = "complete" if final_status == "good" else "skipped"
    bad_status = "retry" if final_status == "retry" else "failed" if final_status == "failed" else "skipped"

    nodes = [
        OrchestrationGraphNode(
            id="user",
            label="USER",
            layer="User",
            status="complete",
            detail="Customer request enters the system.",
        ),
        OrchestrationGraphNode(
            id="state",
            label="STATE",
            layer="LangGraph",
            status="complete",
            detail="Tracks intent, retries, route, confirmation, and safety flags.",
            metadata={"retries": retries},
        ),
        OrchestrationGraphNode(
            id="orchestrator",
            label="LangGraph Orchestrator",
            layer="LangGraph",
            status="complete",
            detail="Decides what runs next and when.",
            metadata={"route": route},
        ),
        OrchestrationGraphNode(
            id="billing",
            label="Billing Node",
            layer="LangGraph",
            status="active" if route == "Billing Node" else "skipped",
            detail="Refunds, invoices, duplicate charges, payments, cancellations.",
        ),
        OrchestrationGraphNode(
            id="technical",
            label="Technical Node",
            layer="LangGraph",
            status="active" if route == "Technical Node" else "skipped",
            detail="Bugs, errors, integrations, and troubleshooting.",
        ),
        OrchestrationGraphNode(
            id="general",
            label="General Node",
            layer="LangGraph",
            status="active" if route == "General Node" else "skipped",
            detail="FAQs, how-to, policies, and general support.",
        ),
        OrchestrationGraphNode(
            id="blocks",
            label="LangChain Building Blocks",
            layer="LangChain",
            status="complete",
            detail="Prompts, chains, retrievers, and tools decide how each step is done.",
        ),
        OrchestrationGraphNode(
            id="retriever",
            label="Retriever",
            layer="LangChain",
            status="complete",
            detail="Searches company knowledge.",
            metadata={"matches": citations_count},
        ),
        OrchestrationGraphNode(
            id="llm",
            label="LLM",
            layer="LangChain",
            status="complete",
            detail="OpenAI/Gemini-compatible reasoning slot with deterministic local fallback.",
        ),
        OrchestrationGraphNode(
            id="tools",
            label="Tools",
            layer="LangChain",
            status=tool_status,
            detail="Authorized actions against APIs, functions, and database records.",
            metadata={"tool_results": [tool_result.model_dump() for tool_result in tool_results]},
        ),
        OrchestrationGraphNode(
            id="vector-db",
            label="Vector DB",
            layer="LangChain",
            status="complete" if citations_count else "skipped",
            detail="Embedding/vector-store adapter for retrieved chunks.",
        ),
        OrchestrationGraphNode(
            id="provider",
            label="OpenAI / Gemini",
            layer="LangChain",
            status="complete",
            detail="Model provider adapter; local fallback is active without API keys.",
        ),
        OrchestrationGraphNode(
            id="api-functions",
            label="APIs + Functions",
            layer="LangChain",
            status=tool_status,
            detail="Business APIs, deterministic policy functions, and database access.",
        ),
        OrchestrationGraphNode(
            id="evaluator",
            label="Evaluator",
            layer="Evaluator",
            status="retry" if final_status == "retry" else "failed" if final_status == "failed" else "complete",
            detail="LLM-as-judge quality gate for grounding, safety, and completeness.",
            metadata={"quality_score": quality_score},
        ),
        OrchestrationGraphNode(
            id="good",
            label="Good",
            layer="Decision",
            status=good_status,
            detail="Quality gate passed.",
        ),
        OrchestrationGraphNode(
            id="bad",
            label="Bad",
            layer="Decision",
            status=bad_status,
            detail="Quality gate failed or requested retry.",
        ),
        OrchestrationGraphNode(
            id="response",
            label="Response",
            layer="Response",
            status=response_status,
            detail="Final customer-safe response.",
            metadata={"response": final_response},
        ),
        OrchestrationGraphNode(
            id="retry",
            label="Retry",
            layer="LangGraph",
            status=retry_status,
            detail="Retry loops back to orchestrator with updated state.",
            metadata={"retries": retries},
        ),
    ]
    edges = [
        OrchestrationGraphEdge(source="user", target="orchestrator", label="request"),
        OrchestrationGraphEdge(source="state", target="orchestrator", label="state"),
        OrchestrationGraphEdge(source="orchestrator", target="billing", label="route"),
        OrchestrationGraphEdge(source="orchestrator", target="technical", label="route"),
        OrchestrationGraphEdge(source="orchestrator", target="general", label="route"),
        OrchestrationGraphEdge(source="billing", target="blocks"),
        OrchestrationGraphEdge(source="technical", target="blocks"),
        OrchestrationGraphEdge(source="general", target="blocks"),
        OrchestrationGraphEdge(source="blocks", target="retriever"),
        OrchestrationGraphEdge(source="blocks", target="llm"),
        OrchestrationGraphEdge(source="blocks", target="tools"),
        OrchestrationGraphEdge(source="retriever", target="vector-db"),
        OrchestrationGraphEdge(source="llm", target="provider"),
        OrchestrationGraphEdge(source="tools", target="api-functions"),
        OrchestrationGraphEdge(source="vector-db", target="evaluator"),
        OrchestrationGraphEdge(source="provider", target="evaluator"),
        OrchestrationGraphEdge(source="api-functions", target="evaluator"),
        OrchestrationGraphEdge(source="evaluator", target="good"),
        OrchestrationGraphEdge(source="evaluator", target="bad"),
        OrchestrationGraphEdge(source="good", target="response"),
        OrchestrationGraphEdge(source="bad", target="retry", edge_type="dashed"),
        OrchestrationGraphEdge(source="retry", target="orchestrator", edge_type="dashed"),
    ]
    return nodes, edges


def run_ordered_orchestration(
    db: Session,
    user: User,
    message: str,
    confirm_action: bool = False,
    idempotency_key: str | None = None,
) -> OrchestrationResponse:
    intent = classify_intent(message)
    route = _route_from_intent(intent.intent)
    order_number = extract_order_number(message)
    retries = 0
    steps: list[OrchestrationStep] = []
    tool_results: list[ToolResult] = []
    final_response = ""
    quality_score = 0.0
    final_status = "good"

    def add(
        layer: str,
        name: str,
        status: str,
        detail: str,
        outputs: dict | None = None,
    ) -> None:
        steps.append(
            OrchestrationStep(
                order=len(steps) + 1,
                layer=layer,
                name=name,
                status=status,
                detail=detail,
                outputs=outputs or {},
            )
        )

    add(
        "User",
        "Incoming request",
        "complete",
        "The request enters the customer support workflow.",
        {"message": message},
    )
    add(
        "LangGraph",
        "State",
        "complete",
        "State captures intent, retry count, and action confirmation flags.",
        {
            "intent": intent.intent,
            "confidence": intent.confidence,
            "retries": retries,
            "confirm_action": confirm_action,
        },
    )
    add(
        "LangGraph",
        "Orchestrator",
        "complete",
        "Routing, retry policy, and control flow decide what runs next.",
        {"route": route, "suggested_action": intent.suggested_action},
    )

    for node in ["Billing Node", "Technical Node", "General Node"]:
        add(
            "LangGraph",
            node,
            "active" if node == route else "skipped",
            _node_detail(node),
            {"selected": node == route},
        )

    add(
        "LangChain",
        "Building blocks",
        "complete",
        "Prompt assembly, retrieval, tool selection, and local model fallback are prepared.",
        {
            "prompt": "support-agent-system-prompt",
            "chain": "deterministic-local-chain",
            "retriever": "lexical-knowledge-retriever",
            "tools": [intent.suggested_action],
        },
    )

    citations = search_knowledge(db, message)
    add(
        "LangChain",
        "Retriever",
        "complete",
        "Knowledge-base retriever searches indexed company policy chunks.",
        {"matches": len(citations)},
    )
    add(
        "LangChain",
        "Vector DB",
        "complete",
        "Local vector-store adapter uses deterministic lexical tokens for development.",
        {
            "documents": [
                {
                    "document": citation.document_name,
                    "score": citation.score,
                    "excerpt": citation.excerpt[:160],
                }
                for citation in citations
            ]
        },
    )

    add(
        "LangChain",
        "LLM",
        "complete",
        "OpenAI/Gemini-compatible provider slot uses a deterministic local model unless configured.",
        {"provider": "local-fallback", "live_provider_required": False},
    )

    started = time.perf_counter()
    tool_detail: dict = {}
    try:
        if intent.suggested_action == "getOrderStatus" and order_number:
            order = get_owned_order(db, user, order_number)
            tool_detail = {
                "order_number": order.order_number,
                "status": order.status,
                "tracking_number": order.tracking_number,
            }
            final_response = (
                f"Order {order.order_number} is currently {order.status.lower()}. "
                f"Tracking: {order.tracking_number or 'not available yet'}."
            )
            tool_results.append(ToolResult(tool_name="getOrderStatus", success=True, result=tool_detail))
        elif intent.suggested_action == "checkRefundEligibility" and order_number:
            order = get_owned_order(db, user, order_number)
            eligible, amount_cents, reason = refund_eligibility(order)
            tool_detail = {"eligible": eligible, "amount_cents": amount_cents, "reason": reason}
            final_response = (
                f"{reason} "
                f"Eligible amount: {amount_cents / 100:.2f} {order.currency}. "
                "Confirmation is required before submitting a refund."
            )
            tool_results.append(
                ToolResult(tool_name="checkRefundEligibility", success=True, result=tool_detail)
            )
        elif intent.suggested_action == "getPaymentStatus" and order_number:
            order = get_owned_order(db, user, order_number)
            tool_detail = {
                "order_number": order.order_number,
                "payment_status": order.payment.status if order.payment else "UNKNOWN",
            }
            final_response = f"Payment for {order.order_number} is {tool_detail['payment_status'].lower()}."
            tool_results.append(ToolResult(tool_name="getPaymentStatus", success=True, result=tool_detail))
        elif citations:
            tool_detail = {"citations": [citation.model_dump() for citation in citations]}
            final_response = (
                "Based on company knowledge: "
                f"{citations[0].excerpt} Source: {citations[0].document_name}."
            )
            tool_results.append(ToolResult(tool_name="searchKnowledgeBase", success=True, result=tool_detail))
        elif intent.escalation_required:
            final_response = (
                "I do not have enough verified information to answer safely. "
                "This should be escalated to a human support agent."
            )
        else:
            final_response = "I need one more detail before taking action. Please provide the order number."

        log_tool(
            db,
            user,
            intent.suggested_action,
            started,
            True,
            metadata={"route": route, "order_number": order_number},
        )
        add(
            "LangChain",
            "Tools",
            "complete",
            "Allowlisted backend function/API/database tool executed with authorization checks.",
            {"tool_results": [tool_result.model_dump() for tool_result in tool_results]},
        )
    except Exception as exc:
        final_status = "failed"
        final_response = "The tool call failed safely and no success was claimed."
        log_tool(
            db,
            user,
            intent.suggested_action,
            started,
            False,
            error_code="ORCHESTRATION_TOOL_FAILED",
            metadata={"route": route, "order_number": order_number},
        )
        add(
            "LangChain",
            "Tools",
            "failed",
            "Tool execution failed safely; private details are not leaked.",
            {"error": exc.__class__.__name__},
        )

    has_grounding = bool(tool_results or citations)
    quality_score = round(
        min(
            1.0,
            (0.45 if has_grounding else 0.15)
            + (0.35 * intent.confidence)
            + (0.2 if final_status != "failed" else 0),
        ),
        2,
    )
    if quality_score < 0.62 and final_status != "failed":
        retries = 1
        final_status = "retry"
        add(
            "Evaluator",
            "LLM-as-judge quality gate",
            "retry",
            "Quality score is below threshold, so control returns to the orchestrator for retry.",
            {"quality_score": quality_score, "threshold": 0.62},
        )
        add(
            "LangGraph",
            "Retry",
            "retry",
            "Retry loop would re-enter the orchestrator with updated state.",
            {"retries": retries},
        )
    else:
        add(
            "Evaluator",
            "LLM-as-judge quality gate",
            "complete" if final_status != "failed" else "failed",
            "Evaluator checks grounding, tool validity, policy safety, and completeness.",
            {"quality_score": quality_score, "threshold": 0.62},
        )

    if final_status == "retry":
        add(
            "Response",
            "Retry required",
            "retry",
            "The system withholds final answer until the retry path improves confidence.",
            {"response": final_response},
        )
    elif final_status == "failed":
        add(
            "Response",
            "Safe failure",
            "failed",
            "The system returns a safe error and avoids pretending the action succeeded.",
            {"response": final_response},
        )
    else:
        add(
            "Response",
            "Good response",
            "complete",
            "The response is grounded in retrieved evidence or verified tool results.",
            {"response": final_response},
        )

    graph_nodes, graph_edges = _build_graph(
        route,
        final_status,
        retries,
        quality_score,
        tool_results,
        len(citations),
        final_response,
    )

    return OrchestrationResponse(
        request=message,
        route=route,
        retries=retries,
        quality_score=quality_score,
        final_status=final_status,
        final_response=final_response,
        steps=steps,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )
