# backend/app/routers/search.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import User
from app.auth import get_current_active_user
from app.services.search import SearchService

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5
    similarity_threshold: float = 0.4

class SearchResult(BaseModel):
    document_id: int
    document_name: str
    chunk_text: str
    similarity_score: float
    page_number: int | None

@router.post("/", response_model=List[SearchResult])
async def semantic_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform semantic similarity search across user's documents"""
    search_service = SearchService(db)

    try:
        results = await search_service.search(
            query=request.query,
            user_id=current_user.id,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
