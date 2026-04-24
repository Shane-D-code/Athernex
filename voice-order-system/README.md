# Multilingual Voice Order System

A self-hosted multilingual voice order system supporting Hindi, Kannada, Marathi, and English with GPU acceleration.

## ✅ Completed Components (Tasks 1-9)

### Core ML Services
- **STT**: Whisper Medium (primary) + Vosk (fallback)
- **LLM**: Ollama + Phi3/LLaMA 3.1 8B (primary) + HuggingFace (fallback)
- **TTS**: Edge TTS (primary) + Piper (fallback)

### Audio Processing
- Silero VAD for speech detection
- Noise suppression (15dB reduction)
- Audio buffer management
- High-pass filtering

### Business Logic
- Confidence scoring (STT + LLM weighted combination)
- Language detection for code-mixed speech
- Structured data extraction
- Time expression parsing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install tzdata  # For Windows timezone support
```

### 2. Start Services

**Ollama (LLM)**:
```bash
python scripts/start_ollama.py --model phi3:latest
```

**Whisper (STT)** - Optional:
```bash
python scripts/start_whisper.py --model medium
```

**Vosk (STT Fallback)** - Optional:
```bash
python scripts/start_vosk.py --language hi
```

### 3. Run Tests

**Integration Test**:
```bash
python scripts/test_integration.py
```

**Checkpoint Validation**:
```bash
python scripts/checkpoint1_validation.py
```

## 📊 System Status

### ✅ Working Components
- LLM intent extraction (English + Hindi tested)
- TTS synthesis (multilingual)
- Confidence analysis
- Language detection
- Time parsing

### 🔄 Pending Implementation
- Tasks 10-24: Dialogue state, order management, caching, full pipeline, API endpoints

## 🎯 Hardware Requirements

- **GPU**: RTX 4060 8GB VRAM (or equivalent)
- **CPU**: i7-14700HX or better
- **RAM**: 16GB
- **Storage**: ~10GB for models

## 🔧 Configuration

Edit `voice-order-system/config/config.py` or create `.env`:

```env
# Service Endpoints
WHISPER_ENDPOINT=http://localhost:8000
OLLAMA_ENDPOINT=http://localhost:11434
PIPER_ENDPOINT=http://localhost:8002

# Models
WHISPER_MODEL=medium
OLLAMA_MODEL=phi3:latest

# Confidence Thresholds
THRESHOLD_PLACE_ORDER=0.85
THRESHOLD_MODIFY_ORDER=0.80
THRESHOLD_CANCEL_ORDER=0.90
```

## 📝 Usage Examples

### Test LLM Processing
```python
from llm import OllamaLLMProcessor

llm = OllamaLLMProcessor(model="phi3:latest")
response = await llm.process_utterance("I want 2 pizzas at 7pm")
print(response.structured_data.intent)  # place_order
print(response.structured_data.items)   # [OrderItem(name='pizza', quantity=2)]
```

### Test TTS Synthesis
```python
from tts import EdgeTTSEngine

tts = EdgeTTSEngine()
result = await tts.synthesize("आपका ऑर्डर कन्फर्म हो गया है", language="hi")
# Saves audio to result.audio_bytes
```

## 🧪 Test Results

**Checkpoint 1**: ✅ PASSED
- LLM: ✅ Processing in 11-15s
- TTS: ✅ Synthesizing multilingual audio
- Confidence: ✅ Scoring and clarification logic
- Language: ✅ Detection and dominant selection
- Time Parser: ✅ Converting relative expressions

## 📚 Project Structure

```
voice-order-system/
├── src/
│   ├── stt/          # Speech-to-Text engines
│   ├── llm/          # Language model processors
│   ├── tts/          # Text-to-Speech engines
│   ├── audio/        # Audio processing (VAD, buffers)
│   ├── confidence/   # Confidence scoring
│   ├── language/     # Language detection
│   └── utils/        # Time parsing, helpers
├── scripts/          # Startup and test scripts
├── config/           # Configuration management
└── tests/            # Test suites
```

## 🔐 Security Notes

- All services run locally (no external API keys required)
- Edge TTS requires internet but no authentication
- Models are downloaded once and cached locally

## 📖 Next Steps

To complete the full system:
1. Implement dialogue state tracking (Task 10)
2. Add order management (Task 11)
3. Build service orchestration with fallbacks (Task 12)
4. Add caching layer (Task 13)
5. Create end-to-end pipeline (Task 16)
6. Build REST API and WebSocket endpoints (Task 22)

## 🐛 Troubleshooting

**Ollama out of memory**:
- Close Chrome and other memory-heavy apps
- Use smaller model: `phi3:latest` instead of `llama3.1:8b`

**CUDA not found**:
- Verify PyTorch installation: `python -c "import torch; print(torch.cuda.is_available())"`
- Reinstall: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

**Timezone errors**:
- Install tzdata: `pip install tzdata`

## 📄 License

MIT License - See LICENSE file for details
