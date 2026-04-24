"""
Simple FastAPI server for testing the voice assistant.
Runs only the Android integration routes.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the Android routes
from api.android_routes import router as android_router

# Create FastAPI app
app = FastAPI(
    title="Athernex Voice Assistant API",
    description="Multilingual voice-based order processing system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Android routes
app.include_router(android_router, prefix="/api/android", tags=["Android"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Athernex Voice Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "language_detection": "/api/android/detect-language",
            "intent_classification": "/api/android/classify-intent",
            "speech_processing": "/api/android/process-speech",
            "test_phrase": "/api/android/test-phrase",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "language_detection": "ready",
            "intent_classification": "ready"
        }
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Athernex Voice Assistant API")
    print("=" * 60)
    print("📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🧪 Test: Open proxy.html in browser")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
