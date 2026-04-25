"""
Vosk REST API wrapper server (fallback STT on port 8001).

Installs Vosk models for Hindi, English-IN, Kannada, Marathi and
exposes a simple /transcribe endpoint.

Usage:
    python scripts/start_vosk.py
    python scripts/start_vosk.py --port 8001 --language hi
"""

import argparse
import os
import sys
import zipfile
import logging
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Model download URLs (Vosk models, Apache 2.0 licensed)
VOSK_MODELS = {
    "hi": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-hi-0.22.zip",
        "dir": "vosk-model-hi-0.22",
    },
    "en": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip",
        "dir": "vosk-model-en-in-0.5",
    },
    "kn": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-kn-0.1.zip",
        "dir": "vosk-model-small-kn-0.1",
    },
    "mr": {
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-mr-0.1.zip",
        "dir": "vosk-model-small-mr-0.1",
    },
}

MODELS_DIR = Path(__file__).parent.parent / "models" / "vosk"
loaded_models: dict = {}


def download_model(lang: str) -> Path:
    """Download and extract a Vosk model if not already present."""
    info = VOSK_MODELS[lang]
    model_path = MODELS_DIR / info["dir"]
    if model_path.exists():
        print(f"[OK] Model for '{lang}' already at {model_path}")
        return model_path

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = MODELS_DIR / f"{info['dir']}.zip"
    print(f"[DOWNLOAD] Downloading Vosk model for '{lang}' ...")

    with httpx.stream("GET", info["url"], follow_redirects=True) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=8192):
                f.write(chunk)

    print(f"[EXTRACT] Extracting {zip_path} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(MODELS_DIR)
    zip_path.unlink()
    print(f"[OK] Model ready at {model_path}")
    return model_path


def load_model(lang: str):
    """Load a Vosk model into memory."""
    if lang in loaded_models:
        return loaded_models[lang]
    try:
        from vosk import Model, KaldiRecognizer  # noqa: F401
        model_path = download_model(lang)
        model = Model(str(model_path))
        loaded_models[lang] = model
        print(f"[OK] Vosk model '{lang}' loaded")
        return model
    except ImportError:
        print("[ERROR] vosk not installed. Run: pip install vosk")
        sys.exit(1)


# FastAPI app
app = FastAPI(title="Vosk STT Server", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "models_loaded": list(loaded_models.keys())}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form("hi"),
    sample_rate: int = Form(16000),
):
    """Transcribe raw PCM_16 audio bytes."""
    try:
        from vosk import KaldiRecognizer
        import json as _json

        model = load_model(language)
        rec = KaldiRecognizer(model, sample_rate)
        rec.SetWords(True)

        audio_data = await file.read()
        rec.AcceptWaveform(audio_data)
        result = _json.loads(rec.FinalResult())

        return JSONResponse({
            "text": result.get("text", ""),
            "language": language,
            "result": result.get("result", []),
        })
    except Exception as e:
        logger.exception("Transcription error")
        return JSONResponse({"error": str(e)}, status_code=500)


def main():
    parser = argparse.ArgumentParser(description="Start Vosk STT server")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--language", default="hi", choices=list(VOSK_MODELS.keys()))
    parser.add_argument("--preload-all", action="store_true", help="Preload all language models")
    args = parser.parse_args()

    print(f"\n[INFO] Starting Vosk STT server on http://{args.host}:{args.port}")

    if args.preload_all:
        for lang in VOSK_MODELS:
            load_model(lang)
    else:
        load_model(args.language)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
