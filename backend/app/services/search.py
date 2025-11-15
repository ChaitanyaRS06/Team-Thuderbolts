# backend/app/services/search.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Document, DocumentChunk
from app.services.embeddings import EmbeddingService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Service for semantic similarity search"""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)

    async def search(
        self,
        query: str,
        user_id: int,
        max_results: int = 5,
        similarity_threshold: float = 0.4
    ) -> list:
        """
        Perform semantic similarity search

        Args:
            query: Search query
            user_id: User ID to filter documents
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score

        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_query_embedding(query)

        # Perform vector similarity search using pgvector
        # Using cosine distance: 1 - (embedding <=> query_embedding)
        sql = text("""
            SELECT
                dc.id as chunk_id,
                dc.document_id,
                dc.chunk_text,
                dc.page_number,
                d.original_filename,
                d.document_type,
                1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.user_id = :user_id
                AND dc.embedding IS NOT NULL
                AND 1 - (dc.embedding <=> CAST(:query_embedding AS vector)) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        results = self.db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "user_id": user_id,
                "threshold": similarity_threshold,
                "limit": max_results
            }
        ).fetchall()

        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "document_name": row.original_filename,
                "document_type": row.document_type,
                "chunk_text": row.chunk_text,
                "page_number": row.page_number,
                "similarity_score": float(row.similarity)
            })

        logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
        return formatted_results
