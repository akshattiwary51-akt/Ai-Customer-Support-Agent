import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import Conversation, Message, ResponseFeedback, User
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationRead,
    FeedbackCreate,
    MessageRead,
)
from app.services.chat_service import respond_to_chat

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return respond_to_chat(
        db,
        current_user,
        payload.message,
        conversation_id=payload.conversation_id,
        confirm_action=payload.confirm_action,
        idempotency_key=payload.idempotency_key,
    )


@router.post("/chat/stream", response_model=ChatResponse)
def chat_stream_placeholder(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return respond_to_chat(
        db,
        current_user,
        payload.message,
        conversation_id=payload.conversation_id,
        confirm_action=payload.confirm_action,
        idempotency_key=payload.idempotency_key,
    )


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(
        select(Conversation)
        .where(Conversation.customer_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    ).scalars().all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = [
        MessageRead(
            id=message.id,
            role=message.role,
            content=message.content,
            citations=json.loads(message.citations_json or "[]"),
            created_at=message.created_at,
        )
        for message in conversation.messages
    ]
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(conversation)
    db.commit()


@router.post("/feedback")
def create_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    message = db.get(Message, payload.message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    conversation = db.get(Conversation, message.conversation_id)
    if conversation is None or conversation.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    feedback = ResponseFeedback(
        message_id=payload.message_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"status": "recorded", "feedback_id": feedback.id}
