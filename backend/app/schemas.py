from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class OrderItemRead(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price_cents: int

    model_config = {"from_attributes": True}


class PaymentRead(BaseModel):
    status: str
    provider: str
    provider_reference: str
    amount_cents: int

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: int
    order_number: str
    status: str
    total_cents: int
    currency: str
    tracking_number: str | None
    items: list[OrderItemRead] = []
    payment: PaymentRead | None = None

    model_config = {"from_attributes": True}


class RefundEligibilityRead(BaseModel):
    order_number: str
    eligible: bool
    amount_cents: int
    reason: str
    requires_confirmation: bool = True


class RefundRequestCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)
    confirm: bool = False
    idempotency_key: str = Field(min_length=8, max_length=128)


class RefundRequestRead(BaseModel):
    id: int
    order_id: int
    status: str
    reason: str
    eligible: bool
    decision_reason: str
    amount_cents: int
    idempotency_key: str

    model_config = {"from_attributes": True}


class CancellationResponse(BaseModel):
    order_number: str
    cancelled: bool
    detail: str
    requires_confirmation: bool


class TicketCreate(BaseModel):
    subject: str = Field(min_length=4, max_length=255)
    description: str = Field(min_length=8, max_length=3000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"
    category: str = Field(default="General", max_length=64)
    conversation_id: int | None = None
    escalation_reason: str | None = None


class TicketUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED", "ESCALATED"] | None = None
    assigned_to_id: int | None = None


class TicketNoteCreate(BaseModel):
    note: str = Field(min_length=2, max_length=3000)


class TicketRead(BaseModel):
    id: int
    customer_id: int
    conversation_id: int | None
    subject: str
    description: str
    priority: str
    category: str
    status: str
    escalation_reason: str | None
    assigned_to_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: int
    name: str
    source: str
    content_type: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)


class Citation(BaseModel):
    document_id: int
    document_name: str
    chunk_id: int
    page_number: int | None = None
    score: float
    excerpt: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    citations: list[Citation]


class ConversationRead(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    citations: list[Citation] = []
    created_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    conversation_id: int | None = None
    confirm_action: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class IntentResult(BaseModel):
    intent: str
    confidence: float
    required_entities: list[str]
    authentication_required: bool
    suggested_action: str
    escalation_required: bool


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageRead
    assistant_message: MessageRead
    intent: IntentResult
    tool_results: list[ToolResult]
    escalation_required: bool


class OrchestrationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    confirm_action: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class OrchestrationStep(BaseModel):
    order: int
    layer: str
    name: str
    status: Literal["complete", "active", "skipped", "retry", "failed"]
    detail: str
    outputs: dict[str, Any] = {}


class OrchestrationGraphNode(BaseModel):
    id: str
    label: str
    layer: str
    status: Literal["complete", "active", "skipped", "retry", "failed"]
    detail: str
    metadata: dict[str, Any] = {}


class OrchestrationGraphEdge(BaseModel):
    source: str
    target: str
    label: str | None = None
    edge_type: Literal["solid", "dashed"] = "solid"


class OrchestrationResponse(BaseModel):
    request: str
    route: str
    retries: int
    quality_score: float
    final_status: Literal["good", "bad", "retry", "failed"]
    final_response: str
    steps: list[OrchestrationStep]
    graph_nodes: list[OrchestrationGraphNode]
    graph_edges: list[OrchestrationGraphEdge]


class FeedbackCreate(BaseModel):
    message_id: int
    rating: Literal[-1, 1]
    comment: str | None = Field(default=None, max_length=1000)


class AnalyticsOverview(BaseModel):
    total_conversations: int
    resolved_by_ai: int
    human_escalation_rate: float
    average_first_response_seconds: float | None
    ticket_backlog: int
    priority_distribution: dict[str, int]
    tool_success_rate: float | None
    rag_citation_count: int
    feedback_score: float | None
    estimated_llm_cost_usd: float | None


class HealthResponse(BaseModel):
    status: str
