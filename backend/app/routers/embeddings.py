# backend/app/routers/embeddings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Document
from app.auth import get_current_active_user
from app.services.embeddings import EmbeddingService
from app.services.embeddings_openai import OpenAIEmbeddingService
from app.config import settings

router = APIRouter()

def get_embedding_service(db: Session, provider: str = None):
    """Factory function to get the appropriate embedding service"""
    if provider is None:
        provider = settings.embedding_provider

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAIEmbeddingService(db)
    else:  # Default to HuggingFace
        return EmbeddingService(db)

@router.post("/generate/{document_id}")
async def generate_embeddings(
    document_id: int,
    provider: str = Query(None, description="Embedding provider: 'huggingface' or 'openai'. Defaults to config setting."),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate embeddings for a processed document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "processed":
        raise HTTPException(
            status_code=400,
            detail="Document must be processed before generating embeddings"
        )

    # Get the appropriate embedding service
    try:
        embedding_service = get_embedding_service(db, provider)
        provider_name = provider or settings.embedding_provider
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate embeddings
    try:
        await embedding_service.generate_embeddings(document.id)
        return {
            "message": "Embeddings generated successfully",
            "provider": provider_name,
            "model": settings.openai_embedding_model if provider_name == "openai" else settings.embedding_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.get("/stats")
async def get_embedding_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get embedding statistics for current user"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()

    total_docs = len(documents)
    embedded_docs = len([d for d in documents if d.status == "embedded"])

    return {
        "total_documents": total_docs,
        "embedded_documents": embedded_docs,
        "pending_documents": total_docs - embedded_docs,
        "current_provider": settings.embedding_provider,
        "current_model": settings.openai_embedding_model if settings.embedding_provider == "openai" else settings.embedding_model
    }

@router.get("/providers")
async def get_embedding_providers(
    current_user: User = Depends(get_current_active_user)
):
    """Get available embedding providers and their info"""
    providers = {
        "huggingface": {
            "name": "HuggingFace",
            "model": settings.embedding_model,
            "dimensions": 384,
            "cost": "Free",
            "speed": "Fast (local)",
            "available": True
        },
        "openai": {
            "name": "OpenAI",
            "model": settings.openai_embedding_model,
            "dimensions": 1536 if "small" in settings.openai_embedding_model else 3072,
            "cost": "$0.02/1M tokens" if "small" in settings.openai_embedding_model else "$0.13/1M tokens",
            "speed": "Medium (API)",
            "available": settings.openai_api_key is not None
        }
    }

    return {
        "providers": providers,
        "current": settings.embedding_provider
    }
