# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, documents, embeddings, search, rag, uva_resources
from app.routers import settings as settings_router
from app.routers import google_drive_oauth, github_oauth

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="UVA AI Research Assistant",
    description="Smart AI Research Assistant for UVA with RAG, multi-LLM support, and OneDrive integration",
    version="1.0.0"
)

# CORS middleware
origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(embeddings.router, prefix="/embeddings", tags=["Embeddings"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(uva_resources.router, prefix="/uva", tags=["UVA Resources"])
app.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
app.include_router(google_drive_oauth.router, prefix="/google-drive", tags=["Google Drive OAuth"])
app.include_router(github_oauth.router, prefix="/github", tags=["GitHub OAuth"])

@app.get("/")
async def root():
    return {
        "message": "UVA AI Research Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
