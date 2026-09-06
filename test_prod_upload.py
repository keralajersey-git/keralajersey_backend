import requests
import json

# Test production upload endpoint
url = "https://keralajersey-backend.vercel.app/products/upload-image"

# Create a test file
test_file = {"file": ("test.png", b"fake image data", "image/png")}

try:
    response = requests.post(url, files=test_file, timeout=15)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
