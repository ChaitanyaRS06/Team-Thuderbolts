# backend/app/routers/uva_resources.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import User
from app.auth import get_current_active_user
from app.services.uva_scraper import UVAResourceScraper

router = APIRouter()

class UVAResourceRequest(BaseModel):
    query: str
    resource_type: str = "it_guide"  # it_guide, policy, faq, etc.

class UVAResourceResponse(BaseModel):
    title: str
    content: str
    url: str
    relevance_score: float

@router.post("/search", response_model=List[UVAResourceResponse])
async def search_uva_resources(
    request: UVAResourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search UVA resources (IT guides, policies, etc.)
    This endpoint scrapes and searches UVA's internal resources
    """
    scraper = UVAResourceScraper(db)

    try:
        results = await scraper.search_resources(
            query=request.query,
            resource_type=request.resource_type
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UVA resource search failed: {str(e)}")

@router.post("/scrape-it-resources")
async def scrape_it_resources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Scrape and index UVA IT resources (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    scraper = UVAResourceScraper(db)

    try:
        count = await scraper.scrape_and_index_it_resources()
        return {"message": f"Successfully indexed {count} UVA IT resources"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
