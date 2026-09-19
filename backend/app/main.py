"""ResourceLoop AI - Main Application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

from app.database.connection import engine, Base
from app.routes import resources, matching, circularity, documents, organizations, dashboard, impact, auth, upload, resource_requests

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(
    title="ResourceLoop AI",
    description="AI-powered resource circularity and redistribution platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# Serve frontend static files (JS, CSS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="frontend_static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(matching.router, prefix="/api/matching", tags=["Matching"])
app.include_router(circularity.router, prefix="/api/circularity", tags=["Circularity"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(impact.router, prefix="/api/impact", tags=["Impact"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(resource_requests.router, prefix="/api/requests", tags=["Resource Requests"])


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "application": "ResourceLoop AI"}


@app.get("/")
async def serve_frontend():
    """Serve the frontend SPA."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
