"""Document management routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
from app.database.connection import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentQuery
from app.services.rag_service import query_documents, process_document

router = APIRouter()


@router.get("")
def list_documents(organization_id: int = 1, db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.organization_id == organization_id).order_by(Document.created_at.desc()).all()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), name: str = Form(""), category: str = Form("policy"),
                          description: str = Form(""), organization_id: int = Form(1), db: Session = Depends(get_db)):
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    safe_name = f"doc_{organization_id}_{file.filename}".replace(" ", "_")
    file_path = os.path.join(upload_dir, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f: f.write(content)
    doc = Document(organization_id=organization_id, name=name or file.filename, filename=file.filename,
                   file_path=file_path, file_type=ext.lstrip("."), file_size=len(content), category=category,
                   description=description, status="uploaded")
    db.add(doc); db.commit(); db.refresh(doc)
    process_document(db, doc.id)
    return doc


@router.post("/query")
def query_knowledge_base(input: DocumentQuery, db: Session = Depends(get_db)):
    return query_documents(db=db, query=input.query, organization_id=input.organization_id)


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
    if doc.file_path and os.path.exists(doc.file_path): os.remove(doc.file_path)
    db.delete(doc); db.commit()
    return {"message": "Document deleted", "id": doc_id}
