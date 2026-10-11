from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models import Document, User
from app.schemas import DocumentRead, KnowledgeSearchRequest, KnowledgeSearchResponse
from app.services.knowledge_service import extract_text, index_document, search_knowledge

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    _: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    text, content_type = await extract_text(file)
    return index_document(db, file.filename or "document", text, content_type)


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(
    _: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    return db.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    _: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    db.delete(document)
    db.commit()


@router.post("/documents/{document_id}/reindex", response_model=DocumentRead)
def reindex_document(
    document_id: int,
    _: User = Depends(require_roles("SUPPORT_AGENT", "ADMIN")),
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    document.status = "INDEXED"
    db.commit()
    db.refresh(document)
    return document


@router.post("/search", response_model=KnowledgeSearchResponse)
def search(payload: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    return KnowledgeSearchResponse(
        query=payload.query,
        citations=search_knowledge(db, payload.query, payload.top_k),
    )
