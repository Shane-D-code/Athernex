"""
Startup script for faster-whisper-server with GPU acceleration.
Runs Whisper Medium on port 8000 with CUDA support.

Usage:
    python scripts/start_whisper.py
    python scripts/start_whisper.py --model large-v3 --port 8000
"""

import subprocess
import sys
import argparse
import time
import httpx


def check_gpu():
    """Check if GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory // (1024 ** 2)
            print(f"[GPU] {name} ({vram}MB VRAM) - CUDA {torch.version.cuda}")
            return True
        else:
            print("[WARNING] No CUDA GPU found, falling back to CPU")
            return False
    except ImportError:
        print("[WARNING] PyTorch not installed, cannot check GPU")
        return False


def wait_for_server(url: str, timeout: int = 60) -> bool:
    """Poll until the server is ready or timeout."""
    print(f"[INFO] Waiting for server at {url} ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                print(f"[OK] Server is ready at {url}")
                return True
        except Exception:
            pass
        time.sleep(2)
    print(f"[ERROR] Server did not start within {timeout}s")
    return False


def main():
    parser = argparse.ArgumentParser(description="Start faster-whisper-server")
    parser.add_argument("--model", default="medium", help="Whisper model size (default: medium)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for server to be ready")
    args = parser.parse_args()

    use_gpu = check_gpu()
    device = "cuda" if use_gpu else "cpu"
    compute_type = "float16" if use_gpu else "int8"

    print(f"\n[INFO] Starting faster-whisper-server")
    print(f"  Model:        Whisper {args.model}")
    print(f"  Device:       {device} ({compute_type})")
    print(f"  Endpoint:     http://{args.host}:{args.port}")
    print(f"  VRAM budget:  ~2GB for Whisper {args.model}\n")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "faster_whisper_server.main:app",
        "--host", args.host,
        "--port", str(args.port),
        "--log-level", "info",
    ]

    env_vars = {
        "WHISPER_MODEL": args.model,
        "WHISPER_DEVICE": device,
        "WHISPER_COMPUTE_TYPE": compute_type,
        "WHISPER_WORD_TIMESTAMPS": "true",
        "WHISPER_LANGUAGE": "auto",
    }

    import os
    env = {**os.environ, **env_vars}

    print(f"[CMD] {' '.join(cmd)}")
    print("[INFO] Press Ctrl+C to stop\n")

    try:
        proc = subprocess.Popen(cmd, env=env)
        if not args.no_wait:
            ready = wait_for_server(f"http://localhost:{args.port}")
            if not ready:
                proc.terminate()
                sys.exit(1)
        proc.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        proc.terminate()


if __name__ == "__main__":
    main()
