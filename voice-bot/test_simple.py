"""Simple inline test"""
import sys
sys.path.insert(0, '.')

from language_detector import detect_language
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# Test language detection
text = "Hello, how are you?"
lang = detect_language(text)
print(f"Detected language: {lang}")

# Test LLM
LOCAL_LLM_URL = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434/api/chat')
LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'llama3:latest')

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": text}
]

payload = {
    "model": LOCAL_LLM_MODEL,
    "messages": messages,
    "stream": False
}

print(f"\nCalling LLM at {LOCAL_LLM_URL}...")
print(f"Model: {LOCAL_LLM_MODEL}")
print(f"Payload: {payload}")

try:
    response = requests.post(LOCAL_LLM_URL, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Result: {result}")
    llm_response = result.get('message', {}).get('content', '')
    print(f"LLM Response: {llm_response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
