# Complete Installation Guide - Ollama & fastText

## Quick Summary

**What you need to do manually:**
1. Install Ollama (5 minutes)
2. Install fastText (2 minutes - optional)

**What happens automatically:**
- Download Ollama model
- Download fastText model
- Verify everything works

---

## Part 1: Install Ollama (REQUIRED)

### Option A: Windows Installer (Recommended - 5 minutes)

1. **Download Ollama**
   - Visit: https://ollama.com/download/windows
   - Download `OllamaSetup.exe`
   - File size: ~500 MB

2. **Run Installer**
   - Double-click `OllamaSetup.exe`
   - Follow installation wizard
   - Ollama will install to: `C:\Users\<YourName>\AppData\Local\Programs\Ollama`

3. **Verify Installation**
   ```bash
   # Open new terminal (important - restart terminal!)
   ollama --version
   ```
   
   Expected output: `ollama version is 0.x.x`

4. **Ollama is now installed!** It runs as a background service automatically.

### Option B: Winget (If you have Windows Package Manager)

```bash
winget install Ollama.Ollama
```

### Option C: Chocolatey (If you have Chocolatey)

```bash
choco install ollama
```

---

## Part 2: Download Ollama Model (REQUIRED)

After installing Ollama, download a model:

### Recommended Models

**For Testing (Fast, Small):**
```bash
ollama pull phi3:latest
# Size: 2.2 GB
# Speed: Fast
# Accuracy: Good
```

**For Production (Better Accuracy):**
```bash
ollama pull llama3.1:8b
# Size: 4.7 GB
# Speed: Medium
# Accuracy: Excellent
```

**For Low Resources:**
```bash
ollama pull llama3.2:3b
# Size: 2 GB
# Speed: Very Fast
# Accuracy: Good
```

### Verify Model Downloaded

```bash
ollama list
```

You should see your model listed.

---

## Part 3: Install fastText (OPTIONAL - Improves Accuracy)

fastText improves language detection accuracy from 75% to 95%. The system works without it.

### Option A: Pre-built Wheel (Recommended for Windows)

```bash
pip install fasttext-wheel
```

This is a pre-compiled version that doesn't need C++ compiler.

### Option B: Official Package (Requires C++ Compiler)

**If you have Visual Studio Build Tools:**
```bash
pip install fasttext
```

**If you don't have Build Tools:**
1. Download Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++"
3. Restart terminal
4. Run: `pip install fasttext`

### Option C: Skip fastText

The system works without fastText using fallback language detection (75% accuracy).

---

## Part 4: Download fastText Model (If you installed fastText)

Run the automated script:

```bash
python scripts/setup_fasttext.py
```

Or manually:

```bash
# Create directory
mkdir %USERPROFILE%\.fasttext

# Download model (131 MB)
# Use browser or wget/curl
# URL: https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
# Save to: %USERPROFILE%\.fasttext\lid.176.bin
```

---

## Part 5: Verify Everything Works

Run the diagnostic:

```bash
python scripts/quick_diagnostic.py
```

Expected output:
```
✓ All directories present
✓ All files present
✓ All packages installed
✓ Ollama installed
✓ Ollama service running
✓ fastText installed (or ⚠ optional)
✓ All modules import successfully
```

---

## Part 6: Test the System

### Test 1: Run Integration Tests

```bash
pytest tests/test_system_integration.py -v
```

Expected: `21 passed`

### Test 2: Test Ollama

```bash
ollama run phi3:latest "Hello, how are you?"
```

Expected: Ollama responds with text

### Test 3: Test Language Detection

```bash
python -c "from language.hybrid_detector import get_hybrid_detector; d = get_hybrid_detector(); print(d.detect_from_text('मुझे pizza चाहिए'))"
```

Expected: Language detection result

### Test 4: Start API Server

```bash
python -m uvicorn api.main:app --reload --port 8080
```

Expected: Server starts on http://localhost:8080

### Test 5: Test API

```bash
curl http://localhost:8080/health
```

Expected: JSON response with system health

---

## Troubleshooting

### Issue: "ollama: command not found"

**Solution**: Restart your terminal after installing Ollama. Windows needs to refresh PATH.

### Issue: "Ollama service not running"

**Solution**: 
```bash
# Start Ollama manually
ollama serve
```

Or just run any ollama command - it auto-starts:
```bash
ollama list
```

### Issue: "fasttext won't install"

**Solution**: Use pre-built wheel:
```bash
pip install fasttext-wheel
```

Or skip it - system works without fastText.

### Issue: "Model download is slow"

**Solution**: Models are large (2-5 GB). Download time depends on internet speed. Be patient.

### Issue: "Out of memory when running model"

**Solution**: Use smaller model:
```bash
ollama pull llama3.2:3b  # Only 2 GB
```

---

## Quick Start After Installation

```bash
# 1. Verify everything
python scripts/quick_diagnostic.py

# 2. Run tests
pytest tests/test_system_integration.py -v

# 3. Start API
python -m uvicorn api.main:app --reload --port 8080

# 4. Test API
curl http://localhost:8080/health
```

---

## What Each Component Does

### Ollama
- **Purpose**: Runs LLM models locally
- **Required**: YES (for LLM functionality)
- **Size**: ~500 MB installer + 2-5 GB model
- **Usage**: Processes user utterances, extracts intents

### fastText
- **Purpose**: Accurate language detection
- **Required**: NO (system has fallback)
- **Size**: ~10 MB package + 131 MB model
- **Usage**: Detects Hindi, English, Kannada, Marathi, Hinglish

---

## Installation Time Estimates

| Task | Time | Size |
|------|------|------|
| Download Ollama installer | 2-5 min | 500 MB |
| Install Ollama | 1 min | - |
| Download Ollama model | 5-15 min | 2-5 GB |
| Install fastText | 1 min | 10 MB |
| Download fastText model | 2-5 min | 131 MB |
| **Total** | **15-30 min** | **2.6-5.6 GB** |

---

## Alternative: Use Ollama Without Installation

If you can't install Ollama locally, you can use:

1. **Ollama Cloud** (when available)
2. **OpenAI API** (modify LLM processor)
3. **HuggingFace API** (already supported as fallback)

To use HuggingFace instead:
```python
# In config/config.py
hf_api_key = "your_huggingface_api_key"
```

---

## Next Steps After Installation

1. ✅ Ollama installed and model downloaded
2. ✅ fastText installed (optional)
3. ✅ All tests passing
4. 🚀 **Ready to use the system!**

Run the API:
```bash
python -m uvicorn api.main:app --reload --port 8080
```

Visit: http://localhost:8080/docs for API documentation

---

## Support

If you encounter issues:

1. Check diagnostic: `python scripts/quick_diagnostic.py`
2. Check logs in terminal
3. Verify Ollama is running: `ollama list`
4. Restart terminal and try again

---

**Installation complete! Your Voice Order System is ready to use.**
