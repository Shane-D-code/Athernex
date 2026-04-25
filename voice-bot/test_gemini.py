"""Test Google Gemini API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def test_gemini(text: str, language: str = 'en'):
    """Test Gemini API"""
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not set")
        return False
    
    if language == 'hi':
        system_instruction = "You are a helpful AI assistant. The user is speaking in Hindi. Respond in Hindi (Devanagari script). Keep responses concise."
    else:
        system_instruction = "You are a helpful AI assistant. Respond in clear, simple English. Keep responses concise."
    
    payload = {
        "contents": [{
            "parts": [
                {"text": f"System: {system_instruction}"},
                {"text": f"User: {text}"},
                {"text": "Assistant:"}
            ]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 150
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    print(f"🤖 Testing Gemini API ({language}): {text[:50]}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    gemini_response = parts[0]['text'].strip()
                    print(f"✅ Success!")
                    print(f"Response: {gemini_response}")
                    return True
        
        print("❌ No valid response from Gemini")
        print(f"Result: {result}")
        return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("Google Gemini API Integration Test")
    print("=" * 70)
    
    # Test 1: English
    print("\n1. Testing English:")
    test_gemini("Hello, how are you today?", 'en')
    
    # Test 2: Hindi
    print("\n2. Testing Hindi:")
    test_gemini("नमस्ते, आप कैसे हैं?", 'hi')
    
    # Test 3: Conversation
    print("\n3. Testing Conversation:")
    test_gemini("What is the weather like?", 'en')
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)
