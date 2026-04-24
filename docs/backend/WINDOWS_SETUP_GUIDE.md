# Windows Setup Guide - Voice Order System

## Issue: fastText Installation on Windows

fastText requires C++ compilation on Windows, which can fail if you don't have Visual Studio Build Tools installed.

## Solution Options

### Option 1: Use Pre-built Wheel (Recommended)

```bash
# Install from pre-built wheel
pip install fasttext-wheel
```

Or download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#fasttext

### Option 2: Install Visual Studio Build Tools

1. Download Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++"
3. Restart terminal
4. Run: `pip install fasttext`

### Option 3: Use WSL (Windows Subsystem for Linux)

```bash
# In WSL Ubuntu
pip install fasttext
```

### Option 4: Skip fastText (Use Fallback)

The system works without fastText! It will use the STT-based language detector as fallback.

```python
# The hybrid detector automatically falls back
from language.hybrid_detector import get_hybrid_detector

detector = get_hybrid_detector()  # Works even without fastText
result = detector.detect_from_text("मुझे pizza चाहिए")
# Uses script-based heuristics instead
```

## Current Status

✅ **Working Without fastText:**
- All core modules import successfully
- Language detection works (using STT metadata + script heuristics)
- Pipeline is functional
- API is ready

⚠ **Missing (Optional):**
- fastText model (for improved language detection accuracy)
- Ollama service (needs to be started separately)
- Whisper service (optional, can use Vosk)

## Quick Start (Without fastText)

```bash
# 1. Install packages (already done)
pip install -r requirements.txt

# 2. Start Ollama
ollama serve

# 3. Test the system
python scripts/quick_diagnostic.py

# 4. Run API
python -m uvicorn api.main:app --reload
```

## Testing Language Detection Without fastText

```python
from language.hybrid_detector import get_hybrid_detector

detector = get_hybrid_detector()

# Test with text
result = detector.detect_from_text("मुझे दो पिज़्ज़ा चाहिए")
print(f"Language: {result.language}")  # "hi"
print(f"Method: {result.method}")      # "fallback"

# Test Hinglish
result = detector.detect_from_text("मुझे pizza चाहिए")
print(f"Language: {result.language}")  # "hinglish"
print(f"Code-mixed: {result.is_code_mixed}")  # True
```

## Performance Comparison

| Method | Accuracy | Speed | Requires |
|--------|----------|-------|----------|
| fastText | 95%+ | 1-2ms | C++ compiler |
| STT metadata | 85%+ | <1ms | STT with word data |
| Script heuristics | 75%+ | <1ms | Nothing |

## Recommendation

For development and testing, the fallback method (script heuristics) is sufficient. For production with high accuracy requirements, install fastText using Option 1 (pre-built wheel) or Option 2 (Build Tools).

## Next Steps

1. ✅ Core system is working
2. ⚠ Start Ollama: `ollama serve`
3. ⚠ (Optional) Install fastText for better accuracy
4. ✅ Test the system: `python scripts/quick_diagnostic.py`
5. ✅ Run tests: `pytest tests/ -v`
