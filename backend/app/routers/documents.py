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
from app.services.google_drive_service import GoogleDriveService
from app.config import settings

router = APIRouter()

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    document_type: str
    file_size: int
    status: str
    google_drive_id: str | None
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
    """Upload a document (PDF) and optionally sync to Google Drive"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Determine storage path based on configuration
    if settings.local_storage_path and os.path.exists(settings.local_storage_path):
        # Use local storage path with document type subdirectory
        upload_dir = os.path.join(settings.local_storage_path, document_type.value)
    else:
        # Fallback to uploads directory (in container)
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

    # Upload to Google Drive only if enabled and user has authorized
    if settings.enable_google_drive:
        try:
            google_drive_service = GoogleDriveService(user_id=current_user.id, db=db)
            google_drive_id = await google_drive_service.upload_file(
                file_path=file_path,
                filename=stored_filename,
                folder=document_type.value
            )
            if google_drive_id:
                document.google_drive_id = google_drive_id
                db.commit()
                db.refresh(document)
        except Exception as e:
            print(f"Google Drive upload skipped or failed: {e}")
            # Continue even if Google Drive upload fails
    else:
        print(f"Google Drive disabled - file saved to local storage: {file_path}")

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

    # Delete from Google Drive if it was uploaded there
    if document.google_drive_id:
        try:
            google_drive_service = GoogleDriveService()
            from app.mcp_servers.google_drive_mcp import GoogleDriveMCPServer
            mcp_server = GoogleDriveMCPServer()
            await mcp_server.delete_file(document.google_drive_id)
            print(f"Deleted from Google Drive: {document.google_drive_id}")
        except Exception as e:
            print(f"Google Drive delete failed: {e}")
            # Continue even if Google Drive delete fails

    # Delete local file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # Delete from database
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}
