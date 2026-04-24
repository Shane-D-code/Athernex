"""
Setup script for fastText language detection.

Downloads and installs:
1. fasttext Python package
2. Facebook's lid.176.bin language identification model

Usage:
    python scripts/setup_fasttext.py
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path


def print_step(message):
    """Print a step message."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def install_fasttext():
    """Install fasttext Python package."""
    print_step("Step 1: Installing fasttext Python package")
    
    try:
        import fasttext
        print("✓ fasttext already installed")
        return True
    except ImportError:
        print("Installing fasttext...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "fasttext"
            ])
            print("✓ fasttext installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install fasttext: {e}")
            return False


def download_model():
    """Download fastText lid.176.bin model."""
    print_step("Step 2: Downloading fastText language identification model")
    
    # Model details
    model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
    model_dir = Path.home() / ".fasttext"
    model_path = model_dir / "lid.176.bin"
    
    # Create directory
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    if model_path.exists():
        file_size = model_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ Model already exists at {model_path}")
        print(f"  Size: {file_size:.1f} MB")
        return True
    
    print(f"Downloading model from {model_url}")
    print(f"Destination: {model_path}")
    print("This may take a few minutes (model size: ~131 MB)...")
    
    try:
        # Download with progress
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end="")
        
        urllib.request.urlretrieve(model_url, model_path, reporthook=report_progress)
        print("\n✓ Model downloaded successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to download model: {e}")
        print("\nManual download instructions:")
        print(f"  mkdir -p {model_dir}")
        print(f"  wget -O {model_path} {model_url}")
        return False


def verify_installation():
    """Verify fastText installation and model."""
    print_step("Step 3: Verifying installation")
    
    try:
        import fasttext
        print("✓ fasttext package imported successfully")
        
        model_path = Path.home() / ".fasttext" / "lid.176.bin"
        if not model_path.exists():
            print(f"✗ Model not found at {model_path}")
            return False
        
        print(f"✓ Model found at {model_path}")
        
        # Try loading the model
        print("Loading model...")
        fasttext.FastText.eprint = lambda x: None  # Suppress warnings
        model = fasttext.load_model(str(model_path))
        print("✓ Model loaded successfully")
        
        # Test predictions
        print("\nTesting language detection:")
        test_cases = [
            ("मुझे दो पिज़्ज़ा चाहिए", "hi"),
            ("I want two pizzas", "en"),
            ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn"),
            ("मला दोन पिझ्झा हवे", "mr"),
            ("मुझे pizza चाहिए", "hi/en"),  # Hinglish
        ]
        
        for text, expected in test_cases:
            labels, scores = model.predict(text.lower(), k=1)
            detected = labels[0].replace("__label__", "")
            confidence = scores[0]
            print(f"  '{text[:30]}...' → {detected} ({confidence:.3f})")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("  fastText Language Detection Setup")
    print("="*60)
    
    # Step 1: Install package
    if not install_fasttext():
        print("\n✗ Setup failed at package installation")
        return 1
    
    # Step 2: Download model
    if not download_model():
        print("\n✗ Setup failed at model download")
        return 1
    
    # Step 3: Verify
    if not verify_installation():
        print("\n✗ Setup failed at verification")
        return 1
    
    # Success
    print_step("Setup Complete!")
    print("You can now use fastText language detection:")
    print("\n  from language.fasttext_detector import get_detector")
    print("  detector = get_detector()")
    print("  result = detector.detect_language('मुझे pizza चाहिए')")
    print("  print(result.lang, result.confidence)")
    print("\nModel location: ~/.fasttext/lid.176.bin")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
