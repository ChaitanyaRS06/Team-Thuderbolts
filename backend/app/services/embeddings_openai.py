# backend/app/services/embeddings_openai.py
"""
OpenAI Embeddings Service - Alternative to HuggingFace
Provides higher quality embeddings using OpenAI's API
"""
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk
from app.config import settings
from datetime import datetime
import logging
from openai import OpenAI
from typing import List

logger = logging.getLogger(__name__)

class OpenAIEmbeddingService:
    """Service for generating embeddings using OpenAI API"""

    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    async def generate_embeddings(self, document_id: int):
        """Generate embeddings for all chunks of a document using OpenAI"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")

        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()

        if not chunks:
            raise ValueError("No chunks found for document")

        logger.info(f"Generating OpenAI embeddings for {len(chunks)} chunks")

        # Process chunks in batches (OpenAI allows up to 2048 inputs per request)
        batch_size = 100  # Conservative batch size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.chunk_text for chunk in batch]

            try:
                # Generate embeddings using OpenAI API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float"
                )

                # Save embeddings
                for chunk, embedding_data in zip(batch, response.data):
                    chunk.embedding = embedding_data.embedding

                self.db.commit()
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            except Exception as e:
                logger.error(f"Error generating OpenAI embeddings: {e}")
                raise

        # Update document status
        document.status = "embedded"
        document.embedding_model = f"openai-{self.model}"
        self.db.commit()

        logger.info(f"Successfully generated OpenAI embeddings for document {document_id}")

    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a search query using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def get_embedding_info(self) -> dict:
        """Get information about the OpenAI embedding model"""
        dimensions_map = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

        return {
            "provider": "openai",
            "model": self.model,
            "dimensions": dimensions_map.get(self.model, 1536),
            "cost_per_1m_tokens": 0.02 if "small" in self.model else 0.13
        }
