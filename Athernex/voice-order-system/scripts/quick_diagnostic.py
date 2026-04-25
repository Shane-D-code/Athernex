"""Quick diagnostic script to identify issues."""

import sys
import os
from pathlib import Path

print("="*80)
print("VOICE ORDER SYSTEM - QUICK DIAGNOSTIC")
print("="*80)

# Add src and project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

print(f"\nProject Root: {project_root}")
print(f"Python Version: {sys.version}")

# Stage 1: Check critical directories
print("\n" + "="*80)
print("STAGE 1: Directory Structure")
print("="*80)

dirs_to_check = [
    "src",
    "src/stt",
    "src/llm",
    "src/tts",
    "src/language",
    "src/dialogue",
    "src/orchestration",
    "src/api",
    "config",
    "scripts",
    "tests",
]

for dir_path in dirs_to_check:
    full_path = project_root / dir_path
    status = "✓" if full_path.exists() else "✗"
    print(f"{status} {dir_path:30} {full_path}")

# Stage 2: Check critical files
print("\n" + "="*80)
print("STAGE 2: Critical Files")
print("="*80)

files_to_check = [
    "requirements.txt",
    "config/config.py",
    "src/language/detector.py",
    "src/language/fasttext_detector.py",
    "src/language/hybrid_detector.py",
    "src/dialogue/manager.py",
    "src/orchestration/pipeline.py",
    "src/api/main.py",
]

for file_path in files_to_check:
    full_path = project_root / file_path
    status = "✓" if full_path.exists() else "✗"
    print(f"{status} {file_path:40} {full_path}")

# Stage 3: Check Python packages
print("\n" + "="*80)
print("STAGE 3: Python Packages")
print("="*80)

packages = [
    "fastapi",
    "pydantic",
    "uvicorn",
    "fasttext",
    "edge_tts",
    "ollama",
    "httpx",
]

for package in packages:
    try:
        __import__(package)
        print(f"✓ {package:20} installed")
    except ImportError:
        print(f"✗ {package:20} NOT installed - pip install {package}")

# Stage 4: Try importing project modules
print("\n" + "="*80)
print("STAGE 4: Module Imports")
print("="*80)

modules = [
    "config.config",
    "stt.base",
    "llm.base",
    "tts.base",
    "language.detector",
    "language.fasttext_detector",
    "language.hybrid_detector",
    "dialogue.manager",
    "orchestration.orchestrator",
    "orchestration.pipeline",
    "orchestration.order_manager",
    "orchestration.cache",
    "api.main",
]

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module:40} OK")
    except Exception as e:
        print(f"✗ {module:40} ERROR: {str(e)[:50]}")

# Stage 5: Check fastText model
print("\n" + "="*80)
print("STAGE 5: fastText Model")
print("="*80)

model_path = Path.home() / ".fasttext" / "lid.176.bin"
if model_path.exists():
    size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"✓ Model found: {model_path}")
    print(f"  Size: {size_mb:.1f} MB")
else:
    print(f"✗ Model NOT found: {model_path}")
    print(f"  Run: python scripts/setup_fasttext.py")

# Stage 6: Check services
print("\n" + "="*80)
print("STAGE 6: External Services")
print("="*80)

try:
    import httpx
    
    # Check Ollama
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✓ Ollama running ({len(models)} models)")
        else:
            print(f"✗ Ollama returned HTTP {response.status_code}")
    except:
        print(f"✗ Ollama NOT running - Start with: ollama serve")
    
    # Check Whisper (optional)
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2.0)
        print(f"✓ Whisper running (optional)")
    except:
        print(f"⚠ Whisper NOT running (optional)")
        
except ImportError:
    print("✗ httpx not installed - pip install httpx")

# Summary
print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
print("\nNext steps:")
print("1. Fix any ✗ errors above")
print("2. Install missing packages: pip install -r requirements.txt")
print("3. Setup fastText: python scripts/setup_fasttext.py")
print("4. Start Ollama: ollama serve")
print()
