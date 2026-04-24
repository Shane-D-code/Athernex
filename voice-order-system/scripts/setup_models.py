#!/usr/bin/env python3
"""
Athernex Voice Pipeline — Automated Model Setup Script
Task 23.1: Downloads and validates all required ML models.

Usage:
    python scripts/setup_models.py              # Download all models
    python scripts/setup_models.py --check-only # Just validate existing setup
    python scripts/setup_models.py --dry-run    # Show what would be downloaded

Models downloaded:
    - faster-whisper-server (auto-downloads Whisper Medium on first start)
    - Ollama LLaMA 3.1 8B (Q4_K_M quantized) via `ollama pull`
    - Piper TTS voices: hi-IN, en-IN, kn-IN, mr-IN
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── Colour helpers ─────────────────────────────────────────────────────────────
def _c(code: str, text: str) -> str:
    """ANSI colour if terminal supports it."""
    if sys.stdout.isatty() and platform.system() != "Windows":
        return f"\033[{code}m{text}\033[0m"
    return text

OK   = lambda t: print(_c("32", f"  [OK] {t}"))
WARN = lambda t: print(_c("33", f"  [!!] {t}"))
ERR  = lambda t: print(_c("31", f"  [XX] {t}"))
INFO = lambda t: print(f"  [..] {t}")

# ── Constants ──────────────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent / "models"

PIPER_VOICES = {
    "hi-IN": {
        "model": "hi-IN-hemant-medium.onnx",
        "config": "hi-IN-hemant-medium.onnx.json",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/hemant/medium",
    },
    "en-IN": {
        "model": "en-IN-nikhil-medium.onnx",
        "config": "en-IN-nikhil-medium.onnx.json",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_IN/nikhil/medium",
    },
    "kn-IN": {
        "model": "kn-IN-female-medium.onnx",
        "config": "kn-IN-female-medium.onnx.json",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/kn/kn_IN/female/medium",
    },
    "mr-IN": {
        "model": "mr-IN-female-medium.onnx",
        "config": "mr-IN-female-medium.onnx.json",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/mr/mr_IN/female/medium",
    },
}

OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"

# ── Hardware checks ────────────────────────────────────────────────────────────

def check_hardware() -> dict:
    """Check GPU, CUDA, RAM availability."""
    print("\n=== Hardware Validation ===")
    result = {"gpu": False, "vram_gb": 0, "cuda_version": None, "ram_gb": 0}

    try:
        import torch
        if torch.cuda.is_available():
            result["gpu"] = True
            props = torch.cuda.get_device_properties(0)
            result["vram_gb"] = round(props.total_memory / (1024 ** 3), 1)
            result["cuda_version"] = torch.version.cuda
            result["gpu_name"] = props.name
            OK(f"GPU: {props.name} ({result['vram_gb']}GB VRAM)")
            OK(f"CUDA: {result['cuda_version']}")

            # VRAM fit check: Whisper Medium ~2GB + LLaMA 8B Q4 ~5GB = ~7GB
            if result["vram_gb"] >= 7:
                OK(f"VRAM sufficient for Whisper Medium + LLaMA 8B Q4 ({result['vram_gb']}GB >= 7GB)")
            elif result["vram_gb"] >= 5:
                WARN(f"VRAM tight ({result['vram_gb']}GB). Run models sequentially, not simultaneously.")
            else:
                ERR(f"VRAM too low ({result['vram_gb']}GB). Recommend CPU-only mode with smaller models.")
        else:
            WARN("No CUDA GPU detected — will run on CPU (expect 3-5x slower inference)")
    except ImportError:
        ERR("PyTorch not installed — run: pip install torch --index-url https://download.pytorch.org/whl/cu121")

    # RAM check
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
        result["ram_gb"] = ram_gb
        if ram_gb >= 16:
            OK(f"RAM: {ram_gb}GB")
        else:
            WARN(f"RAM: {ram_gb}GB (16GB+ recommended for simultaneous model loading)")
    except ImportError:
        INFO("psutil not installed, skipping RAM check")

    # Disk check
    free_gb = round(shutil.disk_usage(".").free / (1024 ** 3), 1)
    needed_gb = 12  # ~10GB models + 2GB buffer
    if free_gb >= needed_gb:
        OK(f"Disk: {free_gb}GB free (need ~{needed_gb}GB for models)")
    else:
        ERR(f"Disk: only {free_gb}GB free — need at least {needed_gb}GB")

    return result


# ── Ollama model ───────────────────────────────────────────────────────────────

def check_ollama() -> bool:
    """Check if Ollama is installed."""
    return shutil.which("ollama") is not None


def pull_ollama_model(model: str = OLLAMA_MODEL, dry_run: bool = False) -> bool:
    """Pull the LLaMA model via Ollama."""
    print(f"\n=== Ollama: {model} ===")

    if not check_ollama():
        ERR("Ollama not installed. Download from: https://ollama.com/download")
        return False

    # Check if model already exists
    result = subprocess.run(
        ["ollama", "list"], capture_output=True, text=True, timeout=10
    )
    if model.split(":")[0] in result.stdout:
        OK(f"Model already downloaded: {model}")
        return True

    if dry_run:
        INFO(f"[DRY RUN] Would run: ollama pull {model}")
        return True

    INFO(f"Pulling {model} (~4.7GB, this will take a few minutes)...")
    try:
        subprocess.run(["ollama", "pull", model], check=True, timeout=1800)
        OK(f"Model downloaded: {model}")
        return True
    except subprocess.CalledProcessError as e:
        ERR(f"Failed to pull model: {e}")
        return False
    except subprocess.TimeoutExpired:
        ERR("Download timed out (30min). Check internet connection.")
        return False


# ── Piper TTS voices ───────────────────────────────────────────────────────────

def download_piper_voices(dry_run: bool = False) -> bool:
    """Download Piper TTS voice models for Indian languages."""
    print("\n=== Piper TTS Voices ===")
    piper_dir = MODELS_DIR / "piper"
    piper_dir.mkdir(parents=True, exist_ok=True)

    all_ok = True
    for lang, info in PIPER_VOICES.items():
        model_path = piper_dir / info["model"]
        config_path = piper_dir / info["config"]

        if model_path.exists() and config_path.exists():
            OK(f"{lang}: already downloaded ({model_path.name})")
            continue

        if dry_run:
            INFO(f"[DRY RUN] Would download {lang} voice from HuggingFace")
            continue

        INFO(f"Downloading {lang} voice ({info['model']})...")
        try:
            model_url = f"{info['url_base']}/{info['model']}"
            config_url = f"{info['url_base']}/{info['config']}"
            urllib.request.urlretrieve(model_url, model_path)
            urllib.request.urlretrieve(config_url, config_path)
            OK(f"{lang}: downloaded ({model_path.stat().st_size // (1024*1024)}MB)")
        except Exception as e:
            WARN(f"{lang}: download failed ({e}) — Edge TTS will be used as fallback")
            all_ok = False

    return all_ok


# ── Vosk models ────────────────────────────────────────────────────────────────

def check_vosk_models() -> None:
    """Check Vosk model availability (used as STT fallback)."""
    print("\n=== Vosk STT Fallback Models ===")
    vosk_dir = MODELS_DIR / "vosk-model-hi"
    if vosk_dir.exists():
        OK("Vosk Hindi model found")
    else:
        WARN("Vosk model not found at models/vosk-model-hi")
        INFO("Download from: https://alphacephei.com/vosk/models")
        INFO("Recommended: vosk-model-hi-0.22 (1.5GB)")
        INFO("Note: Vosk is only needed if Whisper server fails to start")


# ── Whisper server check ───────────────────────────────────────────────────────

def check_whisper_server() -> None:
    """Guide user on starting the faster-whisper-server."""
    print("\n=== Whisper STT Server ===")
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:8000/health", timeout=2)
        OK("Whisper server running at http://localhost:8000")
    except Exception:
        WARN("Whisper server not running")
        INFO("Start it with: python scripts/start_whisper.py")
        INFO("Or: uvicorn faster_whisper_server.app:app --host 0.0.0.0 --port 8000")
        INFO("Model 'medium' will auto-download on first start (~1.5GB)")


# ── Summary ────────────────────────────────────────────────────────────────────

def print_summary(hw: dict) -> None:
    """Print final setup summary and recommended config."""
    print("\n=== Setup Summary ===")
    print()
    print("  Recommended configuration for your hardware:")

    vram = hw.get("vram_gb", 0)
    if vram >= 7:
        print("    STT:  Whisper Medium  (2GB VRAM, faster-whisper GPU)")
        print("    LLM:  LLaMA 3.1 8B Q4_K_M  (5GB VRAM, Ollama)")
        print("    TTS:  Piper TTS / Edge TTS  (CPU, <150ms)")
        print("    Expected p95 latency: ~2-3 seconds")
    elif vram >= 4:
        print("    STT:  Whisper Small   (1.5GB VRAM)")
        print("    LLM:  Phi-3 Mini      (2.5GB VRAM, Ollama)")
        print("    TTS:  Edge TTS        (free, cloud)")
        print("    Expected p95 latency: ~3-5 seconds")
    else:
        print("    STT:  Vosk (CPU-only, ~1s)")
        print("    LLM:  Phi-3 Mini 4-bit (CPU, ~8-15s)")
        print("    TTS:  Edge TTS (cloud, free)")
        print("    Expected p95 latency: ~10-15 seconds (CPU-only mode)")

    print()
    print("  Quick start:")
    print("    1. ollama serve                       # Start Ollama LLM server")
    print("    2. python scripts/start_whisper.py    # Start Whisper STT server")
    print("    3. python main.py                     # Start API server (port 8080)")
    print("    4. Open http://localhost:8080/docs    # Swagger UI")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Athernex Voice Pipeline — Model Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check-only", action="store_true", help="Validate existing setup only, no downloads")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without doing it")
    parser.add_argument("--skip-piper", action="store_true", help="Skip Piper TTS download (Edge TTS will be used)")
    args = parser.parse_args()

    print("=" * 55)
    print("  Athernex Voice Pipeline — Model Setup")
    print("=" * 55)

    hw = check_hardware()
    check_whisper_server()

    if not args.check_only:
        pull_ollama_model(dry_run=args.dry_run)
        if not args.skip_piper:
            download_piper_voices(dry_run=args.dry_run)

    check_vosk_models()
    print_summary(hw)

    print("Setup complete. Run `python main.py` to start the API server.")
    print()


if __name__ == "__main__":
    main()
