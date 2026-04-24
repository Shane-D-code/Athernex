"""
Complete setup script for Ollama and fastText.

This script will:
1. Check if Ollama is installed
2. Guide you through Ollama installation
3. Install fastText (with Windows workarounds)
4. Download fastText model
5. Verify everything works

Usage:
    python scripts/setup_ollama_and_fasttext.py
"""

import sys
import os
import subprocess
import platform
import urllib.request
from pathlib import Path
import webbrowser


def print_header(title):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(step_num, title):
    """Print step header."""
    print(f"\n{'─'*80}")
    print(f"STEP {step_num}: {title}")
    print(f"{'─'*80}\n")


def check_ollama():
    """Check if Ollama is installed."""
    print_step(1, "Checking Ollama Installation")
    
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Ollama is installed: {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("✗ Ollama is NOT installed")
    return False


def install_ollama_guide():
    """Guide user through Ollama installation."""
    print_step(2, "Installing Ollama")
    
    system = platform.system()
    
    if system == "Windows":
        print("Ollama Installation for Windows:")
        print("\nOption 1: Download Installer (Recommended)")
        print("  1. Visit: https://ollama.com/download/windows")
        print("  2. Download OllamaSetup.exe")
        print("  3. Run the installer")
        print("  4. Restart this script after installation")
        
        print("\nOption 2: Use Winget")
        print("  winget install Ollama.Ollama")
        
        print("\nOption 3: Use Chocolatey")
        print("  choco install ollama")
        
        choice = input("\nWould you like to open the download page? (y/n): ").lower()
        if choice == 'y':
            webbrowser.open("https://ollama.com/download/windows")
            print("\n✓ Opened download page in browser")
            print("Please install Ollama and restart this script.")
            return False
    
    elif system == "Linux":
        print("Ollama Installation for Linux:")
        print("\nRun this command:")
        print("  curl -fsSL https://ollama.com/install.sh | sh")
        
        choice = input("\nWould you like to run the installation now? (y/n): ").lower()
        if choice == 'y':
            try:
                subprocess.run(
                    "curl -fsSL https://ollama.com/install.sh | sh",
                    shell=True,
                    check=True
                )
                print("✓ Ollama installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("✗ Installation failed")
                return False
    
    elif system == "Darwin":  # macOS
        print("Ollama Installation for macOS:")
        print("\nOption 1: Download Installer")
        print("  Visit: https://ollama.com/download/mac")
        
        print("\nOption 2: Use Homebrew")
        print("  brew install ollama")
        
        choice = input("\nWould you like to open the download page? (y/n): ").lower()
        if choice == 'y':
            webbrowser.open("https://ollama.com/download/mac")
            return False
    
    print("\n⚠ Please install Ollama manually and restart this script.")
    return False


def start_ollama():
    """Start Ollama service."""
    print_step(3, "Starting Ollama Service")
    
    system = platform.system()
    
    if system == "Windows":
        print("On Windows, Ollama runs as a background service.")
        print("It should start automatically after installation.")
        print("\nTo manually start Ollama:")
        print("  1. Open a new terminal")
        print("  2. Run: ollama serve")
        print("\nOr just run any ollama command to start it automatically.")
        
        # Try to start it
        try:
            print("\nAttempting to start Ollama...")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if system == "Windows" else 0
            )
            print("✓ Ollama service started in background")
            return True
        except Exception as e:
            print(f"⚠ Could not start automatically: {e}")
            print("Please start Ollama manually: ollama serve")
            return False
    
    else:
        print("Starting Ollama service...")
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✓ Ollama service started")
            return True
        except Exception as e:
            print(f"✗ Failed to start: {e}")
            return False


def download_ollama_model():
    """Download a recommended Ollama model."""
    print_step(4, "Downloading Ollama Model")
    
    print("Recommended models for voice ordering:")
    print("  1. phi3:latest (2.2GB) - Fast, good for testing")
    print("  2. llama3.1:8b (4.7GB) - Better accuracy")
    print("  3. llama3.2:3b (2GB) - Smallest, fastest")
    
    choice = input("\nWhich model would you like? (1/2/3 or skip): ").strip()
    
    models = {
        "1": "phi3:latest",
        "2": "llama3.1:8b",
        "3": "llama3.2:3b"
    }
    
    if choice in models:
        model = models[choice]
        print(f"\nDownloading {model}...")
        print("This may take several minutes depending on your internet speed.")
        
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                check=True,
                text=True
            )
            print(f"✓ Model {model} downloaded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to download model: {e}")
            return False
    else:
        print("Skipped model download. You can download later with:")
        print("  ollama pull phi3:latest")
        return False


def install_fasttext():
    """Install fastText with Windows workarounds."""
    print_step(5, "Installing fastText")
    
    # Check if already installed
    try:
        import fasttext
        print("✓ fastText is already installed")
        return True
    except ImportError:
        pass
    
    system = platform.system()
    
    if system == "Windows":
        print("fastText on Windows requires C++ compiler.")
        print("\nOption 1: Install pre-built wheel (Recommended)")
        print("  pip install fasttext-wheel")
        
        print("\nOption 2: Install from unofficial binaries")
        print("  Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#fasttext")
        print("  Download the .whl file for your Python version")
        print("  pip install downloaded_file.whl")
        
        print("\nOption 3: Install Visual Studio Build Tools")
        print("  1. Download: https://visualstudio.microsoft.com/downloads/")
        print("  2. Install 'Desktop development with C++'")
        print("  3. pip install fasttext")
        
        print("\nOption 4: Skip fastText (system works without it)")
        print("  The system uses fallback language detection (75% accuracy)")
        
        choice = input("\nChoose option (1/2/3/4): ").strip()
        
        if choice == "1":
            print("\nInstalling fasttext-wheel...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "fasttext-wheel"],
                    check=True
                )
                print("✓ fasttext-wheel installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("✗ Installation failed")
                print("Try option 2 or 4")
                return False
        
        elif choice == "2":
            webbrowser.open("https://www.lfd.uci.edu/~gohlke/pythonlibs/#fasttext")
            print("\n✓ Opened download page")
            print("After downloading, run:")
            print("  pip install path/to/downloaded_file.whl")
            return False
        
        elif choice == "3":
            webbrowser.open("https://visualstudio.microsoft.com/downloads/")
            print("\n✓ Opened Visual Studio download page")
            print("After installing Build Tools, run:")
            print("  pip install fasttext")
            return False
        
        else:
            print("\n⚠ Skipping fastText installation")
            print("System will use fallback language detection")
            return False
    
    else:
        # Linux/Mac - should work directly
        print("Installing fastText...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "fasttext"],
                check=True
            )
            print("✓ fastText installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Installation failed")
            return False


def download_fasttext_model():
    """Download fastText language identification model."""
    print_step(6, "Downloading fastText Model")
    
    model_dir = Path.home() / ".fasttext"
    model_path = model_dir / "lid.176.bin"
    
    # Check if already exists
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✓ Model already exists ({size_mb:.1f} MB)")
        return True
    
    # Create directory
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading fastText model to {model_path}")
    print("Size: ~131 MB")
    print("This may take a few minutes...")
    
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
        print("\nManual download:")
        print(f"  wget -O {model_path} {url}")
        return False


def verify_installation():
    """Verify all installations."""
    print_step(7, "Verifying Installation")
    
    all_good = True
    
    # Check Ollama
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ Ollama is working")
        else:
            print("✗ Ollama not working")
            all_good = False
    except:
        print("✗ Ollama not found")
        all_good = False
    
    # Check Ollama service
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✓ Ollama service running ({len(models)} models)")
        else:
            print("⚠ Ollama service not responding")
            print("  Start with: ollama serve")
    except:
        print("⚠ Ollama service not running")
        print("  Start with: ollama serve")
    
    # Check fastText
    try:
        import fasttext
        print("✓ fastText package installed")
        
        model_path = Path.home() / ".fasttext" / "lid.176.bin"
        if model_path.exists():
            print("✓ fastText model downloaded")
            
            # Test it
            fasttext.FastText.eprint = lambda x: None
            model = fasttext.load_model(str(model_path))
            labels, scores = model.predict("test", k=1)
            print("✓ fastText model working")
        else:
            print("✗ fastText model not found")
            all_good = False
    except ImportError:
        print("⚠ fastText not installed (optional)")
        print("  System will use fallback language detection")
    except Exception as e:
        print(f"⚠ fastText error: {e}")
    
    return all_good


def main():
    """Main setup function."""
    print_header("OLLAMA AND FASTTEXT SETUP")
    
    print("This script will help you install:")
    print("  1. Ollama (LLM service) - REQUIRED")
    print("  2. fastText (language detection) - OPTIONAL")
    print()
    
    # Step 1: Check Ollama
    ollama_installed = check_ollama()
    
    # Step 2: Install Ollama if needed
    if not ollama_installed:
        if not install_ollama_guide():
            print("\n" + "="*80)
            print("SETUP PAUSED")
            print("="*80)
            print("\nPlease install Ollama and run this script again:")
            print("  python scripts/setup_ollama_and_fasttext.py")
            return 1
        
        # Recheck
        ollama_installed = check_ollama()
        if not ollama_installed:
            print("\n✗ Ollama still not detected")
            print("Please restart your terminal and run this script again.")
            return 1
    
    # Step 3: Start Ollama
    start_ollama()
    
    # Step 4: Download model
    download_ollama_model()
    
    # Step 5: Install fastText
    fasttext_installed = install_fasttext()
    
    # Step 6: Download fastText model
    if fasttext_installed:
        download_fasttext_model()
    
    # Step 7: Verify
    verify_installation()
    
    # Final summary
    print_header("SETUP COMPLETE")
    
    print("Next steps:")
    print("  1. Verify installation: python scripts/quick_diagnostic.py")
    print("  2. Run tests: pytest tests/test_system_integration.py -v")
    print("  3. Start API: python -m uvicorn api.main:app --reload")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
