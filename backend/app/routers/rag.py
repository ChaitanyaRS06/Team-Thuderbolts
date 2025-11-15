# backend/app/routers/rag.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Query, GitHubToken
from app.auth import get_current_active_user
from app.services.langgraph_workflow import LangGraphAgenticWorkflow
from app.services.search import SearchService
from app.services.web_search import TavilySearchService
from app.services.uva_scraper import UVAResourceScraper
from app.mcp_servers.github_mcp import GitHubMCPServer
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class RAGRequest(BaseModel):
    question: str
    max_iterations: int = 3
    enable_detailed_reasoning: bool = True
    preferred_model: str = "claude-3-5-sonnet-20241022"  # Using Anthropic Claude

class RAGResponse(BaseModel):
    question: str
    answer: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    reasoning_steps: List[Dict[str, Any]]
    iterations_used: int
    model_used: str

@router.post("/ask", response_model=RAGResponse)
async def ask_question(
    request: RAGRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question using the advanced agentic RAG workflow.
    The system will:
    1. Search local documents
    2. Evaluate if more info is needed
    3. Perform web search if necessary
    4. Generate answer with citations
    """
    # Initialize services
    search_service = SearchService(db)
    web_search_service = TavilySearchService()
    uva_scraper = UVAResourceScraper(db)

    # Initialize GitHub MCP if user has connected GitHub
    github_mcp = None
    try:
        github_token = db.query(GitHubToken).filter(
            GitHubToken.user_id == current_user.id
        ).first()

        if github_token:
            github_mcp = GitHubMCPServer(user_id=current_user.id, db=db)
            logger.info(f"GitHub MCP initialized for user {current_user.id}")
        else:
            logger.info(f"No GitHub connection for user {current_user.id}")
    except Exception as e:
        logger.warning(f"Could not initialize GitHub MCP: {e}")

    # Create LangGraph workflow
    workflow = LangGraphAgenticWorkflow(
        search_service=search_service,
        web_search_service=web_search_service,
        uva_scraper=uva_scraper,
        github_mcp=github_mcp
    )

    try:
        # Execute workflow
        result = await workflow.execute(
            question=request.question,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
            max_iterations=request.max_iterations,
            enable_detailed_reasoning=request.enable_detailed_reasoning,
            preferred_model=request.preferred_model,
            db=db
        )

        # Save query to database
        query = Query(
            user_id=current_user.id,
            question=request.question,
            answer=result["final_answer"],
            confidence_score=result["confidence_score"],
            sources_used=json.dumps(result["sources"]),
            reasoning_steps=json.dumps(result["reasoning_steps"]),
            iterations_used=result["iterations_used"],
            model_used=request.preferred_model
        )
        db.add(query)
        db.commit()

        return RAGResponse(
            question=request.question,
            answer=result["final_answer"],
            confidence_score=result["confidence_score"],
            sources=result["sources"],
            reasoning_steps=result["reasoning_steps"],
            iterations_used=result["iterations_used"],
            model_used=request.preferred_model
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@router.get("/history")
async def get_query_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's query history"""
    queries = db.query(Query).filter(
        Query.user_id == current_user.id
    ).order_by(Query.created_at.desc()).limit(limit).all()

    return [
        {
            "id": q.id,
            "question": q.question,
            "answer": q.answer,
            "confidence_score": q.confidence_score,
            "model_used": q.model_used,
            "created_at": q.created_at
        }
        for q in queries
    ]
