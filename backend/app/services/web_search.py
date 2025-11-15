# backend/app/services/web_search.py
from tavily import TavilyClient
from app.config import settings
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TavilySearchService:
    """Service for web search using Tavily API"""

    def __init__(self):
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> List[Dict[str, Any]]:
        """
        Perform web search using Tavily

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: "basic" or "advanced"

        Returns:
            List of search results with content and metadata
        """
        try:
            # Perform search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
                include_raw_content=False
            )

            # Format results
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "source": "web_search"
                })

            # Add Tavily's AI-generated answer if available
            if response.get("answer"):
                results.insert(0, {
                    "title": "AI Summary",
                    "url": "",
                    "content": response["answer"],
                    "score": 1.0,
                    "source": "tavily_answer"
                })

            logger.info(f"Tavily search returned {len(results)} results for: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            # Return empty results on error rather than failing
            return []

    async def search_with_context(self, query: str, context: str) -> str:
        """
        Search with additional context for more relevant results

        Args:
            query: Search query
            context: Additional context to refine search

        Returns:
            Combined answer from search results
        """
        enhanced_query = f"{query}\n\nContext: {context}"
        results = await self.search(enhanced_query, max_results=3)

        if not results:
            return "No web search results found."

        # Combine results into a single response
        combined = "\n\n".join([
            f"**{r['title']}**\n{r['content']}\nSource: {r['url']}"
            for r in results
            if r['content']
        ])

        return combined
