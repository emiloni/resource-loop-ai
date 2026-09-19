"""RAG Service."""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import re
from app.models.document import Document, DocumentChunk


def _simple_keyword_search(query, chunks):
    query_words = set(re.findall(r'\w+', query.lower()))
    results = []
    for chunk in chunks:
        content_lower = chunk.content.lower()
        matches = sum(1 for word in query_words if word in content_lower)
        if matches > 0:
            results.append({"chunk_id": chunk.id, "document_id": chunk.document_id, "content": chunk.content,
                            "score": matches / len(query_words) if query_words else 0, "metadata": chunk.chunk_metadata})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]


def _generate_answer_from_chunks(query, chunks):
    if not chunks:
        return {"answer": "I couldn't find relevant information in the organization's documents.", "sources": [], "confidence": 0.0, "disclaimer": "No matching documents found."}
    answer_parts, sources, total_score = [], [], 0
    for c in chunks:
        answer_parts.append(c["content"])
        sources.append({"document_id": c["document_id"], "chunk_id": c["chunk_id"],
                        "snippet": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"]})
        total_score += c["score"]
    avg = total_score / len(chunks) if chunks else 0
    return {"answer": "Based on the organization's documents:\n\n" + "\n\n".join(answer_parts[:3]),
            "sources": sources, "confidence": round(min(avg * 1.5, 0.95), 2),
            "disclaimer": "This answer is based on retrieved document excerpts. Please verify against original documents."}


def query_documents(db, query, organization_id=1):
    documents = db.query(Document).filter(Document.organization_id == organization_id, Document.status == "processed").all()
    if not documents:
        return {"answer": "No processed documents available yet. Upload documents on the Documents page.", "sources": [], "confidence": 0.0, "disclaimer": "Knowledge base empty."}
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id.in_([d.id for d in documents])).all()
    if not chunks:
        return {"answer": "Documents uploaded but not yet processed.", "sources": [], "confidence": 0.0, "disclaimer": "Processing in progress."}
    return _generate_answer_from_chunks(query, _simple_keyword_search(query, chunks))


def process_document(db, document_id):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc: return False
    try:
        doc.status = "processing"
        db.commit()
        content = ""
        if doc.file_path:
            try:
                with open(doc.file_path, "r", encoding="utf-8") as f: content = f.read()
            except (FileNotFoundError, UnicodeDecodeError): content = f"[Could not read: {doc.filename}]"
        if not content: content = f"[Placeholder for {doc.name}]"
        paragraphs = content.split("\n\n")
        chunk_texts, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) > 1000 and current:
                chunk_texts.append(current.strip()); current = para
            else: current += "\n\n" + para if current else para
        if current.strip(): chunk_texts.append(current.strip())
        for i, text in enumerate(chunk_texts):
            db.add(DocumentChunk(document_id=document_id, chunk_index=i, content=text, chunk_metadata=f'{{"section": "chunk_{i}"}}'))
        doc.chunk_count = len(chunk_texts)
        doc.status = "processed"
        db.commit()
        return True
    except: doc.status = "error"; db.commit(); return False
