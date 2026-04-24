"""Hardware validation script for voice order system."""

import sys
import platform
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check Python version (requires 3.8+)."""
    print("=" * 60)
    print("PYTHON VERSION CHECK")
    print("=" * 60)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8+ required")
        return False
    
    print("✅ Python version OK")
    return True


def check_nvidia_gpu():
    """Check NVIDIA GPU availability and VRAM."""
    print("\n" + "=" * 60)
    print("NVIDIA GPU CHECK")
    print("=" * 60)
    
    # Check if nvidia-smi is available
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        print("❌ ERROR: nvidia-smi not found")
        print("   NVIDIA drivers may not be installed")
        return False
    
    try:
        # Run nvidia-smi to get GPU info
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,cuda_version", 
             "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True
        )
        
        gpu_info = result.stdout.strip().split(", ")
        if len(gpu_info) >= 4:
            gpu_name = gpu_info[0]
            vram_total = gpu_info[1]
            driver_version = gpu_info[2]
            cuda_version = gpu_info[3]
            
            print(f"GPU Name: {gpu_name}")
            print(f"VRAM Total: {vram_total}")
            print(f"Driver Version: {driver_version}")
            print(f"CUDA Version: {cuda_version}")
            
            # Extract VRAM in MB
            vram_mb = int(vram_total.split()[0])
            
            if vram_mb < 8000:
                print(f"⚠️  WARNING: VRAM ({vram_mb}MB) < 8GB")
                print("   Consider using smaller models or CPU fallback")
                return False
            
            print(f"✅ GPU OK: {vram_mb}MB VRAM available")
            
            # Check CUDA version
            cuda_major = int(cuda_version.split(".")[0]) if cuda_version != "N/A" else 0
            if cuda_major < 12:
                print(f"⚠️  WARNING: CUDA {cuda_version} < 12.1")
                print("   Recommend upgrading to CUDA 12.1+ for RTX 4060")
            else:
                print(f"✅ CUDA version OK: {cuda_version}")
            
            return True
        else:
            print("❌ ERROR: Could not parse GPU info")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: nvidia-smi failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def check_system_resources():
    """Check CPU and RAM."""
    print("\n" + "=" * 60)
    print("SYSTEM RESOURCES CHECK")
    print("=" * 60)
    
    # CPU info
    cpu_count = platform.processor()
    print(f"CPU: {cpu_count}")
    
    # RAM info (Windows-specific)
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"RAM: {ram_gb:.1f} GB")
        
        if ram_gb < 16:
            print("⚠️  WARNING: RAM < 16GB")
            print("   System may experience memory pressure")
        else:
            print("✅ RAM OK")
            
    except ImportError:
        print("⚠️  psutil not installed, skipping RAM check")
        print("   Install with: pip install psutil")


def check_disk_space():
    """Check available disk space for models."""
    print("\n" + "=" * 60)
    print("DISK SPACE CHECK")
    print("=" * 60)
    
    try:
        import psutil
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        
        print(f"Free disk space: {free_gb:.1f} GB")
        
        if free_gb < 10:
            print("❌ ERROR: Less than 10GB free space")
            print("   Need ~10GB for models (Whisper + LLaMA + Piper)")
            return False
        
        print("✅ Disk space OK")
        return True
        
    except ImportError:
        print("⚠️  psutil not installed, skipping disk check")
        return True


def generate_recommendations(gpu_ok, vram_mb=0):
    """Generate hardware-specific recommendations."""
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if not gpu_ok:
        print("\n🔴 GPU NOT AVAILABLE - CPU-ONLY MODE")
        print("   - Use Whisper Small model (faster on CPU)")
        print("   - Use LLaMA 3.1 8B with CPU inference")
        print("   - Expected latency: 5-10 seconds")
        print("   - Install: pip install torch --index-url https://download.pytorch.org/whl/cpu")
        return
    
    if vram_mb >= 8000:
        print("\n🟢 OPTIMAL CONFIGURATION (8GB VRAM)")
        print("   - Whisper Medium model (2GB VRAM)")
        print("   - LLaMA 3.1 8B Q4_K_M quantized (5GB VRAM)")
        print("   - Total VRAM usage: ~7GB")
        print("   - Expected latency: 2-3 seconds p95")
        print("\n   Installation commands:")
        print("   1. Install CUDA 12.1+: https://developer.nvidia.com/cuda-downloads")
        print("   2. Install cuDNN 8.9+: https://developer.nvidia.com/cudnn")
        print("   3. pip install torch --index-url https://download.pytorch.org/whl/cu121")
        print("   4. Install faster-whisper-server")
        print("   5. Install Ollama and pull llama3.1:8b-instruct-q4_K_M")
    else:
        print(f"\n🟡 LIMITED VRAM ({vram_mb}MB)")
        print("   - Use Whisper Small model (1GB VRAM)")
        print("   - Use LLaMA 3.1 8B Q3_K_M (more quantized, 4GB VRAM)")
        print("   - Expected latency: 3-5 seconds p95")


def main():
    """Run all hardware validation checks."""
    print("\n" + "=" * 60)
    print("VOICE ORDER SYSTEM - HARDWARE VALIDATION")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    
    # Run checks
    python_ok = check_python_version()
    gpu_ok = check_nvidia_gpu()
    check_system_resources()
    disk_ok = check_disk_space()
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Python 3.8+:     {'✅ PASS' if python_ok else '❌ FAIL'}")
    print(f"NVIDIA GPU:      {'✅ PASS' if gpu_ok else '❌ FAIL'}")
    print(f"Disk Space:      {'✅ PASS' if disk_ok else '❌ FAIL'}")
    
    # Generate recommendations
    generate_recommendations(gpu_ok)
    
    # Exit code
    if python_ok and disk_ok:
        print("\n✅ System ready for installation!")
        print("   (GPU recommended but not required)")
        sys.exit(0)
    else:
        print("\n❌ System requirements not met")
        sys.exit(1)


if __name__ == "__main__":
    main()
