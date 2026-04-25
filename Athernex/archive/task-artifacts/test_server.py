"""
Minimal test server for voice assistant - No complex dependencies.
Just language detection and basic API testing.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import only language detection (no other dependencies)
from language.trained_detector import get_trained_detector

# Create FastAPI app
app = FastAPI(
    title="Athernex Voice Assistant - Test Server",
    description="Minimal server for testing language detection",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = get_trained_detector()

# Request models
class TextRequest(BaseModel):
    text: str

class LanguageResponse(BaseModel):
    language: str
    confidence: float
    is_code_mixed: bool
    method: str = "trained"

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "online",
        "message": "Athernex Voice Assistant Test Server",
        "version": "1.0.0",
        "features": ["language_detection"],
        "endpoints": {
            "detect_language": "/api/android/detect-language",
            "test_phrase": "/api/android/test-phrase",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "detector": "ready",
        "languages": ["hi", "en", "kn", "mr", "hinglish"]
    }

@app.post("/api/android/detect-language", response_model=LanguageResponse)
async def detect_language(request: TextRequest):
    """Detect language from text."""
    try:
        result = detector.detect(request.text)
        # Handle tuple return (language, confidence, is_code_mixed)
        if isinstance(result, tuple):
            language, confidence, is_code_mixed = result
            return LanguageResponse(
                language=language,
                confidence=confidence,
                is_code_mixed=is_code_mixed,
                method="trained"
            )
        else:
            # Handle object return
            return LanguageResponse(
                language=result.language,
                confidence=result.confidence,
                is_code_mixed=result.is_code_mixed,
                method="trained"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/android/test-phrase", response_model=LanguageResponse)
async def test_phrase(request: TextRequest):
    """Quick phrase testing."""
    return await detect_language(request)

@app.post("/api/android/classify-intent")
async def classify_intent(request: TextRequest):
    """Basic intent classification (simplified)."""
    text_lower = request.text.lower()
    
    # Simple keyword-based intent detection
    if any(word in text_lower for word in ["चाहिए", "want", "need", "order", "बेकू", "हवे"]):
        intent = "place_order"
        confidence = 0.85
    elif any(word in text_lower for word in ["confirm", "yes", "हाँ", "okay", "ಹೌದು", "होय"]):
        intent = "confirm_order"
        confidence = 0.90
    elif any(word in text_lower for word in ["cancel", "नहीं", "no", "बेड", "नको"]):
        intent = "cancel_order"
        confidence = 0.88
    elif any(word in text_lower for word in ["change", "modify", "बदल", "ಬದಲಾಯಿಸು"]):
        intent = "modify_order"
        confidence = 0.82
    elif any(word in text_lower for word in ["status", "where", "कहाँ", "ಎಲ್ಲಿ", "कुठे"]):
        intent = "check_status"
        confidence = 0.80
    else:
        intent = "request_information"
        confidence = 0.70
    
    return {
        "intent": intent,
        "confidence": confidence,
        "entities": {},
        "method": "rule_based"
    }

@app.post("/api/android/process-speech")
async def process_speech(request: TextRequest):
    """Full speech processing."""
    # Detect language
    result = detector.detect(request.text)
    
    # Handle tuple return
    if isinstance(result, tuple):
        language, confidence, is_code_mixed = result
        lang_result = {
            "language": language,
            "confidence": confidence,
            "is_code_mixed": is_code_mixed
        }
    else:
        lang_result = {
            "language": result.language,
            "confidence": result.confidence,
            "is_code_mixed": result.is_code_mixed
        }
    
    # Classify intent
    intent_result = await classify_intent(request)
    
    return {
        "language": lang_result,
        "intent": intent_result,
        "text": request.text,
        "status": "processed"
    }

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Athernex Voice Assistant - Test Server")
    print("=" * 70)
    print("✅ Language Detection: Ready (5 languages)")
    print("✅ Intent Classification: Ready (rule-based)")
    print("=" * 70)
    print("📍 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🧪 Test UI: Open proxy.html in browser")
    print("=" * 70)
    print("\n🎯 Supported Languages:")
    print("   • Hindi (hi)")
    print("   • English (en)")
    print("   • Kannada (kn)")
    print("   • Marathi (mr)")
    print("   • Hinglish (code-mixed)")
    print("=" * 70)
    print("\n⏳ Starting server...\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
