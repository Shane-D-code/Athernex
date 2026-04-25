"""Test Ollama LLM"""
import requests

url = "http://localhost:11434/api/chat"
payload = {
    "model": "llama3:latest",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": False
}

print("Testing Ollama...")
response = requests.post(url, json=payload, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
