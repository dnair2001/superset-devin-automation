"""
Test script to debug Devin API authentication
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEVIN_API_KEY")
org_id = os.getenv("DEVIN_ORG_ID")
api_url = os.getenv("DEVIN_API_URL", "https://api.devin.ai")

print(f"API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
print(f"Org ID: {org_id}")
print(f"API URL: {api_url}")

# Test v3 API
print("\n=== Test v3 API ===")
session_url = f"{api_url}/v3/organizations/{org_id}/sessions"
payload = {
    "prompt": "Test session",
    "repository": "https://github.com/dnair2001/superset-take-home.git"
}

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(session_url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API Working!")
        print(f"Session ID: {data.get('session_id')}")
        print(f"Status: {data.get('status')}")
    else:
        print(f"✗ API Error: {response.text}")
except Exception as e:
    print(f"✗ Error: {str(e)}")
