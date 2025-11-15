# backend/app/services/uva_scraper.py
"""
UVA Resource Scraper
Scrapes and indexes UVA IT resources, policies, and guides
"""
from bs4 import BeautifulSoup
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import UVAResource
from app.services.embeddings import EmbeddingService
from app.config import settings
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class UVAResourceScraper:
    """Scraper for UVA internal resources"""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.base_url = settings.uva_base_url
        self.it_url = settings.uva_it_resources_url

    async def scrape_and_index_it_resources(self) -> int:
        """
        Scrape UVA IT resources and index them
        Returns count of indexed resources
        """
        resources_indexed = 0

        # Common UVA IT resource URLs
        it_pages = [
            f"{self.it_url}/services/onedrive",
            f"{self.it_url}/services/vpn",
            f"{self.it_url}/services/netbadge",
            f"{self.it_url}/security",
            f"{self.it_url}/get-started"
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in it_pages:
                try:
                    logger.info(f"Scraping: {url}")
                    response = await client.get(url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Extract title
                        title = soup.find('h1')
                        title_text = title.get_text(strip=True) if title else url

                        # Extract main content
                        content_div = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
                        if content_div:
                            # Remove script and style elements
                            for script in content_div(['script', 'style']):
                                script.decompose()

                            content = content_div.get_text(separator='\n', strip=True)

                            # Determine resource type
                            resource_type = self._determine_resource_type(url, title_text)

                            # Check if resource already exists
                            existing = self.db.query(UVAResource).filter(
                                UVAResource.url == url
                            ).first()

                            if existing:
                                existing.title = title_text
                                existing.content = content
                                existing.resource_type = resource_type
                                existing.last_scraped = datetime.utcnow()
                                resource = existing
                            else:
                                resource = UVAResource(
                                    url=url,
                                    title=title_text,
                                    content=content,
                                    resource_type=resource_type
                                )
                                self.db.add(resource)

                            self.db.commit()
                            self.db.refresh(resource)

                            # Generate embedding for content
                            embedding = await self.embedding_service.generate_query_embedding(
                                f"{title_text}\n\n{content[:1000]}"  # Use first 1000 chars
                            )
                            resource.embedding = embedding
                            self.db.commit()

                            resources_indexed += 1
                            logger.info(f"Indexed: {title_text}")

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue

        logger.info(f"Indexed {resources_indexed} UVA IT resources")
        return resources_indexed

    def _determine_resource_type(self, url: str, title: str) -> str:
        """Determine the type of resource based on URL and title"""
        url_lower = url.lower()
        title_lower = title.lower()

        if 'onedrive' in url_lower or 'onedrive' in title_lower:
            return 'onedrive_guide'
        elif 'vpn' in url_lower or 'vpn' in title_lower:
            return 'vpn_guide'
        elif 'security' in url_lower or 'security' in title_lower:
            return 'security_policy'
        elif 'netbadge' in url_lower or 'netbadge' in title_lower:
            return 'authentication_guide'
        else:
            return 'it_guide'

    async def search_resources(
        self,
        query: str,
        resource_type: str = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search indexed UVA resources using semantic similarity

        Args:
            query: Search query
            resource_type: Filter by resource type (optional)
            max_results: Maximum number of results

        Returns:
            List of relevant UVA resources
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_query_embedding(query)

        # Build SQL query
        if resource_type:
            sql = text("""
                SELECT
                    id,
                    url,
                    title,
                    content,
                    resource_type,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as relevance_score
                FROM uva_resources
                WHERE resource_type = :resource_type
                    AND embedding IS NOT NULL
                ORDER BY relevance_score DESC
                LIMIT :limit
            """)
            results = self.db.execute(
                sql,
                {
                    "query_embedding": str(query_embedding),
                    "resource_type": resource_type,
                    "limit": max_results
                }
            ).fetchall()
        else:
            sql = text("""
                SELECT
                    id,
                    url,
                    title,
                    content,
                    resource_type,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as relevance_score
                FROM uva_resources
                WHERE embedding IS NOT NULL
                ORDER BY relevance_score DESC
                LIMIT :limit
            """)
            results = self.db.execute(
                sql,
                {
                    "query_embedding": str(query_embedding),
                    "limit": max_results
                }
            ).fetchall()

        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "content": row.content[:500] + "..." if len(row.content) > 500 else row.content,
                "resource_type": row.resource_type,
                "relevance_score": float(row.relevance_score)
            })

        return formatted_results
