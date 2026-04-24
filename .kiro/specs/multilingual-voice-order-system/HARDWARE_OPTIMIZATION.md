# Hardware Optimization Guide for RTX 4060 8GB

## Your Hardware Configuration

**Predator Helios Neo 16:**
- **GPU:** NVIDIA GeForce RTX 4060 8GB VRAM ✅
- **CPU:** Intel i7-14700HX (20 cores, 28 threads) ✅
- **RAM:** 16GB DDR5 ✅
- **Status:** Sufficient for development and small-scale deployment

## Optimized Model Configuration

### What Fits in 8GB VRAM

| Component | Model | VRAM Usage | Storage | Notes |
|-----------|-------|------------|---------|-------|
| **STT** | Whisper Medium | ~2GB | 1.5GB | Recommended (3x faster than Large) |
| **LLM** | LLaMA 3.1 8B Q4_K_M | ~5GB | 4.7GB | 4-bit quantized (50% VRAM reduction) |
| **TTS** | Piper TTS | CPU-only | 100MB | Ultra-fast (50-150ms) |
| **Total** | - | **~7GB** | **~6.3GB** | ✅ Fits with 1GB headroom |

### Alternative: Higher Accuracy (Tight Fit)

| Component | Model | VRAM Usage | Storage | Notes |
|-----------|-------|------------|---------|-------|
| **STT** | Whisper Large-v3 | ~4GB | 2.9GB | Better accuracy (+2-3% WER) |
| **LLM** | LLaMA 3.1 8B Q4_K_M | ~5GB | 4.7GB | Same as above |
| **Total** | - | **~9GB** | **~7.6GB** | ⚠️ Requires sequential processing |

**Recommendation:** Start with Whisper Medium. Upgrade to Large-v3 only if accuracy is insufficient.

## Installation Commands

### 1. Install CUDA 12.1+ and cuDNN 8.9+

```bash
# Check current CUDA version
nvidia-smi

# If CUDA < 12.1, download from:
# https://developer.nvidia.com/cuda-downloads

# Install cuDNN 8.9+ from:
# https://developer.nvidia.com/cudnn
```

### 2. Install faster-whisper-server (Whisper Medium)

```bash
pip install faster-whisper-server

# Start server with Whisper Medium
faster-whisper-server \
  --model medium \
  --device cuda \
  --compute_type float16 \
  --port 8000
```

### 3. Install Ollama (LLaMA 3.1 8B Q4)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull 4-bit quantized model (optimized for 8GB VRAM)
ollama pull llama3.1:8b-instruct-q4_K_M

# Verify it's running
ollama list
```

### 4. Install Piper TTS

```bash
pip install piper-tts

# Download Indian language models
piper --download-dir ./models --model hi_IN-medium
piper --download-dir ./models --model en_IN-medium
```

## VRAM Monitoring

### Check VRAM Usage

```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Or use Python
python -c "import torch; print(f'VRAM: {torch.cuda.memory_allocated()/1e9:.2f}GB / {torch.cuda.get_device_properties(0).total_memory/1e9:.2f}GB')"
```

### Expected VRAM Usage

- **Idle:** ~500MB (CUDA overhead)
- **Whisper Medium loading:** +1.5GB → ~2GB total
- **LLaMA 8B Q4 loading:** +5GB → ~7GB total
- **During inference:** ~7-7.5GB (safe zone)

**Warning:** If VRAM exceeds 7.5GB, you may experience:
- Slower inference (GPU swapping to system RAM)
- Out-of-memory (OOM) errors
- System instability

## Performance Expectations

### Latency Targets (RTX 4060 8GB)

| Component | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| Whisper Medium | 200ms | 500ms | 800ms |
| LLaMA 8B Q4 | 600ms | 1500ms | 2500ms |
| Piper TTS | 75ms | 150ms | 200ms |
| **Total Pipeline** | 875ms | 2150ms | 3500ms |

**Note:** These are realistic targets for your hardware. Cloud APIs would be faster (500-1000ms) but cost $1000+/month.

### Throughput

- **Sequential processing:** 5-10 requests/minute
- **Concurrent capacity:** 1-2 simultaneous users (limited by VRAM)
- **Best for:** Development, testing, demos, small-scale deployment (<50 users)

## Optimization Tips

### 1. Reduce Batch Size
```python
# In Whisper config
batch_size = 1  # Process one utterance at a time
```

### 2. Enable Gradient Checkpointing (if training)
```python
# Not needed for inference-only deployment
```

### 3. Use Mixed Precision (FP16)
```python
# Already enabled in faster-whisper with compute_type=float16
```

### 4. Cache Aggressively
```python
# Cache LLM responses (1000 entries)
# Cache TTS audio (500 entries)
# Expected cache hit rate: 30-50%
# Latency reduction: 50% on cache hits
```

### 5. Monitor and Alert
```python
# Set up alerts when VRAM > 7GB
if torch.cuda.memory_allocated() > 7e9:
    logger.warning("VRAM usage high, consider reducing load")
```

## Troubleshooting

### OOM (Out of Memory) Errors

**Symptom:** `RuntimeError: CUDA out of memory`

**Solutions:**
1. Reduce to Whisper Small (1GB VRAM) instead of Medium
2. Use LLaMA 3.1 8B Q3_K_M (even more quantized, ~4GB VRAM)
3. Process requests sequentially (no parallel inference)
4. Restart services to clear VRAM fragmentation

### Slow Inference

**Symptom:** Latency > 5 seconds

**Solutions:**
1. Verify GPU is being used: `nvidia-smi` should show processes
2. Check CUDA version: `nvcc --version` (should be 12.1+)
3. Verify quantization: `ollama show llama3.1:8b-instruct-q4_K_M`
4. Monitor CPU usage: High CPU = GPU not being utilized

### CUDA Errors

**Symptom:** `CUDA error: device-side assert triggered`

**Solutions:**
1. Update NVIDIA drivers to latest version
2. Reinstall CUDA 12.1+
3. Check GPU temperature: `nvidia-smi` (should be <85°C)
4. Run GPU stress test to verify hardware stability

## Scaling Path

### When to Upgrade

**Upgrade to 12GB VRAM (RTX 4070 Ti) when:**
- Need Whisper Large-v3 for better accuracy
- Need to support 5+ concurrent users
- Need faster inference (<1s p95)

**Upgrade to 16GB+ VRAM (RTX 4080) when:**
- Need LLaMA 3.1 8B FP16 (no quantization)
- Need to support 10+ concurrent users
- Need production-grade latency (<800ms p95)

**Upgrade to 24GB+ VRAM (RTX 4090) when:**
- Need LLaMA 3.1 70B for highest accuracy
- Need to support 50+ concurrent users
- Need enterprise-grade deployment

## Cost Analysis

**Your Current Setup (RTX 4060 8GB):**
- Hardware cost: $0 (already owned)
- Electricity: ~$10-20/month (if running 24/7)
- **Total Year 1:** $120-240

**Cloud API Alternative:**
- Sarvam AI STT: $60/month
- GPT-4 Turbo: $1000/month
- ElevenLabs TTS: $60/month
- **Total Year 1:** $13,440

**Savings:** $13,200/year by using your existing hardware!

## Summary

✅ **Your RTX 4060 8GB is sufficient** for this project with optimizations
✅ **Use Whisper Medium + LLaMA 8B Q4** for best balance of accuracy and performance
✅ **Expected latency: 2-3 seconds p95** (acceptable for voice systems)
✅ **Supports 5-10 concurrent requests** (good for development and small deployments)
✅ **Zero API costs** - all models run locally

**Next Steps:**
1. Install CUDA 12.1+ and cuDNN 8.9+
2. Set up faster-whisper-server with Medium model
3. Set up Ollama with LLaMA 3.1 8B Q4_K_M
4. Monitor VRAM usage and optimize as needed
