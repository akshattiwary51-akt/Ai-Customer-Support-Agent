import json

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models import (
    Conversation,
    Message,
    ResponseFeedback,
    SupportTicket,
    ToolExecutionLog,
    User,
)
from app.schemas import AnalyticsOverview

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(
    _: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    total_conversations = db.scalar(select(func.count(Conversation.id))) or 0
    escalated = db.scalar(select(func.count(SupportTicket.id)).where(SupportTicket.status == "ESCALATED")) or 0
    backlog = db.scalar(
        select(func.count(SupportTicket.id)).where(SupportTicket.status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"]))
    ) or 0
    priority_rows = db.execute(
        select(SupportTicket.priority, func.count(SupportTicket.id)).group_by(SupportTicket.priority)
    ).all()
    tool_count = db.scalar(select(func.count(ToolExecutionLog.id))) or 0
    tool_success = db.scalar(
        select(func.count(ToolExecutionLog.id)).where(ToolExecutionLog.success.is_(True))
    ) or 0
    feedback_rows = db.execute(select(ResponseFeedback.rating)).scalars().all()
    messages = db.execute(select(Message.citations_json)).scalars().all()
    citation_count = 0
    for raw in messages:
        try:
            citation_count += len(json.loads(raw or "[]"))
        except json.JSONDecodeError:
            continue
    return AnalyticsOverview(
        total_conversations=total_conversations,
        resolved_by_ai=max(total_conversations - escalated, 0),
        human_escalation_rate=round(escalated / total_conversations, 4) if total_conversations else 0.0,
        average_first_response_seconds=None,
        ticket_backlog=backlog,
        priority_distribution={priority: count for priority, count in priority_rows},
        tool_success_rate=round(tool_success / tool_count, 4) if tool_count else None,
        rag_citation_count=citation_count,
        feedback_score=round(sum(feedback_rows) / len(feedback_rows), 4) if feedback_rows else None,
        estimated_llm_cost_usd=None,
    )
