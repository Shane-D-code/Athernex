"""
Quick test script for 11Labs TTS integration
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Test voice IDs
ELEVENLABS_VOICES = {
    'hi': 'pNInz6obpgDQGcFmaJgB',  # Adam - multilingual
    'en': 'EXAVITQu4vr4xnSDxMaL'   # Sarah - English
}

def test_elevenlabs_tts(text: str, language: str = 'en'):
    """Test 11Labs TTS API"""
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not set")
        return False
    
    voice_id = ELEVENLABS_VOICES.get(language, ELEVENLABS_VOICES['en'])
    
    headers = {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.5,
            'use_speaker_boost': True
        }
    }
    
    print(f"🔊 Testing 11Labs TTS ({language}): {text[:50]}...")
    
    try:
        response = requests.post(
            f"{ELEVENLABS_TTS_URL}/{voice_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        audio_data = response.content
        
        if audio_data:
            print(f"✅ Success! Audio size: {len(audio_data)} bytes")
            
            # Save test audio
            filename = f"test_elevenlabs_{language}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Saved to: {filename}")
            return True
        else:
            print("❌ No audio data returned")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("11Labs TTS Integration Test")
    print("=" * 60)
    
    # Test English
    print("\n1. Testing English:")
    test_elevenlabs_tts("Hello! How can I help you today?", 'en')
    
    # Test Hindi
    print("\n2. Testing Hindi:")
    test_elevenlabs_tts("नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?", 'hi')
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
