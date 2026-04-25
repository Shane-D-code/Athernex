"""
Test the Android API endpoint
"""

import requests
import json

SERVER_URL = "http://192.168.137.205:5000"

def test_health():
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_android_api(text: str, language: str):
    """Test Android API endpoint"""
    print(f"\n2. Testing Android API ({language})...")
    print(f"   Input: {text}")
    
    try:
        payload = {
            "audio": text,
            "session_id": "test-session-123"
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/process",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("✅ API call successful")
                print(f"   Detected Language: {result.get('detected_language')}")
                print(f"   Transcription: {result.get('transcription')}")
                print(f"   Response: {result.get('response_text')}")
                print(f"   Audio Available: {'Yes' if result.get('audio_response_b64') else 'No'}")
                
                if result.get('audio_response_b64'):
                    audio_size = len(result.get('audio_response_b64'))
                    print(f"   Audio Size: {audio_size} bytes (base64)")
                
                return True
            else:
                print(f"❌ API returned error: {result.get('error')}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API error: {e}")
        return False


if __name__ == '__main__':
    print("=" * 70)
    print("Android API Integration Test")
    print("=" * 70)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Server is not running or not accessible")
        print(f"   Make sure the server is running at {SERVER_URL}")
        exit(1)
    
    # Test 2: English text
    test_android_api("Hello, how are you today?", "English")
    
    # Test 3: Hindi text
    test_android_api("नमस्ते, आप कैसे हैं?", "Hindi")
    
    # Test 4: Mixed text
    test_android_api("Hello, मैं ठीक हूं", "Mixed")
    
    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)
    print("\n📱 Android app should now be able to:")
    print("   1. Send text to /api/v1/process")
    print("   2. Receive AI response with audio")
    print("   3. Play the audio response")
    print("   4. Continue conversation loop")
