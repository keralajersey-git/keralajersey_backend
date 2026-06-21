import requests
import json

try:
    with open('test.png', 'rb') as f:
        files = {'file': ('test.png', f, 'image/png')}
        response = requests.post(
            'http://127.0.0.1:8000/products/upload-image',
            files=files,
            timeout=10
        )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! URL: {data.get('url')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
