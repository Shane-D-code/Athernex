# Telephony Integration Guide - Voice Assistant for Phone Calls

## Overview

You want to use this voice order system for **telephone calls** (calling customers or receiving calls). This guide explains what works, what doesn't, and how to integrate with telephony services.

---

## 🎯 Quick Answer

**Current System:**
- ✅ **LLM Processing**: Works perfectly for phone calls
- ✅ **Language Detection**: Works perfectly for phone calls
- ✅ **Dialogue Management**: Works perfectly for phone calls
- ✅ **Order Management**: Works perfectly for phone calls
- ⚠ **STT (Speech-to-Text)**: Needs telephony-specific setup
- ⚠ **TTS (Text-to-Speech)**: Needs telephony-specific setup
- ❌ **Audio Format**: Needs conversion for phone networks

**What You Need:**
1. Telephony provider (Twilio, Vonage, Plivo, etc.)
2. Audio format conversion (PCM 8kHz μ-law for phones)
3. Streaming audio handling
4. WebRTC or SIP integration

---

## 📞 How Phone Calls Work (Technical)

### Phone Audio Specifications

| Aspect | Phone Network | Your Current System | Needs Conversion? |
|--------|--------------|---------------------|-------------------|
| Sample Rate | 8 kHz | 16 kHz | ✅ YES |
| Encoding | μ-law (G.711) | PCM 16-bit | ✅ YES |
| Channels | Mono | Mono | ✅ OK |
| Bitrate | 64 kbps | 256 kbps | ✅ YES |
| Latency | <200ms critical | Variable | ⚠ Optimize |

**Key Issue**: Phone networks use **8 kHz μ-law** audio, but your STT/TTS use **16 kHz PCM**. You need conversion.

---

## 🔧 What Works Out-of-the-Box

### ✅ Core Logic (100% Compatible)

Your current system's core logic works perfectly for phone calls:

1. **Language Detection** ✅
   - Detects Hindi, English, Kannada, Marathi, Hinglish
   - Works with any audio quality
   - No changes needed

2. **LLM Processing** ✅
   - Extracts intents from transcribed text
   - Handles multi-turn dialogues
   - No changes needed

3. **Dialogue Management** ✅
   - Tracks conversation state
   - Handles anaphora ("add one more")
   - No changes needed

4. **Order Management** ✅
   - Creates, modifies, cancels orders
   - No changes needed

5. **Caching** ✅
   - Reduces latency
   - No changes needed

---

## ⚠ What Needs Modification

### 1. STT (Speech-to-Text) - Needs Telephony Setup

**Current Setup:**
- Whisper: Expects 16 kHz PCM audio files
- Vosk: Expects 16 kHz PCM audio streams

**Phone Network:**
- Provides 8 kHz μ-law audio streams
- Real-time streaming (not files)

**Solutions:**

#### Option A: Use Telephony Provider's STT (Recommended)
```python
# Twilio has built-in STT
# Vonage has built-in STT
# Google Cloud has telephony-optimized STT
```

#### Option B: Convert Audio + Use Your STT
```python
# Convert 8 kHz μ-law → 16 kHz PCM
import audioop
import wave

def convert_phone_audio_to_stt(mulaw_audio_8khz):
    # 1. Decode μ-law to PCM
    pcm_audio = audioop.ulaw2lin(mulaw_audio_8khz, 2)
    
    # 2. Resample 8 kHz → 16 kHz
    pcm_16khz = audioop.ratecv(
        pcm_audio, 2, 1, 8000, 16000, None
    )[0]
    
    return pcm_16khz
```

#### Option C: Use Telephony-Optimized STT
- **Deepgram**: Optimized for phone calls
- **AssemblyAI**: Supports telephony audio
- **Google Cloud Speech**: Has telephony model
- **Azure Speech**: Has telephony model

### 2. TTS (Text-to-Speech) - Needs Telephony Setup

**Current Setup:**
- Edge TTS: Outputs 24 kHz MP3/WAV
- Piper TTS: Outputs 22 kHz WAV

**Phone Network:**
- Requires 8 kHz μ-law audio
- Real-time streaming

**Solutions:**

#### Option A: Use Telephony Provider's TTS (Recommended)
```python
# Twilio has built-in TTS
# Vonage has built-in TTS
# Google Cloud has telephony-optimized TTS
```

#### Option B: Convert Your TTS Output
```python
def convert_tts_to_phone_audio(pcm_audio_16khz):
    # 1. Resample 16 kHz → 8 kHz
    pcm_8khz = audioop.ratecv(
        pcm_audio_16khz, 2, 1, 16000, 8000, None
    )[0]
    
    # 2. Encode to μ-law
    mulaw_audio = audioop.lin2ulaw(pcm_8khz, 2)
    
    return mulaw_audio
```

#### Option C: Use Telephony-Optimized TTS
- **Google Cloud TTS**: Has telephony voices
- **Azure TTS**: Has telephony voices
- **Amazon Polly**: Supports telephony formats

---

## 🏗️ Architecture for Phone Calls

### Option 1: Twilio Integration (Recommended)

```
Phone Call → Twilio → Your Server → Response → Twilio → Phone
              ↓                        ↑
           Built-in STT          Your LLM Logic
              ↓                        ↑
           Text Stream           Text Response
                                      ↓
                                Built-in TTS
```

**Advantages:**
- ✅ No audio conversion needed
- ✅ Built-in STT/TTS
- ✅ Handles telephony complexity
- ✅ Scales automatically

**Your Code:**
```python
from twilio.twiml.voice_response import VoiceResponse, Gather

@app.post("/twilio/voice")
async def handle_twilio_call(request: Request):
    # Get transcribed text from Twilio
    user_text = request.form.get("SpeechResult")
    session_id = request.form.get("CallSid")
    
    # Use your existing pipeline (text-only mode)
    result = await pipeline.process_text(
        text=user_text,
        session_id=session_id
    )
    
    # Return TwiML response
    response = VoiceResponse()
    response.say(result.bot_text, language="hi-IN")
    response.gather(
        input="speech",
        action="/twilio/voice",
        language="hi-IN"
    )
    
    return str(response)
```

### Option 2: WebRTC Integration

```
Phone Call → WebRTC Gateway → Your Server → WebRTC → Phone
                ↓                              ↑
            Audio Stream                  Audio Stream
                ↓                              ↑
            Your STT                      Your TTS
                ↓                              ↑
            Your LLM Logic
```

**Advantages:**
- ✅ Full control over audio
- ✅ Use your own STT/TTS
- ✅ Lower latency possible

**Disadvantages:**
- ❌ Complex setup
- ❌ Need audio conversion
- ❌ Need WebRTC server

### Option 3: SIP Integration

```
Phone Call → SIP Server → Your Server → SIP → Phone
              ↓                          ↑
          RTP Audio                  RTP Audio
              ↓                          ↑
          Your STT                   Your TTS
              ↓                          ↑
          Your LLM Logic
```

**Advantages:**
- ✅ Direct telephony integration
- ✅ Enterprise-grade

**Disadvantages:**
- ❌ Very complex setup
- ❌ Need SIP server (Asterisk, FreeSWITCH)
- ❌ Need audio conversion

---

## 🚀 Recommended Implementation

### Step 1: Use Twilio (Easiest)

**Why Twilio:**
- ✅ Handles all telephony complexity
- ✅ Built-in STT/TTS for Indian languages
- ✅ Pay-as-you-go pricing
- ✅ 5-minute setup

**Setup:**

1. **Install Twilio SDK**
```bash
pip install twilio
```

2. **Create Twilio Endpoint**
```python
# Add to src/api/main.py

from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi import Form

@app.post("/twilio/incoming-call")
async def handle_incoming_call():
    """Handle incoming phone call."""
    response = VoiceResponse()
    
    # Greeting
    response.say(
        "नमस्ते! आपका स्वागत है। आप क्या ऑर्डर करना चाहेंगे?",
        language="hi-IN",
        voice="Polly.Aditi"
    )
    
    # Listen for speech
    gather = Gather(
        input="speech",
        action="/twilio/process-speech",
        language="hi-IN",
        speech_timeout="auto"
    )
    response.append(gather)
    
    return Response(content=str(response), media_type="text/xml")


@app.post("/twilio/process-speech")
async def process_speech(
    SpeechResult: str = Form(None),
    CallSid: str = Form(None),
    Confidence: float = Form(0.0)
):
    """Process transcribed speech from Twilio."""
    
    if not SpeechResult:
        # No speech detected
        response = VoiceResponse()
        response.say("मुझे सुनाई नहीं दिया। कृपया दोबारा बोलें।", language="hi-IN")
        response.redirect("/twilio/incoming-call")
        return Response(content=str(response), media_type="text/xml")
    
    # Use your existing pipeline (text mode)
    result = await pipeline.process_text(
        text=SpeechResult,
        session_id=CallSid,
        language="hi"  # Twilio provides language
    )
    
    # Generate response
    response = VoiceResponse()
    
    if result.success:
        # Speak the response
        response.say(result.bot_text, language="hi-IN", voice="Polly.Aditi")
        
        # Continue conversation
        if not result.clarification_needed:
            gather = Gather(
                input="speech",
                action="/twilio/process-speech",
                language="hi-IN"
            )
            response.append(gather)
        else:
            # End call if order complete
            response.say("धन्यवाद! आपका ऑर्डर कन्फर्म हो गया है।", language="hi-IN")
            response.hangup()
    else:
        response.say("क्षमा करें, कुछ गलत हो गया। कृपया दोबारा कॉल करें।", language="hi-IN")
        response.hangup()
    
    return Response(content=str(response), media_type="text/xml")


@app.post("/twilio/make-outbound-call")
async def make_outbound_call(phone_number: str, order_id: str):
    """Make outbound call to customer."""
    from twilio.rest import Client
    
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    call = client.calls.create(
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        url="https://your-server.com/twilio/outbound-greeting",
        method="POST"
    )
    
    return {"call_sid": call.sid, "status": call.status}
```

3. **Configure Twilio Webhook**
```
Incoming Call URL: https://your-server.com/twilio/incoming-call
Method: POST
```

### Step 2: Test Locally with ngrok

```bash
# Install ngrok
# Download from: https://ngrok.com/download

# Start your API
python -m uvicorn api.main:app --reload --port 8080

# In another terminal, expose to internet
ngrok http 8080

# Copy the ngrok URL (e.g., https://abc123.ngrok.io)
# Use this in Twilio webhook: https://abc123.ngrok.io/twilio/incoming-call
```

---

## 📊 Comparison: Telephony Providers

| Provider | STT Quality | TTS Quality | Indian Languages | Pricing | Ease of Use |
|----------|-------------|-------------|------------------|---------|-------------|
| **Twilio** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Hi, Kn, Mr | $0.0085/min | ⭐⭐⭐⭐⭐ |
| **Vonage** | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Hi | $0.0065/min | ⭐⭐⭐⭐ |
| **Plivo** | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Hi | $0.0070/min | ⭐⭐⭐⭐ |
| **Exotel** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ All Indian | India-focused | ⭐⭐⭐⭐ |

**Recommendation**: Use **Twilio** for international or **Exotel** for India-only.

---

## 🎯 What You Need to Add

### 1. Twilio Integration Module

```python
# src/telephony/twilio_handler.py

from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client

class TwilioHandler:
    def __init__(self, account_sid, auth_token, phone_number):
        self.client = Client(account_sid, auth_token)
        self.phone_number = phone_number
    
    def create_incoming_response(self, greeting_text, language="hi-IN"):
        """Create TwiML for incoming call."""
        response = VoiceResponse()
        response.say(greeting_text, language=language)
        
        gather = Gather(
            input="speech",
            action="/twilio/process-speech",
            language=language,
            speech_timeout="auto"
        )
        response.append(gather)
        
        return str(response)
    
    def create_speech_response(self, bot_text, continue_conversation=True, language="hi-IN"):
        """Create TwiML for speech response."""
        response = VoiceResponse()
        response.say(bot_text, language=language)
        
        if continue_conversation:
            gather = Gather(
                input="speech",
                action="/twilio/process-speech",
                language=language
            )
            response.append(gather)
        else:
            response.hangup()
        
        return str(response)
    
    def make_outbound_call(self, to_number, webhook_url):
        """Make outbound call."""
        call = self.client.calls.create(
            to=to_number,
            from_=self.phone_number,
            url=webhook_url,
            method="POST"
        )
        return call.sid
```

### 2. Audio Conversion Module (If Not Using Twilio STT/TTS)

```python
# src/telephony/audio_converter.py

import audioop

class TelephonyAudioConverter:
    """Convert between telephony and STT/TTS audio formats."""
    
    @staticmethod
    def phone_to_stt(mulaw_8khz: bytes) -> bytes:
        """Convert phone audio (8kHz μ-law) to STT format (16kHz PCM)."""
        # Decode μ-law to PCM
        pcm = audioop.ulaw2lin(mulaw_8khz, 2)
        
        # Resample 8kHz → 16kHz
        pcm_16khz, _ = audioop.ratecv(pcm, 2, 1, 8000, 16000, None)
        
        return pcm_16khz
    
    @staticmethod
    def tts_to_phone(pcm_16khz: bytes) -> bytes:
        """Convert TTS audio (16kHz PCM) to phone format (8kHz μ-law)."""
        # Resample 16kHz → 8kHz
        pcm_8khz, _ = audioop.ratecv(pcm_16khz, 2, 1, 16000, 8000, None)
        
        # Encode to μ-law
        mulaw = audioop.lin2ulaw(pcm_8khz, 2)
        
        return mulaw
```

### 3. Configuration Updates

```python
# config/config.py

# Add telephony settings
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Telephony
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    telephony_provider: str = "twilio"  # twilio, vonage, plivo
```

---

## 🧪 Testing Telephony Integration

### Test 1: Local Testing with ngrok

```bash
# Terminal 1: Start API
python -m uvicorn api.main:app --reload --port 8080

# Terminal 2: Expose with ngrok
ngrok http 8080

# Use ngrok URL in Twilio webhook
```

### Test 2: Simulate Phone Call

```python
# test_telephony.py

import requests

def test_twilio_webhook():
    """Test Twilio webhook locally."""
    response = requests.post(
        "http://localhost:8080/twilio/process-speech",
        data={
            "SpeechResult": "मुझे दो पिज़्ज़ा चाहिए",
            "CallSid": "test-call-123",
            "Confidence": 0.95
        }
    )
    
    print(response.text)  # Should return TwiML
```

### Test 3: End-to-End Call

1. Configure Twilio webhook
2. Call your Twilio number
3. Speak: "मुझे दो पिज़्ज़ा चाहिए"
4. System should respond with order confirmation

---

## 💰 Cost Estimates

### Twilio Pricing (India)

| Service | Cost |
|---------|------|
| Incoming call | $0.0085/min |
| Outgoing call | $0.0140/min |
| STT | Included |
| TTS | Included |
| Phone number | $1/month |

**Example**: 1000 calls/month, 2 min avg = $17-28/month

---

## 🚀 Quick Start for Telephony

```bash
# 1. Install Twilio
pip install twilio

# 2. Add telephony endpoints (code above)

# 3. Test locally
ngrok http 8080

# 4. Configure Twilio webhook

# 5. Make test call
```

---

## ✅ Summary

**What Works for Phone Calls:**
- ✅ All business logic (LLM, dialogue, orders)
- ✅ Language detection
- ✅ Multi-turn conversations

**What You Need to Add:**
- ⚠ Telephony provider integration (Twilio recommended)
- ⚠ Audio format handling (or use provider's STT/TTS)
- ⚠ Webhook endpoints for calls

**Recommended Approach:**
1. Use Twilio (handles STT/TTS/telephony)
2. Your system processes text (existing pipeline)
3. Twilio converts back to speech
4. 5-minute setup, works immediately

**Your current system is 90% ready for phone calls. You just need to add Twilio integration!**
