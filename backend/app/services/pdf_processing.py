# backend/app/services/pdf_processing.py
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Service for processing PDF documents"""

    def __init__(self, db: Session):
        self.db = db
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    async def process_document(self, document_id: int):
        """Extract text from PDF and create chunks"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")

        # Read PDF
        try:
            reader = PdfReader(document.file_path)
            total_pages = len(reader.pages)
            logger.info(f"Processing PDF: {document.original_filename} ({total_pages} pages)")

            # Extract text from all pages
            full_text = ""
            page_texts = []
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                page_texts.append((page_num, page_text))
                full_text += page_text + "\n"

            # Create chunks
            chunks = self._create_chunks(full_text, page_texts)

            # Save chunks to database
            for idx, (chunk_text, page_num) in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk_text,
                    chunk_index=idx,
                    page_number=page_num
                )
                self.db.add(chunk)

            # Update document status
            document.status = "processed"
            document.processed_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            document.status = "failed"
            self.db.commit()
            raise

    def _create_chunks(self, full_text: str, page_texts: list) -> list:
        """
        Create overlapping text chunks

        Args:
            full_text: Complete document text
            page_texts: List of (page_num, text) tuples

        Returns:
            List of (chunk_text, page_number) tuples
        """
        chunks = []
        words = full_text.split()

        # Simple word-based chunking with overlap
        chunk_size_words = self.chunk_size // 5  # Approximate words per chunk
        overlap_words = self.chunk_overlap // 5

        for i in range(0, len(words), chunk_size_words - overlap_words):
            chunk_words = words[i:i + chunk_size_words]
            chunk_text = " ".join(chunk_words)

            # Find which page this chunk is from (simplified)
            # In a production system, you'd track this more precisely
            page_num = self._find_page_for_chunk(chunk_text, page_texts)

            if len(chunk_text.strip()) > 50:  # Minimum chunk size
                chunks.append((chunk_text, page_num))

        return chunks

    def _find_page_for_chunk(self, chunk_text: str, page_texts: list) -> int:
        """Find which page a chunk belongs to"""
        # Simple heuristic: find the page with the most overlap
        best_page = 1
        best_overlap = 0

        chunk_start = chunk_text[:100]  # Use first 100 chars for matching

        for page_num, page_text in page_texts:
            if chunk_start in page_text:
                return page_num

        return best_page
