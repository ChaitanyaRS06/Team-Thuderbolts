# backend/app/services/embeddings.py
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk
from app.config import settings
from datetime import datetime
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing embeddings using local models"""

    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.embedding_model_name = settings.embedding_model

    def _load_model(self):
        """Lazy load the embedding model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        return self.model

    async def generate_embeddings(self, document_id: int):
        """Generate embeddings for all chunks of a document"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")

        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).all()

        if not chunks:
            raise ValueError("No chunks found for document")

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Load model
        model = self._load_model()

        # Process chunks in batches
        batch_size = 32  # Process 32 chunks at a time
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.chunk_text for chunk in batch]

            try:
                # Generate embeddings using Sentence Transformers
                embeddings = model.encode(texts, show_progress_bar=False)

                # Save embeddings
                for chunk, embedding in zip(batch, embeddings):
                    chunk.embedding = embedding.tolist()

                self.db.commit()
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")

            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                raise

        # Update document status
        document.status = "embedded"
        self.db.commit()

        logger.info(f"Successfully generated embeddings for document {document_id}")

    async def generate_query_embedding(self, query: str) -> list:
        """Generate embedding for a search query"""
        try:
            model = self._load_model()
            embedding = model.encode(query, show_progress_bar=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
