"""
Post-Installation Setup Script

Run this AFTER you've manually installed Ollama.

This script will:
1. Verify Ollama is installed
2. Download recommended Ollama model
3. Install fastText (optional)
4. Download fastText model
5. Run final verification

Usage:
    python scripts/post_install_setup.py
"""

import sys
import subprocess
import urllib.request
from pathlib import Path


def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def check_ollama():
    """Check if Ollama is installed."""
    print("Checking Ollama installation...")
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Ollama is installed: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("✗ Ollama is NOT installed")
    print("\nPlease install Ollama first:")
    print("  1. Visit: https://ollama.com/download/windows")
    print("  2. Download and run OllamaSetup.exe")
    print("  3. Restart terminal")
    print("  4. Run this script again")
    return False


def download_ollama_model():
    """Download Ollama model."""
    print_header("Downloading Ollama Model")
    
    # Check what models are already downloaded
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print("Current models:")
            print(result.stdout)
            
            choice = input("\nDownload another model? (y/n): ").lower()
            if choice != 'y':
                print("Skipping model download")
                return True
    except:
        pass
    
    print("\nRecommended models:")
    print("  1. phi3:latest (2.2GB) - Fast, good for testing")
    print("  2. llama3.2:3b (2GB) - Smallest, fastest")
    print("  3. llama3.1:8b (4.7GB) - Best accuracy")
    
    choice = input("\nSelect model (1/2/3 or skip): ").strip()
    
    models = {
        "1": "phi3:latest",
        "2": "llama3.2:3b",
        "3": "llama3.1:8b"
    }
    
    if choice in models:
        model = models[choice]
        print(f"\nDownloading {model}...")
        print("This may take 5-15 minutes depending on your internet speed.")
        print("Please wait...\n")
        
        try:
            subprocess.run(
                ["ollama", "pull", model],
                check=True
            )
            print(f"\n✓ Model {model} downloaded successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"\n✗ Failed to download model")
            return False
    else:
        print("\nSkipped. You can download later with:")
        print("  ollama pull phi3:latest")
        return True


def install_fasttext():
    """Install fastText."""
    print_header("Installing fastText (Optional)")
    
    # Check if already installed
    try:
        import fasttext
        print("✓ fastText is already installed")
        return True
    except ImportError:
        pass
    
    print("fastText improves language detection accuracy (75% → 95%)")
    print("The system works without it using fallback detection.")
    
    choice = input("\nInstall fastText? (y/n): ").lower()
    
    if choice != 'y':
        print("Skipped. System will use fallback language detection.")
        return False
    
    print("\nAttempting to install fasttext-wheel (pre-built)...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "fasttext-wheel"],
            check=True
        )
        print("✓ fasttext-wheel installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ fasttext-wheel installation failed")
        print("\nTrying official fasttext package...")
        
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "fasttext"],
                check=True
            )
            print("✓ fasttext installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ fasttext installation failed")
            print("\nfastText requires C++ compiler on Windows.")
            print("System will use fallback language detection (75% accuracy).")
            return False


def download_fasttext_model():
    """Download fastText model."""
    print_header("Downloading fastText Model")
    
    # Check if fasttext is installed
    try:
        import fasttext
    except ImportError:
        print("fastText not installed, skipping model download")
        return False
    
    model_dir = Path.home() / ".fasttext"
    model_path = model_dir / "lid.176.bin"
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ Model already exists ({size_mb:.1f} MB)")
        return True
    
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading fastText model...")
    print("Size: ~131 MB")
    print("This may take 2-5 minutes...\n")
    
    url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
    
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end="")
        
        urllib.request.urlretrieve(url, model_path, reporthook=report_progress)
        print("\n✓ Model downloaded successfully")
        return True
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False


def run_verification():
    """Run final verification."""
    print_header("Final Verification")
    
    print("Running diagnostic...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/quick_diagnostic.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(result.stdout)
        
        if "✗" in result.stdout:
            print("\n⚠ Some checks failed. Review output above.")
        else:
            print("\n✓ All checks passed!")
    except Exception as e:
        print(f"Could not run diagnostic: {e}")
        print("Run manually: python scripts/quick_diagnostic.py")


def main():
    """Main setup function."""
    print_header("POST-INSTALLATION SETUP")
    
    print("This script will complete the setup after Ollama installation.")
    print()
    
    # Step 1: Check Ollama
    if not check_ollama():
        return 1
    
    # Step 2: Download Ollama model
    download_ollama_model()
    
    # Step 3: Install fastText
    fasttext_installed = install_fasttext()
    
    # Step 4: Download fastText model
    if fasttext_installed:
        download_fasttext_model()
    
    # Step 5: Verify
    run_verification()
    
    # Final message
    print_header("SETUP COMPLETE")
    
    print("✓ Setup finished!")
    print("\nNext steps:")
    print("  1. Run tests: pytest tests/test_system_integration.py -v")
    print("  2. Start API: python -m uvicorn api.main:app --reload")
    print("  3. Visit: http://localhost:8080/docs")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled")
        sys.exit(1)
