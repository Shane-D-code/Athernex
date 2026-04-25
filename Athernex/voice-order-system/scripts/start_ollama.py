"""
Startup script for Ollama server with model management.

Ensures Ollama is running and the specified model is available.
Handles model pulling and server startup.

Usage:
    python scripts/start_ollama.py
    python scripts/start_ollama.py --model llama3.1:8b-instruct-q4_K_M
"""

import subprocess
import sys
import argparse
import time
import httpx


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {result.stdout.strip()}")
            return True
        else:
            print("[ERROR] Ollama not found")
            return False
    except FileNotFoundError:
        print("[ERROR] Ollama not installed. Download from: https://ollama.ai/")
        return False


def check_server_running():
    """Check if Ollama server is already running."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def start_server():
    """Start Ollama server in background."""
    print("[INFO] Starting Ollama server...")
    try:
        # Start server in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for server to be ready
        for i in range(30):  # 30 second timeout
            if check_server_running():
                print("[OK] Ollama server is running")
                return True
            time.sleep(1)
        
        print("[ERROR] Server failed to start within 30 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        return False


def check_model_available(model: str):
    """Check if model is already pulled."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for m in models:
                if m.get("name") == model:
                    size_gb = m.get("size", 0) / (1024**3)
                    print(f"[OK] Model '{model}' available ({size_gb:.1f}GB)")
                    return True
        return False
    except Exception:
        return False


def pull_model(model: str):
    """Pull the specified model."""
    print(f"[INFO] Pulling model '{model}' (this may take several minutes)...")
    try:
        result = subprocess.run(["ollama", "pull", model], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Model '{model}' pulled successfully")
            return True
        else:
            print(f"[ERROR] Failed to pull model: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to pull model: {e}")
        return False


def test_model(model: str):
    """Test the model with a simple prompt."""
    print(f"[INFO] Testing model '{model}'...")
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hello in JSON format"}],
            "stream": False,
            "format": "json"
        }
        
        response = httpx.post("http://localhost:11434/api/chat", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            print(f"[OK] Model test successful: {content[:50]}...")
            return True
        else:
            print(f"[ERROR] Model test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Model test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Start Ollama server with model")
    parser.add_argument("--model", default="phi3:latest", help="Model to use (default: phi3:latest)")
    parser.add_argument("--no-test", action="store_true", help="Skip model testing")
    args = parser.parse_args()

    print(f"\n[INFO] Setting up Ollama with model: {args.model}")

    # Check installation
    if not check_ollama_installed():
        sys.exit(1)

    # Start server if not running
    if not check_server_running():
        if not start_server():
            sys.exit(1)
    else:
        print("[OK] Ollama server already running")

    # Check/pull model
    if not check_model_available(args.model):
        if not pull_model(args.model):
            sys.exit(1)

    # Test model
    if not args.no_test:
        if not test_model(args.model):
            print("[WARNING] Model test failed, but server is running")

    print(f"\n[SUCCESS] Ollama ready with model '{args.model}'")
    print("  Server: http://localhost:11434")
    print("  API: http://localhost:11434/api/chat")


if __name__ == "__main__":
    main()