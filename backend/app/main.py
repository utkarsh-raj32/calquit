"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import contextlib

from app.config import FRONTEND_URL
from app.data.structured import load_structured_data
from app.data.vectorstore import load_and_index_documents
from app.routes import auth, chat, actions, dashboard


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    print("Loading structured data (Excel)...")
    load_structured_data()
    
    print("Indexing documents into ChromaDB...")
    load_and_index_documents()
    
    print("ParcelPilot AI Backend started successfully.")
    yield
    print("Shutting down...")


# Create app
app = FastAPI(
    title="ParcelPilot AI Support API",
    description="Backend for the ParcelPilot AI Agent Assessment.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - Allow all origins for seamless Vercel and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
