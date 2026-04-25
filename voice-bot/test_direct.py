"""Direct test of Android API"""
import requests

url = "http://192.168.137.205:5000/api/v1/process"
payload = {
    "audio": "Hello, how are you?",
    "session_id": "test-123"
}

print("Testing Android API...")
try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
