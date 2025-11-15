# backend/app/routers/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
from app.database import get_db
from app.models import User, Document, DocumentType
from app.auth import get_current_active_user
from app.services.pdf_processing import PDFProcessor
from app.services.onedrive_service import OneDriveService

router = APIRouter()

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    document_type: str
    file_size: int
    status: str
    onedrive_path: str | None
    uploaded_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all documents for the current user"""
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    return documents

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a document (PDF) and optionally sync to OneDrive"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Create upload directory
    upload_dir = f"uploads/{current_user.id}"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stored_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, stored_filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document record
    document = Document(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        document_type=document_type,
        file_size=file_size,
        status="uploaded"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Upload to OneDrive (async)
    try:
        onedrive_service = OneDriveService()
        onedrive_path = await onedrive_service.upload_file(
            file_path=file_path,
            filename=stored_filename,
            folder=document_type.value,
            user_email=current_user.email
        )
        document.onedrive_path = onedrive_path
        db.commit()
        db.refresh(document)
    except Exception as e:
        print(f"OneDrive upload failed: {e}")
        # Continue even if OneDrive upload fails

    return document

@router.post("/{document_id}/process")
async def process_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process a document (extract text and create chunks)"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status == "processed":
        return {"message": "Document already processed"}

    # Process PDF
    processor = PDFProcessor(db)
    try:
        await processor.process_document(document.id)
        return {"message": "Document processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}
