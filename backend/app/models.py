# backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from pgvector.sqlalchemy import Vector
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")

class DocumentType(str, enum.Enum):
    """Types of documents that can be uploaded"""
    DATASET = "dataset"
    RESEARCH_PAPER = "research_paper"
    RESULTS = "results"
    OTHER = "other"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False, default=DocumentType.OTHER)
    file_size = Column(Integer)
    status = Column(String, default="uploaded")  # uploaded, processed, embedded, failed
    google_drive_id = Column(String, nullable=True)  # Google Drive file ID
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    embedding = Column(Vector(384), nullable=True)  # Sentence Transformers all-MiniLM-L6-v2 is 384 dimensional
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    sources_used = Column(Text, nullable=True)  # JSON string
    reasoning_steps = Column(Text, nullable=True)  # JSON string
    iterations_used = Column(Integer, default=1)
    model_used = Column(String, nullable=True)  # gpt-4, claude-3-5-sonnet, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="queries")

class UVAResource(Base):
    __tablename__ = "uva_resources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    resource_type = Column(String, nullable=True)  # it_guide, policy, faq, etc.
    last_scraped = Column(DateTime, default=datetime.utcnow)
    embedding = Column(Vector(384), nullable=True)

class GoogleDriveToken(Base):
    __tablename__ = "google_drive_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GitHubToken(Base):
    __tablename__ = "github_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    access_token = Column(Text, nullable=False)
    token_type = Column(String, default="bearer")
    scope = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
